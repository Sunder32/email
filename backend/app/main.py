import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.pubsub import campaign_event_listener
from app.core.websocket_manager import ws_manager
from app.routers import auth, campaigns, contacts, domains, mailboxes, send_logs, variations, ws

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener_task = asyncio.create_task(campaign_event_listener(ws_manager))
    logger.info("Campaign event listener started")
    try:
        yield
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Email Service",
    description="Smart email campaign management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(domains.router, prefix="/api")
app.include_router(mailboxes.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(variations.router, prefix="/api")
app.include_router(send_logs.router, prefix="/api")
app.include_router(ws.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
