import asyncio
from datetime import datetime

from sqlalchemy import select

from app.db.engine import async_session
from app.db.models import Notification, NotificationStatus
from app.core.logger import get_logger

logger = get_logger("worker")


class NotificationWorker:
    def __init__(self, email_service, interval_seconds: int = 10):
        self.email_service = email_service
        self.interval_seconds = interval_seconds
        self.running = False

    async def start(self):
        self.running = True

        while self.running:
            await self.process()
            await asyncio.sleep(self.interval_seconds)

    async def process(self):
        async with async_session() as session:
            result = await session.execute(
                select(Notification).where(
                    Notification.status == NotificationStatus.PENDING
                )
            )

            notifications = result.scalars().all()

            for n in notifications:
                try:
                    await self.email_service.send_email(
                        to=str(n.recipient_id),
                        subject=f"Nova notificação ({n.type})",
                        content=f"Tarefa: {n.task_id}",
                    )

                    n.status = NotificationStatus.SENT
                    n.sent_at = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Erro notification {n.id}: {e}")
                    n.status = NotificationStatus.FAILED

                session.add(n)

            await session.commit()