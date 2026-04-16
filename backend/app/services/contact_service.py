from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.schemas.campaign import CampaignReport, ValidationBreakdown
from app.schemas.contact import ContactRead, ContactUploadResponse
from app.utils.csv_parser import parse_emails
from app.utils.error_labels import validation_category, validation_error_label


def _to_read(contact: Contact) -> ContactRead:
    return ContactRead(
        id=contact.id,
        campaign_id=contact.campaign_id,
        email=contact.email,
        is_valid=contact.is_valid,
        validation_error=contact.validation_error,
        validation_error_label=validation_error_label(contact.validation_error),
        status=contact.status,
        created_at=contact.created_at,
    )


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
    db: AsyncSession,
    campaign_id: int,
    status: str | None,
    validation: str | None,
    search: str | None,
    offset: int,
    limit: int,
) -> list[ContactRead]:
    query = select(Contact).where(Contact.campaign_id == campaign_id)
    if status:
        query = query.where(Contact.status == status)
    if validation == "valid":
        query = query.where(Contact.is_valid == True)
    elif validation == "invalid":
        query = query.where(Contact.is_valid == False)
    elif validation == "pending":
        query = query.where(Contact.is_valid.is_(None))
    if search:
        query = query.where(Contact.email.ilike(f"%{search}%"))
    query = query.order_by(Contact.id).offset(offset).limit(limit)
    result = await db.execute(query)
    return [_to_read(c) for c in result.scalars().all()]


async def get_pending_valid_contacts(db: AsyncSession, campaign_id: int) -> list[Contact]:
    campaign = await db.get(Campaign, campaign_id)
    query = select(Contact).where(
        Contact.campaign_id == campaign_id,
        Contact.status == "pending",
    )
    if campaign and campaign.skip_validation:
        pass
    else:
        query = query.where(or_(Contact.is_valid == True, Contact.is_valid.is_(None)))

    result = await db.execute(query.order_by(Contact.id))
    return list(result.scalars().all())


async def mark_all_valid(db: AsyncSession, campaign_id: int) -> int:
    """Override validation: mark all non-sent contacts as valid."""
    result = await db.execute(
        select(Contact).where(
            Contact.campaign_id == campaign_id,
            Contact.status == "pending",
        )
    )
    contacts = list(result.scalars().all())
    for c in contacts:
        c.is_valid = True
        c.validation_error = None

    campaign = await db.get(Campaign, campaign_id)
    if campaign:
        campaign.valid_contacts = len(contacts)

    await db.commit()
    return len(contacts)


async def build_campaign_report(db: AsyncSession, campaign_id: int) -> CampaignReport:
    result = await db.execute(
        select(Contact).where(Contact.campaign_id == campaign_id)
    )
    contacts = list(result.scalars().all())

    total = len(contacts)
    valid = sum(1 for c in contacts if c.is_valid is True)
    invalid = sum(1 for c in contacts if c.is_valid is False)
    sent = sum(1 for c in contacts if c.status == "sent")
    failed = sum(1 for c in contacts if c.status == "failed")
    pending = sum(1 for c in contacts if c.status == "pending")

    breakdown = {"syntax_errors": 0, "no_mx": 0, "smtp_rejected": 0, "disposable": 0, "other": 0}
    for c in contacts:
        if c.is_valid is False:
            cat = validation_category(c.validation_error)
            breakdown[cat] += 1

    return CampaignReport(
        total_contacts=total,
        valid_contacts=valid,
        invalid_contacts=invalid,
        sent_count=sent,
        failed_count=failed,
        pending_count=pending,
        validation_breakdown=ValidationBreakdown(**breakdown),
    )
