from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Domain(Base, TimestampMixin):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hourly_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    sent_this_hour: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    mailboxes = relationship("Mailbox", back_populates="domain", cascade="all, delete-orphan")
