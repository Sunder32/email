from datetime import datetime

from pydantic import BaseModel, Field


class DomainCreate(BaseModel):
    name: str = Field(max_length=255)
    hourly_limit: int = 100
    daily_limit: int = 1000


class DomainUpdate(BaseModel):
    name: str | None = None
    hourly_limit: int | None = None
    daily_limit: int | None = None
    is_active: bool | None = None


class DomainRead(BaseModel):
    id: int
    name: str
    hourly_limit: int
    daily_limit: int
    sent_this_hour: int
    sent_today: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainWithMailboxes(DomainRead):
    mailboxes: list["MailboxRead"] = []


from app.schemas.mailbox import MailboxRead  # noqa: E402

DomainWithMailboxes.model_rebuild()
