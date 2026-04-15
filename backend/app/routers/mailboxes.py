from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.mailbox import MailboxCreate, MailboxRead, MailboxTestResult, MailboxUpdate
from app.services import mailbox_service

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"], dependencies=[Depends(get_current_user)])


@router.post("/domain/{domain_id}", response_model=MailboxRead, status_code=201)
async def create_mailbox(domain_id: int, data: MailboxCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await mailbox_service.create_mailbox(db, domain_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{mailbox_id}", response_model=MailboxRead)
async def update_mailbox(mailbox_id: int, data: MailboxUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await mailbox_service.update_mailbox(db, mailbox_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{mailbox_id}", status_code=204)
async def delete_mailbox(mailbox_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await mailbox_service.delete_mailbox(db, mailbox_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{mailbox_id}/test", response_model=MailboxTestResult)
async def test_mailbox(mailbox_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await mailbox_service.test_mailbox(db, mailbox_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
