from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate, DomainWithMailboxes
from app.services import domain_service

router = APIRouter(prefix="/domains", tags=["domains"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[DomainWithMailboxes])
async def list_domains(db: AsyncSession = Depends(get_db)):
    return await domain_service.get_domains(db)


@router.post("", response_model=DomainRead, status_code=201)
async def create_domain(data: DomainCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await domain_service.create_domain(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{domain_id}", response_model=DomainRead)
async def update_domain(domain_id: int, data: DomainUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await domain_service.update_domain(db, domain_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{domain_id}", status_code=204)
async def delete_domain(domain_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await domain_service.delete_domain(db, domain_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
