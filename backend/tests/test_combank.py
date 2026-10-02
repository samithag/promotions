from datetime import date

import httpx
import pytest

from app.scrapers.base import BlockedError
from app.scrapers.combank import (
    GENERIC_MERCHANT,
    LISTING_URL,
    ComBankScraper,
    merchant_from_title,
    parse_detail,
    parse_listing,
)
from tests.conftest import FIXTURES

TODAY = date(2026, 10, 2)
LISTING = (FIXTURES / "combank_rewards_promotions.html").read_text(encoding="utf-8")
DETAIL = (FIXTURES / "combank_promotion_detail.html").read_text(encoding="utf-8")
COURTYARD_SLUG = (
    "food-restaurants/"
    "enjoy-the-art-of-dining-at-courtyard-by-marriott-colombo-with-combank-credit-cards"
)


def test_parse_listing_reads_every_offer() -> None:
    offers = parse_listing(LISTING, TODAY)
    assert len(offers) == 42
    assert len({offer.external_id for offer in offers}) == 42


def test_parse_listing_reads_card_fields() -> None:
    offer = next(o for o in parse_listing(LISTING, TODAY) if o.external_id == COURTYARD_SLUG)
    assert offer.title == (
        "Enjoy the art of dining at Courtyard by Marriott Colombo with ComBank Credit Cards"
    )
    assert offer.merchant == "Courtyard by Marriott Colombo"
    assert offer.discount_text == "Up to 10% Off"
    assert offer.bank_category == "Food & Restaurants"
    assert offer.card_types == ["Credit"]
    assert offer.valid_to == date(2026, 10, 31)
    assert offer.source_url == f"https://www.combank.lk/rewards-promotion/{COURTYARD_SLUG}"
    assert offer.image_url and offer.image_url.endswith(
        "Courtyard-by-Marriott-Colombo-Oct-thumb.jpg"
    )


@pytest.mark.parametrize(
    ("title", "merchant"),
    [
        (
            "Enjoy the art of dining at Galle Face Hotel with ComBank Credit Cards",
            "Galle Face Hotel",
        ),
        (
            "Enjoy the art of dining at your favourite restaurants with Foody.lk and ComBank Cards",
            "Foody.lk",
        ),
        (
            "Enjoy the art of dining at your favourite Softlogic Restaurants with ComBank Cards",
            "Softlogic Restaurants",
        ),
        ("Great online deals with tudo.lk using ComBank Credit and Debit Cards", "tudo.lk"),
        (
            "Fuel your journey with savings on Mobil Engine Oil with ComBank Cards",
            "Mobil Engine Oil",
        ),
        ("Embark on a journey to Japan with ComBank Visa Cards", "Japan"),
        (
            "Enjoy the art of dining at your favourite restaurant with ComBank Cards",
            GENERIC_MERCHANT,
        ),
        ("Get 10% Cashback at selected Supermarkets with LankaPay JCB Cards", GENERIC_MERCHANT),
        ("Transact More and Win Big with ComBank Digital", GENERIC_MERCHANT),
    ],
)
def test_merchant_from_title(title: str, merchant: str) -> None:
    assert merchant_from_title(title) == merchant


def test_parse_detail_returns_terms_text() -> None:
    text = parse_detail(DETAIL)
    assert text.startswith("Offer –10% discount for Credit Cards")
    assert "Offer applicable from 01st to 31st October 2026." in text.splitlines()


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_scraper_adds_detail_pages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == LISTING_URL:
            return httpx.Response(200, text=LISTING)
        if COURTYARD_SLUG in str(request.url):
            return httpx.Response(200, text=DETAIL)
        return httpx.Response(404)

    result = ComBankScraper(_client(handler)).scrape()

    assert len(result.offers) == 42
    assert set(result.raw) == {"listing.html"}
    courtyard = next(o for o in result.offers if o.external_id == COURTYARD_SLUG)
    # The detail page supplies the terms and the start date.
    assert courtyard.description.startswith("Offer –10% discount")
    assert courtyard.valid_from == date(2026, 10, 1)
    # A missing detail page leaves the listing data in place.
    other = next(o for o in result.offers if o.external_id != COURTYARD_SLUG)
    assert other.description == ""


def test_scraper_treats_an_empty_listing_as_blocked() -> None:
    client = _client(lambda request: httpx.Response(200, text="<html><body>Busy</body></html>"))
    with pytest.raises(BlockedError):
        ComBankScraper(client).scrape()


def test_scraper_obeys_robots_txt() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /rewards-promotions\n")
        return httpx.Response(200, text=LISTING)

    with pytest.raises(BlockedError, match="robots.txt disallows"):
        ComBankScraper(_client(handler)).scrape()


def test_scraper_fetches_robots_txt_once_per_site() -> None:
    robots_requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            robots_requests.append(str(request.url))
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if str(request.url) == LISTING_URL:
            return httpx.Response(200, text=LISTING)
        return httpx.Response(404)

    assert len(ComBankScraper(_client(handler)).scrape().offers) == 42
    assert robots_requests == ["https://www.combank.lk/robots.txt"]


def test_scraper_treats_a_refused_robots_txt_as_blocking_the_site() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(403)
        return httpx.Response(200, text=LISTING)

    with pytest.raises(BlockedError, match="robots.txt answered HTTP 403"):
        ComBankScraper(_client(handler)).scrape()
