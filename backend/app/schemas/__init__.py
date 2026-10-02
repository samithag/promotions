"""Response models. These follow the "Frontend contract" in doc/webscraper_plan.md."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import DiscountType, RunStatus

PromotionStatus = Literal["active", "upcoming", "expired"]
SortOrder = Literal["newest", "ending_soon", "discount"]


class _FromBankRow(BaseModel):
    """Reads ORM rows; `bank` is the bank's code rather than the related row."""

    model_config = ConfigDict(from_attributes=True)

    bank: str = Field(description="Bank code, e.g. `combank`")

    @field_validator("bank", mode="before")
    @classmethod
    def _bank_code(cls, value: Any) -> Any:
        return getattr(value, "code", value)


class PromotionOut(_FromBankRow):
    id: str
    title: str
    merchant: str
    description: str
    discount_value: float | None = Field(
        description="Percent, rupees, or installment months, depending on `discount_type`"
    )
    discount_type: DiscountType | None
    card_types: list[str]
    category: str
    bank_category: str | None
    valid_from: date | None
    valid_to: date | None
    image_url: str | None
    source_url: str
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool

    @field_validator("id", mode="before")
    @classmethod
    def _id_as_string(cls, value: Any) -> str:
        return str(value)


class PromotionPage(BaseModel):
    items: list[PromotionOut]
    total: int
    page: int
    page_size: int


class CategoryCount(BaseModel):
    slug: str
    label: str
    count: int


class BankOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    source_url: str


class ScrapeRunOut(_FromBankRow):
    id: int
    started_at: datetime
    finished_at: datetime | None
    status: RunStatus
    offers_found: int
    offers_new: int
    offers_closed: int
    error: str | None


class ScrapeRequest(BaseModel):
    bank: str | None = Field(default=None, description="Bank code; every bank when left out")


class ScrapeStarted(BaseModel):
    banks: list[str]
