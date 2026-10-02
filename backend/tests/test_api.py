from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

import app.api.v1 as api
from app.core.config import Settings, get_settings
from app.main import app
from app.models import Bank, DiscountType, Promotion, RunStatus, ScrapeRun

TODAY = date(2026, 10, 2)
SEEN = datetime(2026, 9, 1, tzinfo=UTC)

# The keys frontend/src/lib/promotions/types.ts reads.
PROMOTION_KEYS = {
    "id", "bank", "title", "merchant", "description", "discount_value", "discount_type",
    "card_types", "category", "bank_category", "valid_from", "valid_to", "image_url",
    "source_url", "first_seen_at", "last_seen_at", "is_active",
}  # fmt: skip


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "local_today", lambda: TODAY)


@pytest.fixture
def seeded(client: TestClient, session_factory: sessionmaker[Session]) -> dict[str, int]:
    """Five offers covering every status, sort key and both banks. Returns ids by name."""
    with session_factory() as session:
        banks = {b.code: b.id for b in session.scalars(select(Bank))}
        rows = {
            "keells": dict(bank="combank", category="supermarket", merchant="Keells",
                           discount=(DiscountType.PERCENTAGE, 25), to=date(2026, 10, 31), age=5),
            "hilton": dict(bank="sampath", category="dining", merchant="Hilton Colombo",
                           discount=(DiscountType.PERCENTAGE, 15), to=date(2026, 10, 5), age=1),
            "singer": dict(bank="sampath", category="electronics", merchant="Singer",
                           discount=(DiscountType.INSTALLMENT, 24), to=None, age=3),
            "cinnamon": dict(bank="combank", category="hotels", merchant="Cinnamon Grand",
                             discount=(DiscountType.FIXED, 5000), to=date(2026, 12, 31), age=0,
                             start=date(2026, 11, 1)),
            "ended": dict(bank="combank", category="dining", merchant="Old Cafe",
                          discount=(None, None), to=date(2026, 9, 30), age=30),
        }  # fmt: skip
        ids = {}
        for name, row in rows.items():
            promotion = Promotion(
                bank_id=banks[row["bank"]],
                external_id=name,
                content_hash=name,
                title=f"Offer at {row['merchant']}",
                merchant=row["merchant"],
                description=f"Terms for {row['merchant']}",
                discount_type=row["discount"][0],
                discount_value=row["discount"][1],
                card_types=["Visa", "Credit"],
                category=row["category"],
                bank_category="Bank label",
                valid_from=row.get("start"),
                valid_to=row["to"],
                source_url=f"https://bank.example/{name}",
                first_seen_at=SEEN + timedelta(days=30 - row["age"]),
                last_seen_at=SEEN,
            )
            session.add(promotion)
            session.flush()
            ids[name] = promotion.id
        session.commit()
    return ids


def names(response, ids: dict[str, int]) -> list[str]:
    by_id = {str(v): k for k, v in ids.items()}
    return [by_id[item["id"]] for item in response.json()["items"]]


def test_list_matches_the_frontend_contract(client: TestClient, seeded) -> None:
    body = client.get("/api/v1/promotions", params={"bank": "combank", "q": "keells"}).json()

    assert body.keys() == {"items", "total", "page", "page_size"}
    assert (body["total"], body["page"], body["page_size"]) == (1, 1, 12)
    item = body["items"][0]
    assert item.keys() == PROMOTION_KEYS
    assert item["id"] == str(seeded["keells"])
    assert item["bank"] == "combank"
    assert item["discount_type"] == "percentage"
    assert item["valid_to"] == "2026-10-31"
    assert item["card_types"] == ["Visa", "Credit"]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, ["cinnamon", "hilton", "singer", "keells", "ended"]),
        ({"status": "active"}, ["hilton", "singer", "keells"]),
        ({"status": "upcoming"}, ["cinnamon"]),
        ({"status": "expired"}, ["ended"]),
        ({"bank": "sampath"}, ["hilton", "singer"]),
        ({"category": "dining"}, ["hilton", "ended"]),
        ({"q": "HILTON"}, ["hilton"]),
        ({"q": "terms for singer"}, ["singer"]),
        ({"sort": "ending_soon"}, ["ended", "hilton", "keells", "cinnamon", "singer"]),
        ({"sort": "discount"}, ["keells", "hilton", "cinnamon", "singer", "ended"]),
    ],
)
def test_filters_and_sorts(client: TestClient, seeded, params, expected) -> None:
    assert names(client.get("/api/v1/promotions", params=params), seeded) == expected


