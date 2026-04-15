from datetime import datetime

from pydantic import BaseModel


class VariationRead(BaseModel):
    id: int
    campaign_id: int
    subject_variant: str
    iceberg_variant: str
    times_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VariationUpdate(BaseModel):
    subject_variant: str | None = None
    iceberg_variant: str | None = None


class VariationGenerateRequest(BaseModel):
    count: int = 30
