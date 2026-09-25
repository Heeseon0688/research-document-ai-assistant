from app.chunking import chunk_pages
from app.pdf import extract_pages

class FakeTokenizer:
    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        words = text.split()
        offsets = []
        cursor = 0
        for word in words:
            start = text.index(word, cursor); offsets.append((start, start + len(word))); cursor = start + len(word)
        return {"offset_mapping": offsets}

def test_pdf_text_extraction_and_page_numbers():
    import fitz
    doc = fitz.open(); doc.new_page().insert_text((72, 72), "page one"); doc.new_page().insert_text((72, 72), "page two")
    data = doc.tobytes(); doc.close()
    pages = extract_pages(data)
    assert [(p.page, p.text) for p in pages] == [(1, "page one"), (2, "page two")]

def test_chunking_has_overlap_and_page_metadata():
    from app.pdf import PageText
    pages = [PageText(2, "one two three four five six seven")]
    chunks = chunk_pages(pages, "x.pdf", FakeTokenizer(), chunk_size=4, overlap=1)
    assert len(chunks) == 2
    assert chunks[0].page == chunks[1].page == 2
    assert "four" in chunks[0].text and "four" in chunks[1].text
