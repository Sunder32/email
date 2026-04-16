import asyncio

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.domain import Domain
from app.models.mailbox import Mailbox


async def _reset(daily: bool):
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            if daily:
                await db.execute(update(Domain).values(sent_today=0, sent_this_hour=0))
                await db.execute(update(Mailbox).values(sent_today=0, sent_this_hour=0))
            else:
                await db.execute(update(Domain).values(sent_this_hour=0))
                await db.execute(update(Mailbox).values(sent_this_hour=0))
            await db.commit()
    finally:
        await engine.dispose()


@celery_app.task(name="app.tasks.reset_counters.reset_hourly")
def reset_hourly():
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_reset(daily=False))
    finally:
        loop.close()


@celery_app.task(name="app.tasks.reset_counters.reset_daily")
def reset_daily():
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_reset(daily=True))
    finally:
        loop.close()
