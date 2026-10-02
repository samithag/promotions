"""Response models. These follow the "Frontend contract" in doc/webscraper_plan.md."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import DiscountType, RunStatus

PromotionStatus = Literal["active", "upcoming", "expired"]
SortOrder = Literal["newest", "ending_soon", "discount"]


class PromotionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bank: str = Field(description="Bank code, e.g. `combank`")
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


class ScrapeRunOut(BaseModel):
    id: int
    bank: str
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
