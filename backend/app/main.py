import hashlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import PurePosixPath

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.chunking import chunk_pages
from app.config import Settings
from app.embeddings import Embedder
from app.llm import ProviderError, create_provider
from app.pdf import extract_pages
from app.rag import RAGService
from app.schemas import ChatRequest, ChatResponse, DocumentInfo, UploadItem
from app.vector_store import VectorStore

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, embedder=None, provider=None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = VectorStore(settings)
        app.state.store = store
        app.state.embedder = embedder or Embedder(settings.embedding_model, settings.embedding_device)
        app.state.rag = RAGService(store, app.state.embedder,
                                   provider or create_provider(settings), settings)
        yield

    app = FastAPI(title="내 연구문서 탐색을 돕는 AI Assistant", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": settings.llm_provider,
                "model": settings.openai_model if settings.llm_provider == "openai"
                else settings.ollama_model, "embedding_model": settings.embedding_model,
                "llm_connectivity": "not_checked"}

    @app.get("/documents", response_model=list[DocumentInfo])
    def documents():
        return app.state.store.documents()

    @app.post("/documents/upload", response_model=list[UploadItem])
    def upload(files: list[UploadFile] = File(...)):
        # sync routes run in FastAPI's thread pool: parsing/embedding don't block asyncio.
        results = []
        try:
            if len(files) > settings.max_files:
                raise HTTPException(400, f"한 번에 최대 {settings.max_files}개 업로드할 수 있습니다.")
            for file in files:
                name = PurePosixPath((file.filename or "document.pdf").replace("\\", "/")).name
                name = "".join(c for c in name if c.isprintable())[:200] or "document.pdf"
                try:
                    if not name.lower().endswith(".pdf"):
                        raise ValueError("PDF 파일만 업로드할 수 있습니다.")
                    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
                    if len(data) > settings.max_upload_mb * 1024 * 1024:
                        raise ValueError(f"파일당 최대 {settings.max_upload_mb}MB입니다.")
                    document_id = hashlib.sha256(data).hexdigest()
                    # One process owns embedded Chroma. Serialize ingestion + duplicate checks.
                    with app.state.store.lock:
                        existing = app.state.store.find_document(document_id)
                        if existing:
                            results.append(UploadItem(file_name=name, status="duplicate", document=existing))
                            continue
                        pages = extract_pages(data, settings.max_pages)
                        chunks = chunk_pages(pages, name, app.state.embedder.tokenizer,
                                              settings.chunk_size, settings.chunk_overlap)
                        if not chunks:
                            raise ValueError("검색 가능한 텍스트가 없습니다.")
                        if len(chunks) > 4000:
                            raise ValueError("chunk가 너무 많습니다. PDF를 더 작은 파일로 나눠주세요.")
                        vectors = app.state.embedder.passages([c.text for c in chunks])
                        document = DocumentInfo(document_id=document_id, file_name=name,
                                                page_count=len(pages), chunk_count=len(chunks),
                                                uploaded_at=datetime.now(timezone.utc).isoformat())
                        app.state.store.add(document, chunks, vectors)
                    results.append(UploadItem(file_name=name, status="uploaded", document=document))
                except ValueError as exc:
                    results.append(UploadItem(file_name=name, status="error", error=str(exc)))
                except Exception:
                    logger.exception("Document ingestion failed")
                    results.append(UploadItem(file_name=name, status="error",
                                              error="문서 처리에 실패했습니다. 모델 다운로드와 서버 로그를 확인해주세요."))
        finally:
            for file in files:
                file.file.close()
        return results

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        question = request.question.strip()
        if not question:
            raise HTTPException(422, "질문을 입력해주세요.")
        try:
            return app.state.rag.answer(question, request.top_k)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except ProviderError as exc:
            raise HTTPException(502, str(exc)) from exc
        except Exception as exc:
            logger.exception("Chat failed")
            raise HTTPException(503, "검색 처리에 실패했습니다. 서버 로그와 임베딩 모델을 확인해주세요.") from exc

    return app


app = create_app()
