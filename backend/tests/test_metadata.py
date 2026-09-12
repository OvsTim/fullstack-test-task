from io import BytesIO

from src.services.metadata import extract_metadata

_PDF_MARKER = b"/Type /Page"


def _extract(*, name: str, mime: str, content: bytes, chunk_size: int) -> dict:
    return extract_metadata(
        original_name=name,
        mime_type=mime,
        size=len(content),
        stream=BytesIO(content),
        chunk_size=chunk_size,
    )


def test_text_hello_is_one_line():
    result = _extract(name="notes.txt", mime="text/plain", content=b"hello", chunk_size=2)

    assert result["line_count"] == 1
    assert result["char_count"] == 5


def test_text_two_lines_without_trailing_newline():
    result = _extract(name="notes.txt", mime="text/plain", content=b"a\nb", chunk_size=1)

    assert result["line_count"] == 2
    assert result["char_count"] == 3


def test_text_trailing_newline_does_not_add_line():
    result = _extract(name="notes.txt", mime="text/plain", content=b"hello\n", chunk_size=3)

    assert result["line_count"] == 1
    assert result["char_count"] == 6


def test_pdf_page_marker_split_across_chunks():
    prefix = b"%PDF-1.4 "
    content = prefix + _PDF_MARKER
    chunk_size = len(prefix) + 5

    result = _extract(
        name="doc.pdf",
        mime="application/pdf",
        content=content,
        chunk_size=chunk_size,
    )

    assert result["approx_page_count"] == 1


def test_pdf_counts_two_markers_across_tiny_chunks():
    content = b"xx" + _PDF_MARKER + b"yy" + _PDF_MARKER + b"zz"

    result = _extract(
        name="doc.pdf",
        mime="application/pdf",
        content=content,
        chunk_size=3,
    )

    assert result["approx_page_count"] == 2
