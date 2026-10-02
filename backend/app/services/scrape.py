"""Runs one bank's scrape end to end and records it in `scrape_runs`."""

import logging
import shutil
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.models import Bank, RunStatus, ScrapeRun, utcnow
from app.scrapers.base import BlockedError, ScrapeResult
from app.scrapers.registry import SCRAPERS
from app.services.ingest import ingest

log = logging.getLogger(__name__)

ATTEMPTS = 3


def _is_transient(error: BaseException) -> bool:
    """Network failures, timeouts, 429s and 5xx responses are worth retrying."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code == 429 or error.response.status_code >= 500
    return isinstance(error, httpx.TransportError)


def make_client(settings: Settings) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": settings.user_agent},
        timeout=settings.request_timeout_seconds,
        follow_redirects=True,
    )


def run_scrape(
    code: str,
    session_factory: sessionmaker[Session],
    settings: Settings,
    client: httpx.Client | None = None,
) -> ScrapeRun:
    """Scrapes one bank, stores its offers, and logs the run.

    Never raises: failures are recorded on the returned run instead. A blocked run
    leaves stored offers untouched.
    """
    with session_factory() as session:
        bank = session.scalars(select(Bank).where(Bank.code == code)).one()
        run = ScrapeRun(bank_id=bank.id, started_at=utcnow(), status=RunStatus.RUNNING)
        session.add(run)
        session.commit()

        try:
            result = _fetch(code, settings, client)
            run.raw_path = save_raw(
                settings.raw_dir, code, run.started_at, result.raw, keep=settings.raw_keep_per_bank
            )
            _lock_bank(session, bank.id)
            stats = ingest(session, bank, result.offers, utcnow())
            session.flush()  # surface database errors here, where they are recorded
            run.status = RunStatus.SUCCESS
            run.offers_found = stats.found
            run.offers_new = stats.new
            run.offers_closed = stats.closed
        except BlockedError as error:
            session.rollback()
            run.status, run.error = RunStatus.BLOCKED, str(error)
        except Exception as error:  # recorded on the run; the worker keeps going
            session.rollback()
            log.exception("Scrape of %s failed", code)
            run.status, run.error = RunStatus.FAILED, f"{type(error).__name__}: {error}"

        run.finished_at = utcnow()
        session.add(run)
        session.commit()
        log.info(
            "Scrape of %s finished: %s (%s found, %s new, %s closed)",
            code,
            run.status,
            run.offers_found,
            run.offers_new,
            run.offers_closed,
        )
        return run


def _lock_bank(session: Session, bank_id: int) -> None:
    """Serialises ingest per bank, so a manual scrape and the hourly one can't both
    insert the same new offer. Held until the transaction ends. A no-op on SQLite,
    which only allows one writer anyway.
    """
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": bank_id})


def fail_interrupted_runs(session: Session) -> int:
    """Marks runs left "running" by a stopped process as failed. Call at worker startup."""
    runs = session.scalars(select(ScrapeRun).where(ScrapeRun.status == RunStatus.RUNNING)).all()
    for run in runs:
        run.status = RunStatus.FAILED
        run.error = "Interrupted: the process running this scrape stopped"
        run.finished_at = utcnow()
    session.commit()
    return len(runs)


def _fetch(code: str, settings: Settings, client: httpx.Client | None) -> ScrapeResult:
    @retry(
        retry=retry_if_exception(_is_transient),
        stop=stop_after_attempt(ATTEMPTS),
        wait=wait_exponential(multiplier=settings.retry_wait_seconds, max=300),
        reraise=True,
    )
    def attempt(http: httpx.Client) -> ScrapeResult:
        return SCRAPERS[code](http, settings.request_delay_seconds).scrape()

    if client is not None:
        return attempt(client)
    with make_client(settings) as http:
        return attempt(http)


def save_raw(root: Path, code: str, started_at: datetime, files: dict[str, str], keep: int) -> str:
    """Saves a run's raw responses under `root/<bank>/<timestamp>/`, keeping the newest `keep`."""
    bank_dir = root / code
    run_dir = bank_dir / started_at.strftime("%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (run_dir / name).write_text(content, encoding="utf-8")
    for old in sorted(p for p in bank_dir.iterdir() if p.is_dir())[:-keep]:
        shutil.rmtree(old, ignore_errors=True)
    return str(run_dir)
