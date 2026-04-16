import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.variation_service import generate_variations


async def _run(campaign_id: int, count: int):
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            await generate_variations(db, campaign_id, count)
    finally:
        await engine.dispose()


@celery_app.task(name="app.tasks.generate_variations.run_generate_variations", bind=True)
def run_generate_variations(self, campaign_id: int, count: int = 30):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run(campaign_id, count))
    finally:
        loop.close()
