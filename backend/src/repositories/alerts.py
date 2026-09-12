from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[Alert]:
        result = await self._session.execute(select(Alert).order_by(Alert.created_at.desc()))
        return list(result.scalars().all())

    def add(self, alert: Alert) -> None:
        self._session.add(alert)
