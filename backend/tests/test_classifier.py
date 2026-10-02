import pytest

from app.services.classifier import classify


@pytest.mark.parametrize(
    ("bank_category", "text", "expected"),
    [
        # The bank's own label wins when it is specific.
        ("Food & Restaurants", "Courtyard by Marriott Colombo", "dining"),
        ("SuperMarkets", "Keells", "supermarket"),
        ("Electronics & Furniture", "Damro", "electronics"),
        ("Leisure", "Relax at Hunas Falls", "hotels"),
        ("dining", "Hilton Colombo - Oktoberfest 2026", "dining"),
        # Generic labels fall back to keywords in the title and merchant.
        ("Premium Card Offers", "Stay at Cinnamon Bey Beruwala", "hotels"),
        ("VISA_Offers", "Fill up at Lanka IOC", "fuel"),
        ("Other Offers", "Weekend shopping at Cargills Food City", "supermarket"),
        (None, "Order on Daraz", "online"),
        ("Other", "Annual fee waiver", "other"),
    ],
)
def test_classify(bank_category: str | None, text: str, expected: str) -> None:
    assert classify(bank_category, text) == expected
