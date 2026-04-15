from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TextVariation(Base, TimestampMixin):
    __tablename__ = "text_variations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    subject_variant: Mapped[str] = mapped_column(String(500), nullable=False)
    iceberg_variant: Mapped[str] = mapped_column(Text, nullable=False)
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    campaign = relationship("Campaign", back_populates="variations")
