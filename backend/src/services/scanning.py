from dataclasses import dataclass
from pathlib import Path

from src.core.enums import ScanStatus

_DANGEROUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js"}
_ALLOWED_PDF_MIME_TYPES = {"application/pdf", "application/octet-stream"}
_MAX_CLEAN_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ScanResult:
    status: str
    details: str
    requires_attention: bool


def scan(original_name: str, mime_type: str, size: int) -> ScanResult:
    reasons: list[str] = []
    extension = Path(original_name).suffix.lower()

    if extension in _DANGEROUS_EXTENSIONS:
        reasons.append(f"suspicious extension {extension}")

    if size > _MAX_CLEAN_SIZE:
        reasons.append("file is larger than 10 MB")

    if extension == ".pdf" and mime_type not in _ALLOWED_PDF_MIME_TYPES:
        reasons.append("pdf extension does not match mime type")

    if reasons:
        return ScanResult(
            status=ScanStatus.SUSPICIOUS.value,
            details=", ".join(reasons),
            requires_attention=True,
        )

    return ScanResult(
        status=ScanStatus.CLEAN.value,
        details="no threats found",
        requires_attention=False,
    )
