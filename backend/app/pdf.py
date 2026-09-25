from dataclasses import dataclass

import pymupdf


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


def extract_pages(content: bytes, max_pages: int = 200) -> list[PageText]:
    """Physical PDF pages are 1-based, including empty pages; no OCR is performed."""
    if not content.startswith(b"%PDF-"):
        raise ValueError("유효한 PDF 파일이 아닙니다.")
    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("암호화된 PDF는 지원하지 않습니다.")
            if len(document) > max_pages:
                raise ValueError(f"PDF는 {max_pages}페이지 이하여야 합니다.")
            pages = [PageText(i + 1, page.get_text("text", sort=True).strip())
                     for i, page in enumerate(document)]
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("손상되었거나 읽을 수 없는 PDF입니다.") from exc
    if not any(page.text for page in pages):
        raise ValueError("추출할 텍스트가 없습니다. 스캔 PDF는 OCR이 필요합니다.")
    return pages
