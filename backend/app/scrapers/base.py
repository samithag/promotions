import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx


@dataclass(frozen=True)
class RawOffer:
    """An offer as read from a bank's site, before classification and storage."""

    # The bank's own stable ID for the offer (Sampath's record ID, ComBank's URL slug).
    external_id: str
    title: str
    merchant: str
    source_url: str
    description: str = ""
    # Free text the discount is extracted from, e.g. "Up to 20% Off".
    discount_text: str = ""
    bank_category: str | None = None
    card_types: list[str] = field(default_factory=list)
    valid_from: date | None = None
    valid_to: date | None = None
    image_url: str | None = None


@dataclass(frozen=True)
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
        self._robots: dict[str, tuple[RobotFileParser, int | None]] = {}

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        """Fetch the bank's offers and parse them."""

    def _get(self, url: str, **params: str | int) -> httpx.Response:
        """A polite GET: obeys robots.txt, pauses between requests, raises on HTTP errors."""
        if reason := self._disallowed(url):
            raise BlockedError(reason)
        time.sleep(self.delay_seconds)
        response = self.client.get(url, params=params or None)
        response.raise_for_status()
        return response

    def _disallowed(self, url: str) -> str | None:
        """Why robots.txt forbids `url`, or None if it's allowed. Fetched once per site."""
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(url))
        if origin not in self._robots:
            self._robots[origin] = self._load_robots(origin)
        parser, refused = self._robots[origin]
        if parser.can_fetch(self.client.headers.get("user-agent", "*"), url):
            return None
        if refused:
            # Standard robots.txt handling: a 401/403 means the whole site is off limits.
            return f"{origin}/robots.txt answered HTTP {refused}, so the whole site is off limits"
        return f"robots.txt disallows {url}"

    def _load_robots(self, origin: str) -> tuple[RobotFileParser, int | None]:
        """The parsed robots.txt, plus the HTTP status if the site refused to serve it."""
        parser = RobotFileParser()
        try:
            response = self.client.get(f"{origin}/robots.txt")
        except httpx.HTTPError:
            response = None
        if response is not None and response.status_code == 200:
            parser.parse(response.text.splitlines())
        elif response is not None and response.status_code in (401, 403):
            parser.disallow_all = True
            return parser, response.status_code
        else:  # no robots.txt (or it can't be read): everything is allowed
            parser.allow_all = True
        return parser, None
