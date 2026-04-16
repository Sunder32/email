import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.pagination import PaginationParams
from app.models.contact import Contact
from app.models.send_log import SendLog
from app.schemas.campaign import CampaignReport
from app.schemas.contact import ContactRead, ContactUploadResponse
from app.services import contact_service
from app.tasks.validate_contacts import run_validate_contacts
from app.utils.error_labels import smtp_error_label, validation_error_label

router = APIRouter(prefix="/campaigns/{campaign_id}/contacts", tags=["contacts"], dependencies=[Depends(get_current_user)])


@router.post("/upload", response_model=ContactUploadResponse)
async def upload_contacts(
    campaign_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    try:
        return await contact_service.upload_contacts(db, campaign_id, file.filename or "file.csv", content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    campaign_id: int,
    status: str | None = None,
    validation: str | None = None,
    search: str | None = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await contact_service.get_contacts(
        db, campaign_id, status, validation, search, pagination.offset, pagination.size
    )


@router.post("/validate")
async def validate_contacts(campaign_id: int, db: AsyncSession = Depends(get_db)):
    run_validate_contacts.delay(campaign_id)
    return {"status": "started", "campaign_id": campaign_id}


@router.post("/mark-all-valid")
async def mark_all_valid(campaign_id: int, db: AsyncSession = Depends(get_db)):
    count = await contact_service.mark_all_valid(db, campaign_id)
    return {"marked_valid": count}


@router.get("/report", response_model=CampaignReport)
async def campaign_report(campaign_id: int, db: AsyncSession = Depends(get_db)):
    return await contact_service.build_campaign_report(db, campaign_id)


@router.get("/export")
async def export_report(campaign_id: int, db: AsyncSession = Depends(get_db)):
    contacts_res = await db.execute(
        select(Contact).where(Contact.campaign_id == campaign_id).order_by(Contact.id)
    )
    contacts = list(contacts_res.scalars().all())

    logs_res = await db.execute(
        select(SendLog)
        .options(selectinload(SendLog.mailbox))
        .where(SendLog.campaign_id == campaign_id)
    )
    logs_by_contact = {log.contact_id: log for log in logs_res.scalars().all()}

    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([
        "Email",
        "Валидация",
        "Ошибка валидации",
        "Статус отправки",
        "Ошибка отправки",
        "Ящик отправителя",
        "Тема письма",
        "Время отправки",
    ])

    for c in contacts:
        log = logs_by_contact.get(c.id)
        validation_status = (
            "валидный" if c.is_valid is True else
            "невалидный" if c.is_valid is False else
            "не проверен"
        )
        writer.writerow([
            c.email,
            validation_status,
            validation_error_label(c.validation_error) or "",
            c.status,
            smtp_error_label(log.error_message) if log and log.error_message else "",
            log.mailbox.email if log and log.mailbox else "",
            log.subject_used if log else "",
            log.sent_at.strftime("%Y-%m-%d %H:%M:%S") if log else "",
        ])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="campaign_{campaign_id}_report.csv"'},
    )
