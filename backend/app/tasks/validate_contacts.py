import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.validation_service import validate_campaign_contacts


def _get_async_session() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _run(campaign_id: int):
    session_factory = _get_async_session()
    async with session_factory() as db:
        await validate_campaign_contacts(db, campaign_id)


@celery_app.task(name="app.tasks.validate_contacts.run_validate_contacts", bind=True)
def run_validate_contacts(self, campaign_id: int):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run(campaign_id))
    finally:
        loop.close()
