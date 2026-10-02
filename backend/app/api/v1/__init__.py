from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings, local_today
from app.db import get_session, get_session_factory
from app.models import Bank, Promotion, ScrapeRun
from app.schemas import (
    BankOut,
    CategoryCount,
    PromotionOut,
    PromotionPage,
    PromotionStatus,
    ScrapeRequest,
    ScrapeRunOut,
    ScrapeStarted,
    SortOrder,
)
from app.scrapers.registry import SCRAPERS
from app.services.classifier import CATEGORIES
from app.services.promotions import count_categories, list_promotions
from app.services.scrape import run_scrape

router = APIRouter(prefix="/api/v1")

SessionDep = Annotated[Session, Depends(get_session)]
CategorySlug = Annotated[str | None, Query(pattern=f"^({'|'.join(CATEGORIES)})$")]


# Largest id Postgres' INTEGER holds; anything else can't be a promotion.
_MAX_ID = 2**31 - 1


@router.get("/promotions", response_model=PromotionPage, tags=["promotions"])
def get_promotions(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    bank: str | None = None,
    category: CategorySlug = None,
    status: PromotionStatus | None = None,
    sort: SortOrder = "newest",
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 12,
) -> PromotionPage:
    """Promotions, filtered and sorted. Leaving out `status` returns every status."""
    items, total = list_promotions(
        session,
        today=local_today(),
        q=q,
        bank=bank,
        category=category,
        status=status,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return PromotionPage(
        items=[PromotionOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/promotions/{promotion_id}", response_model=PromotionOut, tags=["promotions"])
def get_promotion(promotion_id: str, session: SessionDep) -> PromotionOut:
    # Any malformed id is simply "not found", which is what the website handles.
    valid = promotion_id.isdigit() and int(promotion_id) <= _MAX_ID
    promotion = session.get(Promotion, int(promotion_id)) if valid else None
    if promotion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promotion not found")
    return PromotionOut.model_validate(promotion)


@router.get("/categories", response_model=list[CategoryCount], tags=["promotions"])
def get_categories(
    session: SessionDep, status: PromotionStatus | None = None
) -> list[CategoryCount]:
    """Every category with its number of offers (for `status`, or all statuses)."""
    counts = count_categories(session, today=local_today(), status=status)
    return [CategoryCount(slug=slug, label=label, count=count) for slug, label, count in counts]


@router.get("/banks", response_model=list[BankOut], tags=["banks"])
def get_banks(session: SessionDep) -> list[Bank]:
    return list(session.scalars(select(Bank).order_by(Bank.name)))


@router.get("/scrape-runs", response_model=list[ScrapeRunOut], tags=["scrape runs"])
def get_scrape_runs(
    session: SessionDep, limit: Annotated[int, Query(ge=1, le=200)] = 20
) -> list[ScrapeRunOut]:
    """Recent scrape runs, newest first: shows whether scraping is healthy."""
    runs = session.scalars(select(ScrapeRun).order_by(ScrapeRun.id.desc()).limit(limit))
    return [ScrapeRunOut.model_validate(run) for run in runs]


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.admin_token:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Manual scrapes are disabled; set ADMIN_TOKEN"
        )
    if x_admin_token != settings.admin_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or wrong X-Admin-Token header")


@router.post(
    "/scrape-runs",
    response_model=ScrapeStarted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_admin)],
    tags=["scrape runs"],
)
def start_scrape(
    background: BackgroundTasks,
    session_factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    settings: Annotated[Settings, Depends(get_settings)],
    body: ScrapeRequest | None = None,
) -> ScrapeStarted:
    """Starts a scrape now (admin). Results appear in `GET /scrape-runs`."""
    banks = [body.bank] if body and body.bank else list(SCRAPERS)
    if unknown := [code for code in banks if code not in SCRAPERS]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown bank: {', '.join(unknown)}")
    for code in banks:
        background.add_task(run_scrape, code, session_factory, settings)
    return ScrapeStarted(banks=banks)
