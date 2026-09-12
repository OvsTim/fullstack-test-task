import asyncio

from src.core.config import settings
from src.core.enums import ProcessingStatus, ScanStatus
from src.db.session import async_session_maker
from src.repositories.alerts import AlertRepository
from src.repositories.files import FileRepository
from src.services.alerting import build_alert
from src.services.metadata import extract_metadata
from src.services.scanning import scan
from src.services.storage import LocalStorage
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
        files = FileRepository(session)
        file_item = await files.get(file_id)
        if not file_item:
            return

        file_item.processing_status = ProcessingStatus.PROCESSING.value
        result = scan(file_item.original_name, file_item.mime_type, file_item.size)
        file_item.scan_status = result.status
        file_item.scan_details = result.details
        file_item.requires_attention = result.requires_attention
        await session.commit()

    extract_file_metadata.delay(file_id)


async def _extract_file_metadata(file_id: str) -> None:
    storage = LocalStorage(settings.storage_dir)
    async with async_session_maker() as session:
        files = FileRepository(session)
        file_item = await files.get(file_id)
        if not file_item:
            return

        if not storage.exists(file_item.stored_name):
            file_item.processing_status = ProcessingStatus.FAILED.value
            file_item.scan_status = file_item.scan_status or ScanStatus.FAILED.value
            file_item.scan_details = "stored file not found during metadata extraction"
            await session.commit()
            send_file_alert.delay(file_id)
            return

        with storage.open(file_item.stored_name) as stream:
            content = stream.read()

        file_item.metadata_json = extract_metadata(
            original_name=file_item.original_name,
            mime_type=file_item.mime_type,
            size=file_item.size,
            content=content,
        )
        file_item.processing_status = ProcessingStatus.PROCESSED.value
        await session.commit()

    send_file_alert.delay(file_id)


async def _send_file_alert(file_id: str) -> None:
    async with async_session_maker() as session:
        files = FileRepository(session)
        alerts = AlertRepository(session)
        file_item = await files.get(file_id)
        if not file_item:
            return

        alerts.add(build_alert(file_item))
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
