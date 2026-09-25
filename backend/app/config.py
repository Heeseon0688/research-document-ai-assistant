from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    llm_provider: Literal["openai", "ollama"] = "ollama"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    llm_timeout_seconds: float = Field(120, gt=0)
    demo_fallback: bool = True
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_device: str = "cpu"
    chroma_path: Path = Path("data/chroma")
    chunk_size: int = Field(220, ge=16, le=450)
    chunk_overlap: int = Field(40, ge=0)
    top_k: int = Field(5, ge=1, le=20)
    min_similarity: float = Field(0.70, ge=-1, le=1)
    max_upload_mb: int = Field(20, ge=1, le=100)
    max_files: int = Field(10, ge=1, le=50)
    max_pages: int = Field(200, ge=1)
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    @model_validator(mode="after")
    def validate_settings(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if not self.chroma_path.is_absolute():
            self.chroma_path = ROOT / self.chroma_path
        return self
