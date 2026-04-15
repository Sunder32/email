import random
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.models.contact import Contact
from app.models.send_log import SendLog
from app.models.text_variation import TextVariation
from app.services.contact_service import get_pending_valid_contacts
from app.services.rotation_service import RotationPool, build_rotation_pool
from app.services.smtp_service import send_email
from app.utils.time_helpers import random_delay


def pick_variation(variations: list[TextVariation], index: int) -> TextVariation | None:
    if not variations:
        return None
    least_used = sorted(variations, key=lambda v: v.times_used)
    return least_used[0]


def apply_iceberg(original_body: str, new_iceberg: str) -> str:
    parts = original_body.split("\n\n", 1)
    if len(parts) == 2:
        return new_iceberg + "\n\n" + parts[1]
    return new_iceberg


async def send_campaign(db: AsyncSession, campaign_id: int, ws_broadcast=None):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return

    contacts = await get_pending_valid_contacts(db, campaign_id)
    if not contacts:
        campaign.status = CampaignStatus.COMPLETED
        await db.commit()
        return

    pool = await build_rotation_pool(db, campaign.rotate_every_n)
    if pool.is_empty:
        campaign.status = CampaignStatus.PAUSED
        await db.commit()
        return

    from sqlalchemy import select
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
            if ws_broadcast:
                await ws_broadcast(campaign_id, {
                    "type": "status",
                    "data": {"status": "paused", "reason": "All mailboxes exhausted"},
                })
            break

        if i % 2 == 0:
            subject = campaign.original_subject
            body = campaign.original_body
        else:
            variation = pick_variation(variations, i)
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
            send_email(
                host=slot.mailbox.smtp_host,
                port=slot.mailbox.smtp_port,
                login=slot.mailbox.login,
                password=slot.password,
                use_tls=slot.mailbox.use_tls,
                from_email=slot.mailbox.email,
                to_email=contact.email,
                subject=subject,
                body_html=body,
            )
            log.status = "sent"
            contact.status = "sent"
            campaign.sent_count += 1
            slot.increment()
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)[:500]
            contact.status = "failed"
            campaign.failed_count += 1

        db.add(log)
        pool.advance()
        await db.commit()

        if ws_broadcast:
            await ws_broadcast(campaign_id, {
                "type": "progress",
                "data": {
                    "sent": campaign.sent_count,
                    "failed": campaign.failed_count,
                    "total": campaign.valid_contacts,
                    "current_mailbox": slot.mailbox.email,
                    "current_domain": slot.domain.name,
                    "last_contact": contact.email,
                    "last_subject": subject,
                    "last_status": log.status,
                },
            })

        delay = random_delay(campaign.delay_min_sec, campaign.delay_max_sec)
        time.sleep(delay)

    await db.refresh(campaign)
    if campaign.status == CampaignStatus.RUNNING:
        campaign.status = CampaignStatus.COMPLETED
        from datetime import datetime, timezone
        campaign.completed_at = datetime.now(timezone.utc)
        await db.commit()

    if ws_broadcast:
        await ws_broadcast(campaign_id, {
            "type": "status",
            "data": {"status": campaign.status.value},
        })
