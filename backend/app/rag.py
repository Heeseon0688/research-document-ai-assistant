from app.llm import LLM, make_payload
from app.schemas import ChatResponse, NO_EVIDENCE, Source


def normalize(text: str) -> str:
    return " ".join(text.split())


class RAGService:
    def __init__(self, store, embedder, provider: LLM, settings):
        self.store = store
        self.embedder = embedder
        self.provider = provider
        self.settings = settings

    def answer(self, question: str, top_k: int | None = None) -> ChatResponse:
        fallback = ChatResponse(answer=NO_EVIDENCE, sources=[], grounded=False, retrieved_count=0)
        # Avoid downloading the embedding model or calling an LLM for an empty library.
        if not self.store.documents():
            return fallback
        hits = self.store.search(self.embedder.query(question),
                                 top_k or self.settings.top_k, self.settings.min_similarity)
        fallback.retrieved_count = len(hits)
        if not hits:
            return fallback
        result = self.provider.generate(make_payload(question, hits))
        if not result.grounded or not result.answer.strip() or not result.citations:
            return fallback
        by_id = {hit.chunk_id: hit for hit in hits}
        sources = []
        seen = set()
        for citation in result.citations:
            hit = by_id.get(citation.chunk_id)
            quote = normalize(citation.quote)
            # Fail closed: even one fabricated citation rejects the whole answer.
            if hit is None or len(quote) < 8 or quote not in normalize(hit.text):
                return fallback
            key = (citation.chunk_id, quote)
            if key in seen:
                continue
            seen.add(key)
            sources.append(Source(chunk_id=hit.chunk_id,
                                  document_id=hit.metadata["document_id"],
                                  file_name=hit.metadata["file_name"], page=hit.metadata["page"],
                                  chunk_index=hit.metadata["chunk_index"], quote=quote,
                                  excerpt=hit.text, similarity=round(hit.similarity, 4)))
        return ChatResponse(answer=result.answer.strip(), sources=sources, grounded=True,
                            retrieved_count=len(hits))
