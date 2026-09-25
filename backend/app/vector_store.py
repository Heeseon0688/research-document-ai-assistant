from dataclasses import dataclass
from threading import RLock

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.chunking import Chunk
from app.config import Settings
from app.schemas import DocumentInfo


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    text: str
    metadata: dict
    similarity: float


class VectorStore:
    def __init__(self, settings: Settings):
        self.lock = RLock()
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        signature = {"embedding_model": settings.embedding_model,
                     "chunk_size": settings.chunk_size,
                     "chunk_overlap": settings.chunk_overlap, "schema_version": 1}
        self.collection = self.client.get_or_create_collection(
            "research_chunks", embedding_function=None,
            metadata={"hnsw:space": "cosine", **signature},
        )
        if any(self.collection.metadata.get(k) != v for k, v in signature.items()):
            raise ValueError("기존 인덱스 설정과 다릅니다. 새 CHROMA_PATH에 문서를 다시 업로드하세요.")
        # Incomplete uploads from a killed process are never exposed as documents.
        self.collection.delete(where={"committed": False})

    @staticmethod
    def _document(metadata: dict) -> DocumentInfo:
        return DocumentInfo(**{key: metadata[key] for key in DocumentInfo.model_fields})

    def documents(self) -> list[DocumentInfo]:
        with self.lock:
            rows = self.collection.get(where={"$and": [
                {"chunk_index": 0}, {"committed": True}]}, include=["metadatas"])
            return sorted([self._document(row) for row in rows["metadatas"]],
                          key=lambda row: row.uploaded_at, reverse=True)

    def find_document(self, document_id: str) -> DocumentInfo | None:
        with self.lock:
            rows = self.collection.get(ids=[f"{document_id}:0"], include=["metadatas"])
            if rows["metadatas"] and rows["metadatas"][0]["committed"]:
                return self._document(rows["metadatas"][0])
            return None

    def add(self, document: DocumentInfo, chunks: list[Chunk], vectors: list[list[float]]):
        if not chunks or len(chunks) != len(vectors):
            raise ValueError("Chunks and embeddings must have the same nonzero length")
        ids = [f"{document.document_id}:{c.chunk_index}" for c in chunks]
        metadata = [{**document.model_dump(), "page": c.page,
                     "chunk_index": c.chunk_index, "committed": False} for c in chunks]
        with self.lock:
            try:
                for start in range(0, len(chunks), 128):
                    self.collection.add(ids=ids[start:start + 128],
                                        documents=[c.text for c in chunks[start:start + 128]],
                                        embeddings=vectors[start:start + 128],
                                        metadatas=metadata[start:start + 128])
                # All chunks become visible in one update after ingestion succeeds.
                self.collection.update(ids=ids, metadatas=[
                    {**m, "committed": True} for m in metadata])
            except Exception:
                self.collection.delete(where={"document_id": document.document_id})
                raise

    def search(self, vector: list[float], top_k: int = 5,
               min_similarity: float = 0.70) -> list[Hit]:
        with self.lock:
            if self.collection.count() == 0:
                return []
            rows = self.collection.query(query_embeddings=[vector],
                                         n_results=min(top_k, self.collection.count()),
                                         where={"committed": True},
                                         include=["documents", "metadatas", "distances"])
        hits = []
        for chunk_id, text, metadata, distance in zip(
            rows["ids"][0], rows["documents"][0], rows["metadatas"][0], rows["distances"][0]
        ):
            similarity = max(-1.0, min(1.0, 1 - distance))
            if similarity >= min_similarity:
                hits.append(Hit(chunk_id, text, metadata, similarity))
        return hits