def test_pagination(client: TestClient, seeded) -> None:
    response = client.get("/api/v1/promotions", params={"page": 2, "page_size": 2})
    assert names(response, seeded) == ["singer", "keells"]
    assert response.json()["total"] == 5


def test_inactive_offers_count_as_expired(
    client: TestClient, seeded, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        session.get(Promotion, seeded["keells"]).is_active = False
        session.commit()
    response = client.get("/api/v1/promotions", params={"status": "expired"})
    assert names(response, seeded) == ["keells", "ended"]


@pytest.mark.parametrize(
    "params",
    [{"status": "soon"}, {"sort": "random"}, {"category": "toys"}, {"page_size": 101}],
)
def test_rejects_invalid_params(client: TestClient, params) -> None:
    assert client.get("/api/v1/promotions", params=params).status_code == 422


def test_get_promotion(client: TestClient, seeded) -> None:
    response = client.get(f"/api/v1/promotions/{seeded['singer']}")
    assert response.status_code == 200
    assert response.json()["merchant"] == "Singer"
    assert client.get("/api/v1/promotions/999999").status_code == 404


def test_categories_count_every_category(client: TestClient, seeded) -> None:
    body = client.get("/api/v1/categories", params={"status": "active"}).json()
    counts = {c["slug"]: c["count"] for c in body}
    assert len(body) == 10
    assert body[0] == {"slug": "dining", "label": "Dining", "count": 1}
    assert (counts["supermarket"], counts["hotels"], counts["fuel"]) == (1, 0, 0)


def test_banks(client: TestClient) -> None:
    codes = [b["code"] for b in client.get("/api/v1/banks").json()]
    assert codes == ["combank", "sampath"]


def test_scrape_runs_newest_first(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        bank_id = session.scalars(select(Bank.id)).first()
        for status in (RunStatus.SUCCESS, RunStatus.BLOCKED):
            session.add(ScrapeRun(bank_id=bank_id, status=status, error=None))
        session.commit()
    runs = client.get("/api/v1/scrape-runs").json()
    assert [r["status"] for r in runs] == ["blocked", "success"]


class TestStartScrape:
    @pytest.fixture
    def started(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        calls: list[str] = []
        monkeypatch.setattr(api, "run_scrape", lambda code, *args: calls.append(code))
        return calls

    @pytest.fixture
    def admin(self) -> None:
        app.dependency_overrides[get_settings] = lambda: Settings(admin_token="secret")
        yield
        del app.dependency_overrides[get_settings]

    def test_disabled_without_admin_token(self, client: TestClient, started) -> None:
        app.dependency_overrides[get_settings] = lambda: Settings(admin_token=None)
        try:
            assert client.post("/api/v1/scrape-runs").status_code == 403
        finally:
            del app.dependency_overrides[get_settings]
        assert started == []

    def test_rejects_a_wrong_token(self, client: TestClient, admin, started) -> None:
        response = client.post("/api/v1/scrape-runs", headers={"X-Admin-Token": "nope"})
        assert response.status_code == 401
        assert started == []

    def test_starts_every_bank_or_one(self, client: TestClient, admin, started) -> None:
        headers = {"X-Admin-Token": "secret"}
        response = client.post("/api/v1/scrape-runs", headers=headers)
        assert (response.status_code, response.json()) == (
            202,
            {"banks": ["combank", "sampath"]},
        )
        client.post("/api/v1/scrape-runs", headers=headers, json={"bank": "sampath"})
        assert started == ["combank", "sampath", "sampath"]
        unknown = client.post("/api/v1/scrape-runs", headers=headers, json={"bank": "hsbc"})
        assert unknown.status_code == 404
