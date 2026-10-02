"""Commercial Bank (ComBank): offers are server-rendered HTML.

The listing page has one `a.reward` card per offer (discount tag, category, title,
validity line). Each card links to a detail page with the full terms.
"""

import re
import time
from dataclasses import replace
from datetime import date

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import LOCAL_TZ
from app.models import utcnow
from app.scrapers.base import BaseScraper, BlockedError, RawOffer, ScrapeResult
from app.services.extract import html_to_text, parse_card_types, parse_validity

LISTING_URL = "https://www.combank.lk/rewards-promotions"
_DETAIL_PREFIX = "/rewards-promotion/"
GENERIC_MERCHANT = "Selected merchants"

# Everything from "with ComBank Credit Cards" (or a partner card scheme) onwards.
_CARD_TAIL = re.compile(r"\s+(?:with|using|and)\s+(?:ComBank|LankaPay)\b.*$", re.I)
_BEFORE_MERCHANT = re.compile(r"\b(?:at|via|with|from|to|in)\s+", re.I)
_FILLER = re.compile(r"^(?:your\s+favourite\s+|savings\s+on\s+|the\s+)+", re.I)
_BACKGROUND_URL = re.compile(r"url\(['\"]?([^'\")]+)")


def merchant_from_title(title: str) -> str:
    """Guesses the merchant from a title such as "Enjoy the art of dining at Courtyard
    by Marriott Colombo with ComBank Credit Cards". ComBank doesn't list it separately.
    """
    text = _CARD_TAIL.sub("", title).strip()
    # Try the last "at/via/with/..." first: "at your favourite restaurants with Foody.lk".
    for match in reversed(list(_BEFORE_MERCHANT.finditer(text))):
        candidate = text[match.end() :]
        if candidate.lower().startswith("selected "):
            continue
        candidate = _FILLER.sub("", candidate).strip(" .,")
        # A real name is capitalised ("Keells") or a web address ("tudo.lk").
        if candidate and (candidate[0].isupper() or "." in candidate):
            return candidate
    return GENERIC_MERCHANT


def parse_listing(html: str, today: date) -> list[RawOffer]:
    soup = BeautifulSoup(html, "lxml")
    offers: dict[str, RawOffer] = {}
    for card in soup.select("a.reward[href]"):
        href = card["href"]
        if _DETAIL_PREFIX not in href or href in offers:
            continue
        title = _text(card.h3)
        valid_from, valid_to = parse_validity(_text(card.select_one("p.valid-date")), today)
        offers[href] = RawOffer(
            external_id=href.split(_DETAIL_PREFIX, 1)[1].strip("/"),
            title=title,
            merchant=merchant_from_title(title),
            source_url=href,
            discount_text=" ".join(_text(p) for p in card.select(".offer-tag p")),
            bank_category=_text(card.select_one("p.category")) or None,
            card_types=parse_card_types(title),
            valid_from=valid_from,
            valid_to=valid_to,
            image_url=_background_image(card.select_one(".reward-image")),
        )
    return list(offers.values())


def parse_detail(html: str) -> str:
    """The offer's full description and terms, as plain text."""
    content = BeautifulSoup(html, "lxml").select_one("section.reward-content")
    text = html_to_text(str(content)) if content else ""
    return re.sub(r"^Offer terms and conditions\s*", "", text)


class ComBankScraper(BaseScraper):
    code = "combank"
    name = "Commercial Bank"
    source_url = LISTING_URL

    def scrape(self) -> ScrapeResult:
        today = utcnow().astimezone(LOCAL_TZ).date()
        response = self.client.get(LISTING_URL)
        response.raise_for_status()
        offers = parse_listing(response.text, today)
        if not offers:
            raise BlockedError("No offers found on the ComBank listing page")
        return ScrapeResult(
            offers=[self._with_details(offer, today) for offer in offers],
            raw={"listing.html": response.text},
        )

    def _with_details(self, offer: RawOffer, today: date) -> RawOffer:
        """Adds the detail page's terms; keeps the listing data if that page fails."""
        time.sleep(self.delay_seconds)
        try:
            response = self.client.get(offer.source_url)
            response.raise_for_status()
        except httpx.HTTPError:
            return offer
        description = parse_detail(response.text)
        if not description:
            return offer
        # The terms often state the start date ("applicable from 01st to 31st October").
        detail_from, detail_to = parse_validity(description, today)
        return replace(
            offer,
            description=description,
            valid_from=offer.valid_from or detail_from,
            valid_to=offer.valid_to or detail_to,
        )


def _text(node: Tag | None) -> str:
    return " ".join(node.get_text(" ").split()) if node else ""


def _background_image(node: Tag | None) -> str | None:
    match = _BACKGROUND_URL.search(str(node.get("style", ""))) if node else None
    return match[1] if match else None
