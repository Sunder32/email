import asyncio
import smtplib
from datetime import datetime, timezone

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pubsub import publish_campaign_event
from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.models.domain import Domain
from app.models.mailbox import Mailbox
from app.models.send_log import SendLog
from app.models.text_variation import TextVariation
from app.services.contact_service import get_pending_valid_contacts
from app.services.rotation_service import build_rotation_pool
from app.services.smtp_service import send_email
from app.utils.time_helpers import random_delay


def pick_variation(variations: list[TextVariation]) -> TextVariation | None:
    if not variations:
        return None
    return min(variations, key=lambda v: v.times_used)


def apply_iceberg(original_body: str, new_iceberg: str) -> str:
    parts = original_body.split("\n\n", 1)
    if len(parts) == 2:
        return new_iceberg + "\n\n" + parts[1]
    return original_body


def _is_transient_smtp_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "timeout" in msg or "timed out" in msg:
        return True
    if "connection" in msg and ("reset" in msg or "refused" in msg or "unexpectedly closed" in msg):
        return True
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return True
    if isinstance(exc, smtplib.SMTPResponseException) and 400 <= exc.smtp_code < 500:
        return True
    return False


async def _send_with_retry(slot, contact_email: str, subject: str, body: str) -> None:
    last_error: Exception | None = None
    for attempt in range(1, settings.SMTP_MAX_ATTEMPTS + 1):
        try:
            await asyncio.to_thread(
                send_email,
                slot.mailbox.smtp_host,
                slot.mailbox.smtp_port,
                slot.mailbox.login,
                slot.password,
                slot.mailbox.use_tls,
                slot.mailbox.email,
                contact_email,
                subject,
                body,
            )
            return
        except Exception as e:
            last_error = e
            if attempt < settings.SMTP_MAX_ATTEMPTS and _is_transient_smtp_error(e):
                await asyncio.sleep(settings.SMTP_RETRY_BACKOFF_BASE ** attempt)
                continue
            raise

    if last_error:
        raise last_error


async def _increment_counters_atomic(db: AsyncSession, mailbox_id: int, domain_id: int) -> None:
    """Atomic SQL update — safe under concurrent workers."""
    await db.execute(
        sql_update(Mailbox)
        .where(Mailbox.id == mailbox_id)
        .values(sent_this_hour=Mailbox.sent_this_hour + 1, sent_today=Mailbox.sent_today + 1)
    )
    await db.execute(
        sql_update(Domain)
        .where(Domain.id == domain_id)
        .values(sent_this_hour=Domain.sent_this_hour + 1, sent_today=Domain.sent_today + 1)
    )


async def send_campaign(db: AsyncSession, campaign_id: int):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return

    if campaign.skip_validation:
        await db.execute(
            sql_update(Contact)
            .where(Contact.campaign_id == campaign_id, Contact.is_valid.is_(None))
            .values(is_valid=True)
        )
        await db.commit()
        await db.refresh(campaign)

    contacts = await get_pending_valid_contacts(db, campaign_id)
    if not contacts:
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.now(timezone.utc)
        await db.commit()
        publish_campaign_event(campaign_id, {"type": "status", "data": {"status": "completed"}})
        return

    pool = await build_rotation_pool(db, campaign.rotate_every_n)
    if pool.is_empty:
        campaign.status = CampaignStatus.PAUSED
        await db.commit()
        publish_campaign_event(
            campaign_id,
            {"type": "status", "data": {"status": "paused", "reason": "No active mailboxes"}},
        )
        return

    result = await db.execute(
        select(TextVariation)
        .where(TextVariation.campaign_id == campaign_id)
        .order_by(TextVariation.id)
    )
    variations = list(result.scalars().all())

    for i, contact in enumerate(contacts):
        await db.refresh(campaign)
        if campaign.status != CampaignStatus.RUNNING:
            break

        slot = pool.get_next_available()
        if not slot:
            campaign.status = CampaignStatus.PAUSED
            await db.commit()
            publish_campaign_event(
                campaign_id,
                {"type": "status", "data": {"status": "paused", "reason": "All mailboxes exhausted"}},
            )
            break

        if i % 2 == 0:
            subject = campaign.original_subject
            body = campaign.original_body
        else:
            variation = pick_variation(variations)
            if variation:
                subject = variation.subject_variant
                body = apply_iceberg(campaign.original_body, variation.iceberg_variant)
                variation.times_used += 1
            else:
                subject = campaign.original_subject
                body = campaign.original_body

        log = SendLog(
            campaign_id=campaign_id,
            contact_id=contact.id,
            mailbox_id=slot.mailbox.id,
            subject_used=subject,
            body_preview=body[:200],
            status="pending",
        )

        try:
            await _send_with_retry(slot, contact.email, subject, body)
            log.status = "sent"
            contact.status = "sent"
            campaign.sent_count += 1
            await _increment_counters_atomic(db, slot.mailbox.id, slot.domain.id)
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)[:500]
            contact.status = "failed"
            campaign.failed_count += 1

        db.add(log)
        if log.status == "sent":
            pool.advance()
        await db.commit()

        # Refresh counters from DB so can_send checks are accurate
        if log.status == "sent":
            await db.refresh(slot.mailbox)
            await db.refresh(slot.domain)

        publish_campaign_event(campaign_id, {
            "type": "progress",
            "data": {
                "sent": campaign.sent_count,
                "failed": campaign.failed_count,
                "total": campaign.valid_contacts if campaign.valid_contacts > 0 else campaign.total_contacts,
                "valid": campaign.valid_contacts,
                "current_mailbox": slot.mailbox.email,
                "current_domain": slot.domain.name,
                "last_contact": contact.email,
                "last_subject": subject,
                "last_status": log.status,
            },
        })

        await asyncio.sleep(random_delay(campaign.delay_min_sec, campaign.delay_max_sec))

    await db.refresh(campaign)
    if campaign.status == CampaignStatus.RUNNING:
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.now(timezone.utc)
        await db.commit()

    publish_campaign_event(campaign_id, {"type": "status", "data": {"status": campaign.status.value}})
