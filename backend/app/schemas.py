from pydantic import BaseModel, ConfigDict, Field

NO_EVIDENCE = "제공된 문서에서 근거를 찾을 수 없습니다"


class DocumentInfo(BaseModel):
    document_id: str
    file_name: str
    page_count: int
    chunk_count: int
    uploaded_at: str


class UploadItem(BaseModel):
    file_name: str
    status: str
    document: DocumentInfo | None = None
    error: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: str
    quote: str


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grounded: bool
    answer: str
    citations: list[Citation]


class Source(BaseModel):
    chunk_id: str
    document_id: str
    file_name: str
    page: int
    chunk_index: int
    quote: str
    excerpt: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
    retrieved_count: int
