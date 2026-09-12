from src.core.enums import AlertLevel, ProcessingStatus
from src.db.models import Alert, StoredFile
from src.repositories.alerts import AlertRepository


def build_alert(file_item: StoredFile) -> Alert:
    if file_item.processing_status == ProcessingStatus.FAILED.value:
        return Alert(
            file_id=file_item.id,
            level=AlertLevel.CRITICAL.value,
            message="File processing failed",
        )
    if file_item.requires_attention:
        return Alert(
            file_id=file_item.id,
            level=AlertLevel.WARNING.value,
            message=f"File requires attention: {file_item.scan_details}",
        )
    return Alert(
        file_id=file_item.id,
        level=AlertLevel.INFO.value,
        message="File processed successfully",
    )


class AlertService:
    def __init__(self, alerts: AlertRepository) -> None:
        self._alerts = alerts

    async def list(self) -> list[Alert]:
        return await self._alerts.list()
