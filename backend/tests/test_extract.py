from datetime import date

import pytest

from app.models import DiscountType
from app.services.extract import html_to_text, parse_card_types, parse_discount, parse_validity

TODAY = date(2026, 10, 2)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Up to 10% Off", (DiscountType.PERCENTAGE, 10)),
        ("Up to 15% Discount", (DiscountType.PERCENTAGE, 15)),
        ("Offer 1: 30% Discount ... Offer 2: 25% Discount", (DiscountType.PERCENTAGE, 30)),
        ("Rs. 1,500 off on bills over Rs. 10,000", (DiscountType.FIXED, 1500)),
        ("LKR 500 cashback", (DiscountType.FIXED, 500)),
        ("0% interest installment plans for up to 24 months", (DiscountType.INSTALLMENT, 24)),
        ("0% Easy Payment Plan", (DiscountType.INSTALLMENT, None)),
        ("Buy one get one free", (None, None)),
    ],
)
def test_parse_discount(text: str, expected: tuple) -> None:
    assert parse_discount(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Offer valid till 31st October 2026", (None, date(2026, 10, 31))),
        ("Offer valid on every Thursday till 15th October 2026", (None, date(2026, 10, 15))),
        (
            "Offer applicable from 01st to 31st October 2026.",
            (date(2026, 10, 1), date(2026, 10, 31)),
        ),
        ("Valid till 01st October to 31st October 2026.", (date(2026, 10, 1), date(2026, 10, 31))),
        ("from 1st September 2026 to 31st January 2027", (date(2026, 9, 1), date(2027, 1, 31))),
        ("Valid from 5th November 2026", (date(2026, 11, 5), None)),
        # No year: the nearest one is assumed, rolling into next year near January.
        ("Valid until 15 Jan", (None, date(2027, 1, 15))),
        ("Valid for group of 2-20 adults", (None, None)),
    ],
)
def test_parse_validity(text: str, expected: tuple) -> None:
    assert parse_validity(text, TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("For all Sampath Visa Credit Cardholders", ["Visa Credit"]),
        (
            "for Sampath Mastercard and Visa Credit Cardholders",
            ["Visa Credit", "Mastercard Credit"],
        ),
        ("with ComBank Credit and Debit Cards", ["Credit", "Debit"]),
        ("with ComBank Cards", []),
    ],
)
def test_parse_card_types(text: str, expected: list[str]) -> None:
    assert parse_card_types(text) == expected


def test_html_to_text_keeps_blocks_on_separate_lines() -> None:
    markup = '<p><span style="x">15% off</span> &amp; more</p><ul><li>One</li><li>Two</li></ul>'
    assert html_to_text(markup) == "15% off & more\nOne\nTwo"
