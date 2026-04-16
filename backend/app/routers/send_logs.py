from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.pagination import PaginationParams
from app.models.send_log import SendLog
from app.schemas.send_log import SendLogRead
from app.utils.error_labels import smtp_error_label

router = APIRouter(prefix="/campaigns/{campaign_id}/logs", tags=["send_logs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SendLogRead])
async def list_send_logs(
    campaign_id: int,
    mailbox_id: int | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SendLog)
        .options(selectinload(SendLog.contact), selectinload(SendLog.mailbox))
        .where(SendLog.campaign_id == campaign_id)
    )
    if mailbox_id:
        query = query.where(SendLog.mailbox_id == mailbox_id)
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(pagination.offset).limit(pagination.size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        SendLogRead(
            id=log.id,
            campaign_id=log.campaign_id,
            contact_id=log.contact_id,
            contact_email=log.contact.email if log.contact else None,
            mailbox_id=log.mailbox_id,
            mailbox_email=log.mailbox.email if log.mailbox else None,
            subject_used=log.subject_used,
            body_preview=log.body_preview,
            status=log.status,
            error_message=log.error_message,
            error_label=smtp_error_label(log.error_message),
            sent_at=log.sent_at,
        )
        for log in logs
    ]
