from datetime import datetime

from pydantic import BaseModel, Field


class MailboxCreate(BaseModel):
    email: str = Field(max_length=255)
    smtp_host: str = Field(max_length=255)
    smtp_port: int = 587
    login: str = Field(max_length=255)
    password: str = Field(max_length=255)
    use_tls: bool = True
    hourly_limit: int = 50
    daily_limit: int = 500


class MailboxUpdate(BaseModel):
    email: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    login: str | None = None
    password: str | None = None
    use_tls: bool | None = None
    hourly_limit: int | None = None
    daily_limit: int | None = None
    is_active: bool | None = None


class MailboxRead(BaseModel):
    id: int
    domain_id: int
    email: str
    smtp_host: str
    smtp_port: int
    login: str
    use_tls: bool
    hourly_limit: int
    daily_limit: int
    sent_this_hour: int
    sent_today: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MailboxTestResult(BaseModel):
    success: bool
    message: str
