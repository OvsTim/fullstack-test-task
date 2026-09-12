from fastapi import APIRouter, Depends

from src.api.deps import get_alert_service
from src.schemas.alerts import AlertItem
from src.services.alerting import AlertService

router = APIRouter()


@router.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view(alerts: AlertService = Depends(get_alert_service)):
    return await alerts.list()
