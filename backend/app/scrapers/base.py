from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

import httpx


@dataclass(frozen=True)
class RawOffer:
    """An offer as read from a bank's site, before classification and storage."""

    title: str
    merchant: str
    source_url: str
    # The bank's own ID; when missing, ingest falls back to a content hash.
    external_id: str | None = None
    description: str = ""
    # Free text the discount is extracted from, e.g. "Up to 20% Off".
    discount_text: str = ""
    bank_category: str | None = None
    card_types: list[str] = field(default_factory=list)
    valid_from: date | None = None
    valid_to: date | None = None
    image_url: str | None = None


@dataclass
class ScrapeResult:
    offers: list[RawOffer]
    # Raw responses keyed by a short name, saved for debugging and re-parsing.
    raw: dict[str, str]


class BlockedError(Exception):
    """The site responded but withheld its offers, e.g. because of bot protection.

    Raised instead of returning an empty list, so a blocked run never marks every
    offer as gone.
    """


class BaseScraper(ABC):
    code: str
    name: str
    source_url: str

    def __init__(self, client: httpx.Client, delay_seconds: float = 0.0):
        self.client = client
        self.delay_seconds = delay_seconds

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        """Fetch the bank's offers and parse them."""
