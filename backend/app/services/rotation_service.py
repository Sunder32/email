from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_password
from app.models.domain import Domain
from app.models.mailbox import Mailbox


class MailboxSlot:
    def __init__(self, mailbox: Mailbox, domain: Domain, password: str):
        self.mailbox = mailbox
        self.domain = domain
        self.password = password

    @property
    def can_send(self) -> bool:
        mb = self.mailbox
        dm = self.domain
        return (
            mb.is_active
            and dm.is_active
            and mb.sent_this_hour < mb.hourly_limit
            and mb.sent_today < mb.daily_limit
            and dm.sent_this_hour < dm.hourly_limit
            and dm.sent_today < dm.daily_limit
        )

    def increment(self):
        self.mailbox.sent_this_hour += 1
        self.mailbox.sent_today += 1
        self.domain.sent_this_hour += 1
        self.domain.sent_today += 1


class RotationPool:
    def __init__(self, slots: list[MailboxSlot], rotate_every_n: int):
        self.slots = slots
        self.rotate_every_n = rotate_every_n
        self.current_index = 0
        self.sent_via_current = 0

    @property
    def is_empty(self) -> bool:
        return len(self.slots) == 0

    @property
    def current(self) -> MailboxSlot | None:
        if self.is_empty:
            return None
        return self.slots[self.current_index]

    def advance(self):
        self.sent_via_current += 1
        if self.sent_via_current >= self.rotate_every_n:
            self.sent_via_current = 0
            self.current_index = (self.current_index + 1) % len(self.slots)

    def evict_current(self):
        if self.is_empty:
            return
        self.slots.pop(self.current_index)
        self.sent_via_current = 0
        if self.slots:
            self.current_index = self.current_index % len(self.slots)

    def get_next_available(self) -> MailboxSlot | None:
        if self.is_empty:
            return None
        current = self.current
        if current and current.can_send:
            return current
        for _ in range(len(self.slots)):
            if not self.current.can_send:
                self.evict_current()
                if self.is_empty:
                    return None
            else:
                return self.current
        return None


async def build_rotation_pool(db: AsyncSession, rotate_every_n: int) -> RotationPool:
    result = await db.execute(
        select(Mailbox, Domain)
        .join(Domain, Mailbox.domain_id == Domain.id)
        .where(Mailbox.is_active == True, Domain.is_active == True)
        .order_by(Domain.id, Mailbox.id)
    )
    rows = result.all()

    slots = []
    for mailbox, domain in rows:
        password = decrypt_password(mailbox.password_encrypted)
        slot = MailboxSlot(mailbox=mailbox, domain=domain, password=password)
        if slot.can_send:
            slots.append(slot)

    return RotationPool(slots=slots, rotate_every_n=rotate_every_n)
