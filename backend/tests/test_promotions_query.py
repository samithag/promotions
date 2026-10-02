from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bank, Promotion
from app.services.banks import sync_banks
from app.services.promotions import status_condition

TODAY = date(2026, 10, 2)


@pytest.mark.parametrize(
    ("valid_from", "valid_to", "is_active", "expected"),
    [
        (None, None, True, "active"),  # no dates: always running
        (TODAY, TODAY, True, "active"),  # first and last day both count
        (date(2026, 10, 3), None, True, "upcoming"),
        (date(2026, 10, 3), date(2026, 10, 31), True, "upcoming"),
        (None, date(2026, 10, 1), True, "expired"),
        (None, None, False, "expired"),  # the scraper no longer sees it
        (date(2026, 10, 3), None, False, "expired"),
    ],
)
def test_status_condition_matches_exactly_one_status(
    session: Session, valid_from, valid_to, is_active, expected
) -> None:
    sync_banks(session)
    bank_id = session.scalars(select(Bank.id)).first()
    now = datetime(2026, 10, 1, tzinfo=UTC)
    session.add(
        Promotion(
            bank_id=bank_id, external_id="x", title="t", merchant="m", category="other",
            source_url="u", valid_from=valid_from, valid_to=valid_to, is_active=is_active,
            first_seen_at=now, last_seen_at=now,
        )
    )  # fmt: skip
    session.flush()

    matches = [
        status
        for status in ("active", "upcoming", "expired")
        if session.scalar(select(Promotion.id).where(status_condition(status, TODAY)))
    ]
    assert matches == [expected]
