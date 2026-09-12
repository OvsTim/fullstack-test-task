from fastapi import APIRouter

from src.schemas.alerts import AlertItem
from src.service import list_alerts

router = APIRouter()


@router.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view():
    return await list_alerts()
