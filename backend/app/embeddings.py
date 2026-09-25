from threading import RLock


class Embedder:
    """One shared model, loaded lazily so /health never downloads model weights."""

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._lock = RLock()

    @property
    def model(self):
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
            return self._model

    @property
    def tokenizer(self):
        return self.model.tokenizer

    def _encode(self, texts: list[str], prefix: str) -> list[list[float]]:
        # E5 requires these English prefixes even when the text is Korean.
        prepared = [prefix + text for text in texts]
        with self._lock:
            model = self.model
            lengths = [len(ids) for ids in model.tokenizer(
                prepared, truncation=False)["input_ids"]]
            if any(length > model.max_seq_length for length in lengths):
                raise ValueError("임베딩 토큰 한도를 초과했습니다. 질문 또는 CHUNK_SIZE를 줄여주세요.")
            return model.encode(prepared, normalize_embeddings=True,
                                batch_size=32, show_progress_bar=False).tolist()

    def passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts, "passage: ")

    def query(self, text: str) -> list[float]:
        return self._encode([text], "query: ")[0]
