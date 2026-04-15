from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.text_variation import VariationGenerateRequest, VariationRead, VariationUpdate
from app.services import variation_service
from app.tasks.generate_variations import run_generate_variations

router = APIRouter(tags=["variations"], dependencies=[Depends(get_current_user)])


@router.post("/campaigns/{campaign_id}/variations/generate")
async def generate_variations(
    campaign_id: int,
    data: VariationGenerateRequest = VariationGenerateRequest(),
    db: AsyncSession = Depends(get_db),
):
    run_generate_variations.delay(campaign_id, data.count)
    return {"status": "started", "campaign_id": campaign_id, "count": data.count}


@router.get("/campaigns/{campaign_id}/variations", response_model=list[VariationRead])
async def list_variations(campaign_id: int, db: AsyncSession = Depends(get_db)):
    return await variation_service.get_variations(db, campaign_id)


@router.put("/variations/{variation_id}", response_model=VariationRead)
async def update_variation(
    variation_id: int, data: VariationUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        return await variation_service.update_variation(db, variation_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/variations/{variation_id}", status_code=204)
async def delete_variation(variation_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await variation_service.delete_variation(db, variation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
