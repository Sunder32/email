from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.pagination import PaginationParams
from app.schemas.contact import ContactRead, ContactUploadResponse
from app.services import contact_service
from app.tasks.validate_contacts import run_validate_contacts

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
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await contact_service.get_contacts(db, campaign_id, status, pagination.offset, pagination.size)


@router.post("/validate")
async def validate_contacts(campaign_id: int, db: AsyncSession = Depends(get_db)):
    run_validate_contacts.delay(campaign_id)
    return {"status": "started", "campaign_id": campaign_id}
