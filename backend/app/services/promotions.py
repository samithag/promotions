"""Promotion queries for the read API.

Status, filtering and sorting match the frontend's mock repository
(frontend/src/lib/promotions), so the site behaves the same on live data.
"""

from datetime import date

from sqlalchemy import ColumnElement, Select, and_, case, func, not_, or_, select
from sqlalchemy.orm import Session

from app.models import Bank, DiscountType, Promotion
from app.schemas import PromotionStatus, SortOrder
from app.services.classifier import CATEGORIES


def status_condition(status: PromotionStatus, today: date) -> ColumnElement[bool]:
    """SQL for a derived status. Offers the scraper no longer sees count as expired.

    NULL dates mean "no limit", and are spelled out: in SQL `NOT (NULL < x)` is NULL,
    not true.
    """
    not_ended = or_(Promotion.valid_to.is_(None), Promotion.valid_to >= today)
    started = or_(Promotion.valid_from.is_(None), Promotion.valid_from <= today)
    if status == "expired":
        return or_(not_(Promotion.is_active), Promotion.valid_to < today)
    if status == "upcoming":
        return and_(Promotion.is_active, not_ended, Promotion.valid_from > today)
    return and_(Promotion.is_active, not_ended, started)


_DISCOUNT_GROUP = case(
    (Promotion.discount_type == DiscountType.PERCENTAGE, 0),
    (Promotion.discount_type == DiscountType.FIXED, 1),
    (Promotion.discount_type == DiscountType.INSTALLMENT, 2),
    else_=3,
)

_ORDER_BY = {
    "newest": [Promotion.first_seen_at.desc()],
    # Open-ended offers have no deadline, so they sort last.
    "ending_soon": [Promotion.valid_to.is_(None), Promotion.valid_to.asc()],
    # Percentages first (largest first), then rupee amounts, then installment plans.
    "discount": [_DISCOUNT_GROUP, func.coalesce(Promotion.discount_value, 0).desc()],
}


def list_promotions(
    session: Session,
    *,
    today: date,
    q: str | None = None,
    bank: str | None = None,
    category: str | None = None,
    status: PromotionStatus | None = None,
    sort: SortOrder = "newest",
    page: int = 1,
    page_size: int = 12,
) -> tuple[list[Promotion], int]:
    query: Select[tuple[Promotion]] = select(Promotion).join(Promotion.bank)
    if q:
        query = query.where(
            or_(
                Promotion.title.icontains(q, autoescape=True),
                Promotion.merchant.icontains(q, autoescape=True),
                Promotion.description.icontains(q, autoescape=True),
            )
        )
    if bank:
        query = query.where(Bank.code == bank)
    if category:
        query = query.where(Promotion.category == category)
    if status:
        query = query.where(status_condition(status, today))

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(
        query.order_by(*_ORDER_BY[sort], Promotion.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def count_categories(
    session: Session, *, today: date, status: PromotionStatus | None = None
) -> list[tuple[str, str, int]]:
    """(slug, label, count) for every category, including empty ones."""
    query = select(Promotion.category, func.count()).group_by(Promotion.category)
    if status:
        query = query.where(status_condition(status, today))
    counts = {slug: count for slug, count in session.execute(query)}
    return [(slug, label, counts.get(slug, 0)) for slug, label in CATEGORIES.items()]
