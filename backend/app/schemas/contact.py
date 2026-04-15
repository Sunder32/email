from datetime import datetime

from pydantic import BaseModel


class ContactRead(BaseModel):
    id: int
    campaign_id: int
    email: str
    is_valid: bool | None
    validation_error: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactUploadResponse(BaseModel):
    total: int
    parsed: int
    duplicates: int


class ValidationProgress(BaseModel):
    total: int
    checked: int
    valid: int
    invalid: int
    progress_percent: float
