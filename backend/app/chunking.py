from dataclasses import dataclass
from typing import Any

from app.pdf import PageText


@dataclass(frozen=True)
class Chunk:
    text: str
    file_name: str
    page: int
    chunk_index: int


def chunk_pages(pages: list[PageText], file_name: str, tokenizer: Any,
                chunk_size: int = 220, overlap: int = 40) -> list[Chunk]:
    """Sliding token windows; offsets slice the original text without decode artifacts.

    A window never crosses a page boundary, so every chunk has one exact page.
    Overlap preserves context for facts that straddle a window boundary.
    """
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")
    chunks = []
    for page in pages:
        offsets = tokenizer(page.text, add_special_tokens=False,
                            return_offsets_mapping=True)["offset_mapping"]
        for start in range(0, len(offsets), chunk_size - overlap):
            end = min(start + chunk_size, len(offsets))
            text = page.text[offsets[start][0]:offsets[end - 1][1]].strip()
            if text:
                chunks.append(Chunk(text, file_name, page.page, len(chunks)))
            if end == len(offsets):
                break
    return chunks
