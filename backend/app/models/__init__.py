from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class DiscountType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    INSTALLMENT = "installment"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    # The site answered but withheld its offers (e.g. bot protection).
    BLOCKED = "blocked"
    FAILED = "failed"


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    source_url: Mapped[str] = mapped_column(String(512))


class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = (UniqueConstraint("bank_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id"), index=True)
    # The bank's own ID for the offer; with bank_id it identifies the offer across scrapes.
    external_id: Mapped[str] = mapped_column(String(255))

    title: Mapped[str] = mapped_column(String(512))
    merchant: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    discount_value: Mapped[float | None]
    discount_type: Mapped[DiscountType | None] = mapped_column(String(16))
    card_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(String(32), index=True)
    bank_category: Mapped[str | None] = mapped_column(String(128))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    image_url: Mapped[str | None] = mapped_column(String(1024))
    source_url: Mapped[str] = mapped_column(String(1024))

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # False once the offer disappears from the bank's site; rows are never deleted.
    is_active: Mapped[bool] = mapped_column(default=True, index=True)

    bank: Mapped[Bank] = relationship(lazy="joined")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[RunStatus] = mapped_column(String(16), default=RunStatus.RUNNING)
    offers_found: Mapped[int] = mapped_column(default=0)
    offers_new: Mapped[int] = mapped_column(default=0)
    offers_closed: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(Text)
    # Where the raw HTML/JSON fetched by this run was saved.
    raw_path: Mapped[str | None] = mapped_column(String(1024))

    bank: Mapped[Bank] = relationship(lazy="joined")
