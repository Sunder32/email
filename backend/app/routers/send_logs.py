from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.pagination import PaginationParams
from app.models.send_log import SendLog
from app.schemas.send_log import SendLogRead

router = APIRouter(prefix="/campaigns/{campaign_id}/logs", tags=["send_logs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SendLogRead])
async def list_send_logs(
    campaign_id: int,
    mailbox_id: int | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    query = select(SendLog).where(SendLog.campaign_id == campaign_id)
    if mailbox_id:
        query = query.where(SendLog.mailbox_id == mailbox_id)
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(pagination.offset).limit(pagination.size)
    result = await db.execute(query)
    return [SendLogRead.model_validate(log) for log in result.scalars().all()]
