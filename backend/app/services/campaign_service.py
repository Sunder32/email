from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignStats, CampaignUpdate
from app.utils.time_helpers import calc_eta, elapsed_seconds


async def create_campaign(db: AsyncSession, data: CampaignCreate) -> CampaignRead:
    campaign = Campaign(**data.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return CampaignRead.model_validate(campaign)


async def get_campaigns(db: AsyncSession) -> list[CampaignRead]:
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return [CampaignRead.model_validate(c) for c in result.scalars().all()]


async def get_campaign(db: AsyncSession, campaign_id: int) -> Campaign:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise ValueError("Campaign not found")
    return campaign


async def get_campaign_read(db: AsyncSession, campaign_id: int) -> CampaignRead:
    campaign = await get_campaign(db, campaign_id)
    return CampaignRead.model_validate(campaign)


async def update_campaign(db: AsyncSession, campaign_id: int, data: CampaignUpdate) -> CampaignRead:
    campaign = await get_campaign(db, campaign_id)
    if campaign.status != CampaignStatus.DRAFT:
        raise ValueError("Can only edit campaigns in draft status")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    await db.commit()
    await db.refresh(campaign)
    return CampaignRead.model_validate(campaign)


async def delete_campaign(db: AsyncSession, campaign_id: int) -> None:
    campaign = await get_campaign(db, campaign_id)
    await db.delete(campaign)
    await db.commit()


async def start_campaign(db: AsyncSession, campaign_id: int) -> CampaignRead:
    campaign = await get_campaign(db, campaign_id)
    if campaign.status == CampaignStatus.DRAFT:
        campaign.valid_contacts = campaign.total_contacts
        campaign.status = CampaignStatus.READY
        await db.commit()
        await db.refresh(campaign)
    if campaign.status not in (CampaignStatus.READY, CampaignStatus.PAUSED):
        raise ValueError(f"Cannot start campaign in '{campaign.status.value}' status")
    campaign.status = CampaignStatus.RUNNING
    if not campaign.started_at:
        campaign.started_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campaign)
    return CampaignRead.model_validate(campaign)


async def pause_campaign(db: AsyncSession, campaign_id: int) -> CampaignRead:
    campaign = await get_campaign(db, campaign_id)
    if campaign.status != CampaignStatus.RUNNING:
        raise ValueError("Campaign is not running")
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    await db.refresh(campaign)
    return CampaignRead.model_validate(campaign)


async def stop_campaign(db: AsyncSession, campaign_id: int) -> CampaignRead:
    campaign = await get_campaign(db, campaign_id)
    if campaign.status not in (CampaignStatus.RUNNING, CampaignStatus.PAUSED):
        raise ValueError("Campaign is not running or paused")
    campaign.status = CampaignStatus.COMPLETED
    campaign.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campaign)
    return CampaignRead.model_validate(campaign)


async def get_campaign_stats(db: AsyncSession, campaign_id: int) -> CampaignStats:
    campaign = await get_campaign(db, campaign_id)
    denominator = campaign.valid_contacts if campaign.valid_contacts > 0 else campaign.total_contacts
    remaining = denominator - campaign.sent_count - campaign.failed_count
    progress = (campaign.sent_count / denominator * 100) if denominator > 0 else 0.0

    invalid_res = await db.execute(
        select(func.count(Contact.id)).where(
            Contact.campaign_id == campaign_id, Contact.is_valid == False
        )
    )
    invalid_count = invalid_res.scalar() or 0

    return CampaignStats(
        total_contacts=campaign.total_contacts,
        valid_contacts=campaign.valid_contacts,
        sent_count=campaign.sent_count,
        failed_count=campaign.failed_count,
        invalid_count=invalid_count,
        remaining=max(remaining, 0),
        progress_percent=round(progress, 2),
        elapsed_seconds=elapsed_seconds(campaign.started_at),
        eta_seconds=calc_eta(campaign.sent_count, denominator, campaign.started_at),
    )
