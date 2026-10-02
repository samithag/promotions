from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.models import Bank, Promotion, RunStatus, ScrapeRun
from app.scrapers.combank import LISTING_URL
from app.services.banks import sync_banks
from app.services.scrape import ATTEMPTS, fail_interrupted_runs, run_scrape, save_raw
from tests.conftest import FIXTURES

LISTING = (FIXTURES / "combank_rewards_promotions.html").read_text(encoding="utf-8")


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(raw_dir=tmp_path / "raw", request_delay_seconds=0, retry_wait_seconds=0)


@pytest.fixture
def factory(session_factory: sessionmaker[Session]) -> sessionmaker[Session]:
    with session_factory() as session:
        sync_banks(session)
    return session_factory


def client(listing: httpx.Response, calls: list[str] | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) != LISTING_URL:
            return httpx.Response(404)  # robots.txt and detail pages
        if calls is not None:
            calls.append(str(request.url))
        return listing

    return httpx.Client(transport=httpx.MockTransport(handler))


def active_count(factory: sessionmaker[Session]) -> int:
    with factory() as session:
        return len(session.scalars(select(Promotion).where(Promotion.is_active)).all())


def test_successful_run_stores_offers_and_raw_pages(factory, settings) -> None:
    run = run_scrape("combank", factory, settings, client(httpx.Response(200, text=LISTING)))

    assert run.status == RunStatus.SUCCESS
    assert (run.offers_found, run.offers_new, run.offers_closed) == (42, 42, 0)
    assert run.finished_at is not None
    assert (Path(run.raw_path) / "listing.html").read_text(encoding="utf-8") == LISTING
    assert active_count(factory) == 42


def test_blocked_run_leaves_stored_offers_active(factory, settings) -> None:
    run_scrape("combank", factory, settings, client(httpx.Response(200, text=LISTING)))

    blocked = client(httpx.Response(200, text="<html>Request rejected</html>"))
    run = run_scrape("combank", factory, settings, blocked)

    assert run.status == RunStatus.BLOCKED
    assert "No offers found" in run.error
    assert active_count(factory) == 42


def test_server_errors_are_retried_then_recorded(factory, settings) -> None:
    calls: list[str] = []
    run = run_scrape("combank", factory, settings, client(httpx.Response(503), calls))

    assert run.status == RunStatus.FAILED
    assert "HTTPStatusError" in run.error
    assert len(calls) == ATTEMPTS


def test_client_errors_are_not_retried(factory, settings) -> None:
    calls: list[str] = []
    run = run_scrape("combank", factory, settings, client(httpx.Response(403), calls))
    assert run.status == RunStatus.FAILED
    assert len(calls) == 1


def test_save_raw_keeps_only_the_newest_runs(tmp_path: Path) -> None:
    for hour in range(5):
        started = datetime(2026, 10, 2, hour, tzinfo=UTC)
        save_raw(tmp_path, "combank", started, {"listing.html": str(hour)}, keep=3)

    kept = sorted(p.name for p in (tmp_path / "combank").iterdir())
    assert kept == ["20261002T020000Z", "20261002T030000Z", "20261002T040000Z"]


def test_database_errors_are_recorded_on_the_run(factory, settings, monkeypatch) -> None:
    def broken_ingest(session, bank, offers, now):
        # Missing required columns: fails when flushed, like a constraint violation.
        session.add(Promotion(bank_id=bank.id))

    monkeypatch.setattr("app.services.scrape.ingest", broken_ingest)
    run = run_scrape("combank", factory, settings, client(httpx.Response(200, text=LISTING)))

    assert run.status == RunStatus.FAILED
    assert "IntegrityError" in run.error
    assert run.finished_at is not None


def test_fail_interrupted_runs(factory) -> None:
    with factory() as session:
        bank_id = session.scalars(select(Bank.id)).first()
        session.add_all([ScrapeRun(bank_id=bank_id), ScrapeRun(bank_id=bank_id, status="success")])
        session.commit()
        assert fail_interrupted_runs(session) == 1
        statuses = sorted(r.status for r in session.scalars(select(ScrapeRun)))
    assert statuses == ["failed", "success"]
