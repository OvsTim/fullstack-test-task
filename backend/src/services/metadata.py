from pathlib import Path


def extract_metadata(
    *,
    original_name: str,
    mime_type: str,
    size: int,
    content: bytes,
) -> dict:
    metadata = {
        "extension": Path(original_name).suffix.lower(),
        "size_bytes": size,
        "mime_type": mime_type,
    }

    if mime_type.startswith("text/"):
        text = content.decode("utf-8", errors="ignore")
        metadata["line_count"] = len(text.splitlines())
        metadata["char_count"] = len(text)
    elif mime_type == "application/pdf":
        metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

    return metadata
