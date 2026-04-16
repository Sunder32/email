import enum

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    VALIDATING = "validating"
    GENERATING = "generating"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    original_body: Mapped[str] = mapped_column(Text, nullable=False)
    total_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False
    )
    rotate_every_n: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    delay_min_sec: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    delay_max_sec: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    skip_validation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contacts = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
    variations = relationship("TextVariation", back_populates="campaign", cascade="all, delete-orphan")
    send_logs = relationship("SendLog", back_populates="campaign", cascade="all, delete-orphan")
