import codecs
from pathlib import Path
from typing import BinaryIO

_CHUNK_SIZE = 64 * 1024
_PDF_PAGE_MARKER = b"/Type /Page"
_LINE_BREAK_SUFFIXES = (
    "\r\n",
    "\n",
    "\r",
    "\v",
    "\f",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x85",
    "\u2028",
    "\u2029",
)


def extract_metadata(
    *,
    original_name: str,
    mime_type: str,
    size: int,
    stream: BinaryIO,
    chunk_size: int = _CHUNK_SIZE,
) -> dict:
    metadata = {
        "extension": Path(original_name).suffix.lower(),
        "size_bytes": size,
        "mime_type": mime_type,
    }

    if mime_type.startswith("text/"):
        line_count, char_count = _count_text(stream, chunk_size)
        metadata["line_count"] = line_count
        metadata["char_count"] = char_count
    elif mime_type == "application/pdf":
        metadata["approx_page_count"] = max(_count_pdf_pages(stream, chunk_size), 1)

    return metadata


def _count_text(stream: BinaryIO, chunk_size: int) -> tuple[int, int]:
    decoder = codecs.getincrementaldecoder("utf-8")("ignore")
    char_count = 0
    line_count = 0
    pending = ""

    def consume(text: str, *, final: bool) -> None:
        nonlocal char_count, line_count, pending
        char_count += len(text)
        combined = pending + text
        if not combined:
            return
        parts = combined.splitlines(keepends=True)
        if not final and parts and not parts[-1].endswith(_LINE_BREAK_SUFFIXES):
            pending = parts.pop()
        else:
            pending = ""
        line_count += len(parts)

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        consume(decoder.decode(chunk), final=False)
    consume(decoder.decode(b"", final=True), final=True)
    return line_count, char_count


def _count_pdf_pages(stream: BinaryIO, chunk_size: int) -> int:
    overlap = len(_PDF_PAGE_MARKER) - 1
    prev = b""
    count = 0
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        data = prev + chunk
        count += data.count(_PDF_PAGE_MARKER)
        prev = data[-overlap:] if len(data) >= overlap else data
    return count
