import json
from datetime import date

import httpx
import pytest

from app.models import DiscountType
from app.scrapers.base import BlockedError
from app.scrapers.sampath import SampathScraper, parse_offer
from app.services.extract import parse_discount
from tests.conftest import FIXTURES

TODAY = date(2026, 10, 2)


def fixture(category: str) -> dict:
    path = FIXTURES / f"sampath_card_promotions_{category}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def record(category: str, record_id: int) -> dict:
    return next(r for r in fixture(category)["data"] if r["id"] == record_id)


def test_parse_offer_maps_the_api_fields() -> None:
    offer = parse_offer(record("dining", 3354), TODAY)

    assert offer.external_id == "3354"
    assert offer.merchant == "Hilton Colombo - Oktoberfest 2026"
    assert offer.title == "Up to 15% Discount at Hilton Colombo - Oktoberfest 2026"
    assert offer.discount_text == "Up to 15% Discount"
    assert offer.bank_category == "Dining"
    assert offer.card_types == ["Visa", "Credit"]
    # From the "Promotion Period" card: "29th October to 07th November 2026".
    assert (offer.valid_from, offer.valid_to) == (date(2026, 10, 29), date(2026, 11, 7))
    assert offer.source_url == "https://www.sampath.lk/sampath-cards/credit-card-offer/3354"
    assert offer.image_url and offer.image_url.startswith("https://www.sampath.lk/api/uploads/")
    assert offer.description.startswith("* 15% Discount is valid on Event Tickets")
    assert "\nTerms and conditions\n1. The offer will be valid" in offer.description


def test_parse_offer_cleans_merchant_whitespace() -> None:
    assert parse_offer(record("dining", 3056), TODAY).merchant == "Subway"


def test_parse_offer_reads_installment_plans() -> None:
    offer = parse_offer(record("online", 3163), TODAY)
    assert offer.discount_text == "06,12, 20 & 24 months 0% Instalment Plans"
    assert parse_discount(offer.discount_text) == (DiscountType.INSTALLMENT, 24)
    # No "Promotion Period" card: the end date comes from `expire_on`.
    assert offer.valid_to == date(2026, 12, 31)


def test_parse_offer_reads_single_day_offers() -> None:
    offer = parse_offer(record("super_markets", 3289), TODAY)
    assert (offer.valid_from, offer.valid_to) == (date(2026, 10, 26), date(2026, 10, 26))


def _api(responses: dict[str, dict]) -> httpx.Client:
    """Serves `responses[f"{category}-{page}"]`, and empty pages for anything else."""

    def handler(request: httpx.Request) -> httpx.Response:
        key = f"{request.url.params['category']}-{request.url.params['page_number']}"
        body = responses.get(key, {"data": [], "page_number": 1, "size": 8, "total": 0})
        return httpx.Response(200, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_scraper_pages_through_categories_and_dedupes() -> None:
    dining = fixture("dining")  # 8 of 12 on page 1
    page_two = [{**r, "id": r["id"] + 100000} for r in dining["data"][:4]]
    client = _api(
        {
            "dining-1": dining,
            "dining-2": {**dining, "data": page_two, "page_number": 2},
            "super_markets-1": fixture("super_markets"),
            # The same offers again under a generic tab.
            "VISA_Offers-1": fixture("super_markets"),
        }
    )

    result = SampathScraper(client).scrape()

    assert len(result.offers) == 12 + 5
    keells = next(o for o in result.offers if o.external_id == "3287")
    assert keells.bank_category == "SuperMarkets"  # the specific tab wins
    assert {"dining-1.json", "dining-2.json", "super_markets-1.json"} <= set(result.raw)


def test_scraper_reports_withheld_offers_as_blocked() -> None:
    client = _api({"hotels-1": {"data": [], "page_number": 1, "size": 8, "total": 46}})
    with pytest.raises(BlockedError, match="withheld the 46 offers in 'hotels'"):
        SampathScraper(client).scrape()


def test_scraper_reports_no_offers_at_all_as_blocked() -> None:
    with pytest.raises(BlockedError):
        SampathScraper(_api({})).scrape()
