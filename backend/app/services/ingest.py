"""Turns scraped offers into stored promotions: classify, dedupe, upsert, close."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bank, Promotion
from app.scrapers.base import RawOffer
from app.services.classifier import classify
from app.services.extract import parse_discount


@dataclass(frozen=True)
class IngestStats:
    found: int
    new: int
    closed: int


def ingest(session: Session, bank: Bank, offers: list[RawOffer], now: datetime) -> IngestStats:
    """Upserts one complete scrape of a bank's offers.

    New offers are inserted; offers seen before are updated and stay active; active
    offers missing from this scrape are marked inactive (kept for history). The
    caller commits.
    """
    stored = {
        promotion.external_id: promotion
        for promotion in session.scalars(select(Promotion).where(Promotion.bank_id == bank.id))
    }
    seen: set[str] = set()
    new = 0

    for offer in offers:
        if offer.external_id in seen:
            continue
        seen.add(offer.external_id)

        promotion = stored.get(offer.external_id)
        if promotion is None:
            promotion = Promotion(bank_id=bank.id, external_id=offer.external_id, first_seen_at=now)
            session.add(promotion)
            new += 1
        _apply(promotion, offer)
        promotion.last_seen_at = now
        promotion.is_active = True

    closed = 0
    for external_id, promotion in stored.items():
        if promotion.is_active and external_id not in seen:
            promotion.is_active = False
            closed += 1

    return IngestStats(found=len(seen), new=new, closed=closed)


def _apply(promotion: Promotion, offer: RawOffer) -> None:
    discount_type, discount_value = parse_discount(offer.discount_text or offer.title)
    promotion.title = offer.title
    promotion.merchant = offer.merchant
    promotion.description = offer.description
    promotion.discount_type = discount_type
    promotion.discount_value = discount_value
    promotion.card_types = offer.card_types
    promotion.category = classify(offer.bank_category, f"{offer.title} {offer.merchant}")
    promotion.bank_category = offer.bank_category
    promotion.valid_from = offer.valid_from
    promotion.valid_to = offer.valid_to
    promotion.image_url = offer.image_url
    promotion.source_url = offer.source_url
