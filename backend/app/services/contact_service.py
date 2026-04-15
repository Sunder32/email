from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.schemas.contact import ContactRead, ContactUploadResponse
from app.utils.csv_parser import parse_emails


async def upload_contacts(
    db: AsyncSession, campaign_id: int, filename: str, content: bytes
) -> ContactUploadResponse:
    emails = parse_emails(filename, content)
    total = len(emails)

    existing = await db.execute(
        select(Contact.email).where(Contact.campaign_id == campaign_id)
    )
    existing_set = {row[0] for row in existing.fetchall()}

    unique_emails = []
    seen = set()
    for email in emails:
        if email not in existing_set and email not in seen:
            unique_emails.append(email)
            seen.add(email)

    duplicates = total - len(unique_emails)

    contacts = [Contact(campaign_id=campaign_id, email=e) for e in unique_emails]
    db.add_all(contacts)

    campaign = await db.get(Campaign, campaign_id)
    if campaign:
        campaign.total_contacts += len(unique_emails)

    await db.commit()
    return ContactUploadResponse(total=total, parsed=len(unique_emails), duplicates=duplicates)


async def get_contacts(
    db: AsyncSession, campaign_id: int, status: str | None, offset: int, limit: int
) -> list[ContactRead]:
    query = select(Contact).where(Contact.campaign_id == campaign_id)
    if status:
        query = query.where(Contact.status == status)
    query = query.order_by(Contact.id).offset(offset).limit(limit)
    result = await db.execute(query)
    return [ContactRead.model_validate(c) for c in result.scalars().all()]


async def get_pending_valid_contacts(db: AsyncSession, campaign_id: int) -> list[Contact]:
    from sqlalchemy import or_
    result = await db.execute(
        select(Contact)
        .where(
            Contact.campaign_id == campaign_id,
            or_(Contact.is_valid == True, Contact.is_valid.is_(None)),
            Contact.status == "pending",
        )
        .order_by(Contact.id)
    )
    return list(result.scalars().all())
