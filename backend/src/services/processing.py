import logging

from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import ProcessingStatus, ScanStatus
from src.db.models import StoredFile
from src.db.session import sync_session_maker
from src.services.alerting import build_alert
from src.services.metadata import extract_metadata
from src.services.scanning import scan
from src.services.storage import LocalStorage

logger = logging.getLogger(__name__)


def process_uploaded_file(file_id: str) -> None:
    storage = LocalStorage(settings.storage_dir)
    with sync_session_maker() as session:
        process_file(session, storage, file_id)


def process_file(session: Session, storage: LocalStorage, file_id: str) -> None:
    file_item = session.get(StoredFile, file_id)
    if file_item is None:
        return

    try:
        _run_processing(session, storage, file_item)
        session.commit()
    except Exception:
        logger.exception("Failed to process file %s", file_id)
        session.rollback()
        _mark_failed(session, file_id)


def _run_processing(session: Session, storage: LocalStorage, file_item: StoredFile) -> None:
    file_item.processing_status = ProcessingStatus.PROCESSING.value
    result = scan(file_item.original_name, file_item.mime_type, file_item.size)
    file_item.scan_status = result.status
    file_item.scan_details = result.details
    file_item.requires_attention = result.requires_attention

    if not storage.exists(file_item.stored_name):
        file_item.processing_status = ProcessingStatus.FAILED.value
        file_item.scan_status = file_item.scan_status or ScanStatus.FAILED.value
        file_item.scan_details = "stored file not found during metadata extraction"
        session.add(build_alert(file_item))
        return

    with storage.open(file_item.stored_name) as stream:
        file_item.metadata_json = extract_metadata(
            original_name=file_item.original_name,
            mime_type=file_item.mime_type,
            size=file_item.size,
            stream=stream,
        )

    file_item.processing_status = ProcessingStatus.PROCESSED.value
    session.add(build_alert(file_item))


def _mark_failed(session: Session, file_id: str) -> None:
    file_item = session.get(StoredFile, file_id)
    if file_item is None:
        return

    file_item.processing_status = ProcessingStatus.FAILED.value
    file_item.scan_status = ScanStatus.FAILED.value
    file_item.scan_details = file_item.scan_details or "file processing failed"
    session.add(build_alert(file_item))
    session.commit()
