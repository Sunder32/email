from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_password, encrypt_password
from app.models.mailbox import Mailbox
from app.schemas.mailbox import MailboxCreate, MailboxRead, MailboxTestResult, MailboxUpdate
from app.services.smtp_service import test_smtp_connection


async def create_mailbox(db: AsyncSession, domain_id: int, data: MailboxCreate) -> MailboxRead:
    mailbox = Mailbox(
        domain_id=domain_id,
        email=data.email,
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        login=data.login,
        password_encrypted=encrypt_password(data.password),
        use_tls=data.use_tls,
        hourly_limit=data.hourly_limit,
        daily_limit=data.daily_limit,
    )
    db.add(mailbox)
    await db.commit()
    await db.refresh(mailbox)
    return MailboxRead.model_validate(mailbox)


async def get_mailbox(db: AsyncSession, mailbox_id: int) -> Mailbox:
    result = await db.execute(select(Mailbox).where(Mailbox.id == mailbox_id))
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        raise ValueError("Mailbox not found")
    return mailbox


async def update_mailbox(db: AsyncSession, mailbox_id: int, data: MailboxUpdate) -> MailboxRead:
    mailbox = await get_mailbox(db, mailbox_id)
    updates = data.model_dump(exclude_unset=True)
    if "password" in updates:
        updates["password_encrypted"] = encrypt_password(updates.pop("password"))
    for key, value in updates.items():
        setattr(mailbox, key, value)
    await db.commit()
    await db.refresh(mailbox)
    return MailboxRead.model_validate(mailbox)


async def delete_mailbox(db: AsyncSession, mailbox_id: int) -> None:
    mailbox = await get_mailbox(db, mailbox_id)
    await db.delete(mailbox)
    await db.commit()


async def test_mailbox(db: AsyncSession, mailbox_id: int) -> MailboxTestResult:
    mailbox = await get_mailbox(db, mailbox_id)
    password = decrypt_password(mailbox.password_encrypted)
    success, message = test_smtp_connection(
        host=mailbox.smtp_host,
        port=mailbox.smtp_port,
        login=mailbox.login,
        password=password,
        use_tls=mailbox.use_tls,
    )
    return MailboxTestResult(success=success, message=message)
