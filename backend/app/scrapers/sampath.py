"""Sampath Bank: offers come from the JSON API behind the site's Nuxt front end.

`GET /api/card-promotions?category=<value>&page_number=<n>&size=<n>` returns
`{data: [...], page_number, size, total}` for one category.
"""

import html
import time
from datetime import date, datetime
from typing import Any

from app.core.config import LOCAL_TZ, local_today
from app.scrapers.base import BaseScraper, BlockedError, RawOffer, ScrapeResult
from app.services.extract import html_to_text, parse_card_types, parse_validity

API_URL = "https://www.sampath.lk/api/card-promotions"
OFFER_URL = "https://www.sampath.lk/sampath-cards/credit-card-offer/{id}"
PAGE_SIZE = 8  # what the site itself requests
MAX_PAGES = 25  # per category; a safety stop if `total` is ever wrong

# The site's category tabs (value -> label). Merchant-specific ones come first so an
# offer listed under several tabs keeps its most specific category.
CATEGORIES: dict[str, str] = {
    "hotels": "Hotels",
    "super_markets": "SuperMarkets",
    "online": "Online",
    "Electronics_and_Furniture": "Electronics & Furniture",
    "health_and_insurance": "Health and Insurance",
    "fashion": "Fashion",
    "dining": "Dining",
    "travel_and_leisure": "Travel and Leisure",
    "Premium_Offers": "Premium Offers",
    "wepay": "WePay",
    "VISA_Offers": "VISA Offers",
    "Mastercard_Offers": "Mastercard Offers",
    "Other": "Other",
}
_PERIOD_TITLES = {"promotion period", "promotional period"}


def parse_offer(record: dict[str, Any], today: date) -> RawOffer:
    merchant = _clean(record.get("company_name"))
    short_discount = _clean(record.get("short_discount"))
    cards = {
        _clean(c.get("title")).lower(): html_to_text(c.get("description"))
        for c in record.get("cards_new") or []
    }

    period = next((text for title, text in cards.items() if title in _PERIOD_TITLES), "")
    valid_from, valid_to = parse_validity(period, today)
    valid_to = valid_to or _epoch_date(record.get("expire_on"))

    details = html_to_text(record.get("promotion_details"))
    terms = html_to_text(record.get("terms_and_conditions"))
    description = "\n".join(
        part for part in [details, f"Terms and conditions\n{terms}" if terms else ""] if part
    )
    eligible = " ".join(
        [_clean(record.get("short_description")), cards.get("eligible card categories", "")]
    )

    return RawOffer(
        external_id=str(record["id"]),
        title=f"{short_discount} at {merchant}" if short_discount else merchant,
        merchant=merchant,
        source_url=OFFER_URL.format(id=record["id"]),
        description=description,
        discount_text=short_discount,
        bank_category=CATEGORIES.get(record.get("category") or "", record.get("category")),
        card_types=parse_card_types(eligible),
        valid_from=valid_from,
        valid_to=valid_to,
        image_url=record.get("image_url") or None,
    )


class SampathScraper(BaseScraper):
    code = "sampath"
    name = "Sampath Bank"
    source_url = "https://www.sampath.lk/sampath-cards/credit-card-offer?firstTab=Other"

    def scrape(self) -> ScrapeResult:
        today = local_today()
        offers: dict[str, RawOffer] = {}
        raw: dict[str, str] = {}
        for category in CATEGORIES:
            for record in self._fetch_category(category, raw):
                offer = parse_offer(record, today)
                offers.setdefault(offer.external_id or "", offer)
        if not offers:
            raise BlockedError("Sampath returned no offers in any category")
        return ScrapeResult(offers=list(offers.values()), raw=raw)

    def _fetch_category(self, category: str, raw: dict[str, str]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for page in range(1, MAX_PAGES + 1):
            time.sleep(self.delay_seconds)
            response = self.client.get(
                API_URL, params={"category": category, "page_number": page, "size": PAGE_SIZE}
            )
            response.raise_for_status()
            raw[f"{category}-{page}.json"] = response.text
            body = response.json()
            data, total = body.get("data") or [], int(body.get("total") or 0)
            if total and not data and not records:
                # The API reports offers but withholds them: it does this for
                # requests it treats as automated.
                raise BlockedError(f"Sampath withheld the {total} offers in '{category}'")
            records += data
            if not data or len(records) >= total:
                break
        return records


def _clean(value: Any) -> str:
    return " ".join(html.unescape(str(value or "")).split())


def _epoch_date(value: Any) -> date | None:
    try:
        return datetime.fromtimestamp(int(value) / 1000, LOCAL_TZ).date()
    except (TypeError, ValueError):
        return None
