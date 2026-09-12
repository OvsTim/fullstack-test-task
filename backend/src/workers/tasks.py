import asyncio
from pathlib import Path

from src.core.config import settings
from src.core.enums import AlertLevel, ProcessingStatus, ScanStatus
from src.db.models import Alert, StoredFile
from src.db.session import async_session_maker
from src.workers.celery_app import celery_app

_worker_loop: asyncio.AbstractEventLoop | None = None


def run_in_worker_loop(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


async def _scan_file_for_threats(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        file_item.processing_status = ProcessingStatus.PROCESSING.value
        reasons: list[str] = []
        extension = Path(file_item.original_name).suffix.lower()

        if extension in {".exe", ".bat", ".cmd", ".sh", ".js"}:
            reasons.append(f"suspicious extension {extension}")

        if file_item.size > 10 * 1024 * 1024:
            reasons.append("file is larger than 10 MB")

        if extension == ".pdf" and file_item.mime_type not in {"application/pdf", "application/octet-stream"}:
            reasons.append("pdf extension does not match mime type")

        file_item.scan_status = ScanStatus.SUSPICIOUS.value if reasons else ScanStatus.CLEAN.value
        file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
        file_item.requires_attention = bool(reasons)
        await session.commit()

    extract_file_metadata.delay(file_id)


async def _extract_file_metadata(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        stored_path = settings.storage_dir / file_item.stored_name
        if not stored_path.exists():
            file_item.processing_status = ProcessingStatus.FAILED.value
            file_item.scan_status = file_item.scan_status or ScanStatus.FAILED.value
            file_item.scan_details = "stored file not found during metadata extraction"
            await session.commit()
            send_file_alert.delay(file_id)
            return

        metadata = {
            "extension": Path(file_item.original_name).suffix.lower(),
            "size_bytes": file_item.size,
            "mime_type": file_item.mime_type,
        }

        if file_item.mime_type.startswith("text/"):
            content = stored_path.read_text(encoding="utf-8", errors="ignore")
            metadata["line_count"] = len(content.splitlines())
            metadata["char_count"] = len(content)
        elif file_item.mime_type == "application/pdf":
            content = stored_path.read_bytes()
            metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

        file_item.metadata_json = metadata
        file_item.processing_status = ProcessingStatus.PROCESSED.value
        await session.commit()

    send_file_alert.delay(file_id)


async def _send_file_alert(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        if file_item.processing_status == ProcessingStatus.FAILED.value:
            alert = Alert(file_id=file_id, level=AlertLevel.CRITICAL.value, message="File processing failed")
        elif file_item.requires_attention:
            alert = Alert(
                file_id=file_id,
                level=AlertLevel.WARNING.value,
                message=f"File requires attention: {file_item.scan_details}",
            )
        else:
            alert = Alert(file_id=file_id, level=AlertLevel.INFO.value, message="File processed successfully")

        session.add(alert)
        await session.commit()


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    run_in_worker_loop(_scan_file_for_threats(file_id))


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    run_in_worker_loop(_extract_file_metadata(file_id))


@celery_app.task
def send_file_alert(file_id: str) -> None:
    run_in_worker_loop(_send_file_alert(file_id))
