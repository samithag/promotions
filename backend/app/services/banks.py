from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bank
from app.scrapers.registry import SCRAPERS


def sync_banks(session: Session) -> None:
    """Makes the banks table match the scraper registry (inserting or renaming rows)."""
    existing = {bank.code: bank for bank in session.scalars(select(Bank))}
    for code, scraper in SCRAPERS.items():
        bank = existing.get(code) or Bank(code=code)
        bank.name = scraper.name
        bank.source_url = scraper.source_url
        session.add(bank)
    session.commit()
