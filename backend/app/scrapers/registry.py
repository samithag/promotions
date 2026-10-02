"""Every bank the scraper tracks. Adding a bank means one scraper module and one line here."""

from app.scrapers.base import BaseScraper
from app.scrapers.combank import ComBankScraper
from app.scrapers.sampath import SampathScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    scraper.code: scraper for scraper in [ComBankScraper, SampathScraper]
}
