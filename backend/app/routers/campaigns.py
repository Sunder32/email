from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignStats, CampaignUpdate
from app.services import campaign_service
from app.tasks.send_campaign import run_send_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CampaignRead])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    return await campaign_service.get_campaigns(db)


@router.post("", response_model=CampaignRead, status_code=201)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    return await campaign_service.create_campaign(db, data)


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await campaign_service.get_campaign_read(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(campaign_id: int, data: CampaignUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await campaign_service.update_campaign(db, campaign_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await campaign_service.delete_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{campaign_id}/start", response_model=CampaignRead)
async def start_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    try:
        campaign = await campaign_service.start_campaign(db, campaign_id)
        run_send_campaign.delay(campaign_id)
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/pause", response_model=CampaignRead)
async def pause_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await campaign_service.pause_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/stop", response_model=CampaignRead)
async def stop_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await campaign_service.stop_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def campaign_stats(campaign_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await campaign_service.get_campaign_stats(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
