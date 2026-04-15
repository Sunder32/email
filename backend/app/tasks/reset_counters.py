import asyncio

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.domain import Domain
from app.models.mailbox import Mailbox


def _get_async_session() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _reset_hourly():
    session_factory = _get_async_session()
    async with session_factory() as db:
        await db.execute(update(Domain).values(sent_this_hour=0))
        await db.execute(update(Mailbox).values(sent_this_hour=0))
        await db.commit()


async def _reset_daily():
    session_factory = _get_async_session()
    async with session_factory() as db:
        await db.execute(update(Domain).values(sent_today=0, sent_this_hour=0))
        await db.execute(update(Mailbox).values(sent_today=0, sent_this_hour=0))
        await db.commit()


@celery_app.task(name="app.tasks.reset_counters.reset_hourly")
def reset_hourly():
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_reset_hourly())
    finally:
        loop.close()


@celery_app.task(name="app.tasks.reset_counters.reset_daily")
def reset_daily():
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_reset_daily())
    finally:
        loop.close()
