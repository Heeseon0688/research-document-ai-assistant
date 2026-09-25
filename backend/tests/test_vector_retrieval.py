import pytest

pytestmark = pytest.mark.integration

def test_vector_retrieval_semantic_search(tmp_path):
    from app.config import Settings
    from app.embeddings import Embedder
    from app.vector_store import VectorStore
    from app.chunking import Chunk
    from app.schemas import DocumentInfo
    settings = Settings(chroma_path=tmp_path, embedding_model="intfloat/multilingual-e5-small")
    store = VectorStore(settings); embedder = Embedder(settings.embedding_model)
    doc = DocumentInfo(document_id="demo", file_name="demo.pdf", page_count=1, chunk_count=2, uploaded_at="now")
    chunks = [Chunk("fermentation titer increased to 48 g/L", "demo.pdf", 1, 0), Chunk("quality lot was held", "demo.pdf", 1, 1)]
    store.add(doc, chunks, embedder.passages([c.text for c in chunks]))
    hits = store.search(embedder.query("highest fermentation production"), top_k=1, min_similarity=-1)
    assert hits and hits[0].metadata["chunk_index"] == 0
