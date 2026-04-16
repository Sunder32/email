from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.utils.email_validator import validate_email_full


async def validate_campaign_contacts(db: AsyncSession, campaign_id: int, progress_callback=None):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return

    campaign.status = CampaignStatus.VALIDATING
    await db.commit()

    result = await db.execute(
        select(Contact)
        .where(Contact.campaign_id == campaign_id, Contact.is_valid.is_(None))
        .order_by(Contact.id)
    )
    contacts = list(result.scalars().all())
    total = len(contacts)
    valid_count = 0
    invalid_count = 0

    for i, contact in enumerate(contacts):
        is_valid, error = validate_email_full(contact.email)
        contact.is_valid = is_valid
        contact.validation_error = error

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

        if (i + 1) % 10 == 0 or i == total - 1:
            await db.commit()
            if progress_callback:
                progress_callback(
                    total=total,
                    checked=i + 1,
                    valid=valid_count,
                    invalid=invalid_count,
                )

    from sqlalchemy import func
    count_res = await db.execute(
        select(func.count(Contact.id)).where(
            Contact.campaign_id == campaign_id, Contact.is_valid == True
        )
    )
    campaign.valid_contacts = count_res.scalar() or 0
    campaign.status = CampaignStatus.READY
    await db.commit()
