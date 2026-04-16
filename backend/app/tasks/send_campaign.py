import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.sending_service import send_campaign


async def _run(campaign_id: int):
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            await send_campaign(db, campaign_id)
    finally:
        await engine.dispose()


@celery_app.task(name="app.tasks.send_campaign.run_send_campaign", bind=True)
def run_send_campaign(self, campaign_id: int):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run(campaign_id))
    finally:
        loop.close()
