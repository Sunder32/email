from datetime import datetime

from pydantic import BaseModel


class SendLogRead(BaseModel):
    id: int
    campaign_id: int
    contact_id: int
    mailbox_id: int | None
    subject_used: str
    body_preview: str | None
    status: str
    error_message: str | None
    sent_at: datetime

    model_config = {"from_attributes": True}


class SendLogFilter(BaseModel):
    mailbox_id: int | None = None
    status: str | None = None
