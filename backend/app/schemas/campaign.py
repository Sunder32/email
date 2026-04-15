from datetime import datetime

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str = Field(max_length=255)
    original_subject: str = Field(max_length=500)
    original_body: str
    rotate_every_n: int = 5
    delay_min_sec: float = 5.0
    delay_max_sec: float = 30.0


class CampaignUpdate(BaseModel):
    name: str | None = None
    original_subject: str | None = None
    original_body: str | None = None
    rotate_every_n: int | None = None
    delay_min_sec: float | None = None
    delay_max_sec: float | None = None


class CampaignRead(BaseModel):
    id: int
    name: str
    original_subject: str
    original_body: str
    total_contacts: int
    valid_contacts: int
    sent_count: int
    failed_count: int
    status: str
    rotate_every_n: int
    delay_min_sec: float
    delay_max_sec: float
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignStats(BaseModel):
    total_contacts: int
    valid_contacts: int
    sent_count: int
    failed_count: int
    remaining: int
    progress_percent: float
    elapsed_seconds: float | None
    eta_seconds: float | None
