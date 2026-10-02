from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bank, DiscountType, Promotion
from app.scrapers.base import RawOffer
from app.services.banks import sync_banks
from app.services.ingest import ingest

NOW = datetime(2026, 10, 2, 6, 0, tzinfo=UTC)


def offer(external_id: str | None = "a", **overrides) -> RawOffer:
    values = {
        "external_id": external_id,
        "title": "Enjoy 20% off at Keells",
        "merchant": "Keells",
        "source_url": "https://bank.example/offer",
        "discount_text": "Up to 20% Off",
        "bank_category": "Supermarket",
        "valid_to": date(2026, 10, 31),
    }
    return RawOffer(**{**values, **overrides})


def bank(session: Session) -> Bank:
    sync_banks(session)
    return session.scalars(select(Bank).where(Bank.code == "combank")).one()


def promotions(session: Session) -> dict[str, Promotion]:
    return {p.external_id: p for p in session.scalars(select(Promotion))}


def test_inserts_new_offers_with_derived_fields(session: Session) -> None:
    stats = ingest(session, bank(session), [offer()], NOW)
    session.commit()

    assert (stats.found, stats.new, stats.closed) == (1, 1, 0)
    stored = promotions(session)["a"]
    assert stored.category == "supermarket"
    assert (stored.discount_type, stored.discount_value) == (DiscountType.PERCENTAGE, 20)
    assert stored.first_seen_at == stored.last_seen_at
    assert stored.is_active


def test_updates_existing_offers_instead_of_duplicating(session: Session) -> None:
    combank = bank(session)
    ingest(session, combank, [offer()], NOW)
    session.commit()
    later = NOW + timedelta(hours=1)
    stats = ingest(session, combank, [offer(title="Enjoy 25% off at Keells")], later)
    session.commit()

    assert (stats.found, stats.new) == (1, 0)
    stored = promotions(session)["a"]
    assert stored.title == "Enjoy 25% off at Keells"
    assert stored.last_seen_at.replace(tzinfo=UTC) == later
    assert stored.first_seen_at.replace(tzinfo=UTC) == NOW


def test_closes_offers_that_disappear_and_reopens_them_if_they_return(session: Session) -> None:
    combank = bank(session)
    ingest(session, combank, [offer("a"), offer("b")], NOW)
    stats = ingest(session, combank, [offer("a")], NOW)
    assert stats.closed == 1
    assert not promotions(session)["b"].is_active

    ingest(session, combank, [offer("a"), offer("b")], NOW)
    assert promotions(session)["b"].is_active


def test_falls_back_to_a_content_hash_and_dedupes_within_a_scrape(session: Session) -> None:
    stats = ingest(session, bank(session), [offer(None), offer(None)], NOW)
    assert (stats.found, stats.new) == (1, 1)
    (stored,) = promotions(session).values()
    assert stored.external_id == stored.content_hash
