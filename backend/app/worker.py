"""Scrape worker: scrapes every bank on a schedule. Run with `python -m app.worker`.

It runs as its own process, not inside the API: each API worker process would
otherwise start its own scheduler and scrape the same pages several times.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import LOCAL_TZ, get_settings
from app.db import get_sessionmaker
from app.scrapers.registry import SCRAPERS
from app.services.banks import sync_banks
from app.services.scrape import fail_interrupted_runs, run_scrape


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = get_settings()
    session_factory = get_sessionmaker()
    with session_factory() as session:
        sync_banks(session)
        fail_interrupted_runs(session)

    scheduler = BlockingScheduler(timezone=LOCAL_TZ)
    for code in SCRAPERS:
        # One job per bank, so one site failing doesn't hold up the other.
        scheduler.add_job(
            run_scrape,
            "interval",
            args=[code, session_factory, settings],
            minutes=settings.scrape_interval_minutes,
            next_run_time=datetime.now(LOCAL_TZ),  # scrape once at startup
            id=f"scrape-{code}",
            max_instances=1,
            coalesce=True,
        )
    logging.getLogger(__name__).info(
        "Scraping %s every %s minutes", ", ".join(SCRAPERS), settings.scrape_interval_minutes
    )
    scheduler.start()


if __name__ == "__main__":
    main()
