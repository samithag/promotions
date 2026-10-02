"""Sorts offers from every bank into one shared set of categories."""

import re

CATEGORIES: dict[str, str] = {
    "dining": "Dining",
    "supermarket": "Supermarket",
    "travel": "Travel",
    "hotels": "Hotels",
    "fashion": "Fashion",
    "electronics": "Electronics",
    "health": "Health",
    "fuel": "Fuel",
    "online": "Online",
    "other": "Other",
}

# The banks' own category labels (normalised by `_key`) mapped to shared categories.
# Labels that say nothing about the merchant ("Premium Offers", "VISA Offers") are
# left out, so those offers fall through to the keyword rules.
BANK_CATEGORIES: dict[str, str] = {
    # ComBank
    "food-restaurants": "dining",
    "supermarket": "supermarket",
    "online-shopping": "online",
    "healthcare": "health",
    "travel": "travel",
    "leisure": "hotels",
    # Sampath
    "dining": "dining",
    "supermarkets": "supermarket",
    "online": "online",
    "health-and-insurance": "health",
    "travel-and-leisure": "travel",
    "hotels": "hotels",
    "fashion": "fashion",
    "electronics-furniture": "electronics",
}

# Regex alternatives per category, checked in order: the more specific rules come
# first ("Food City" is a supermarket, not dining).
KEYWORDS: dict[str, str] = {
    "fuel": r"fuel|petrol|diesel|filling station|ceypetco|lanka ioc",
    "supermarket": r"super ?markets?|grocer|keells|cargills|food ?city|arpico|spar|glomark",
    "electronics": r"electronic|appliance|mobile phone|laptop|furniture|abans|singer|damro",
    "health": r"hospital|pharmac|health|medical|clinic|dental|optical|wellness|insurance|asiri",
    "fashion": r"fashion|clothing|apparel|boutique|footwear|shoe|jewell|saree|odel|cool planet",
    "hotels": r"hotel|resort|villa|bungalow|lodge|stay|spa\b|cinnamon|jetwing|hilton|shangri",
    "travel": r"travel|airline|airways|flight|tour|holiday|cab\b|taxi",
    "dining": r"restaurant|dining|dine|caf[eé]|coffee|bakery|pizza|buffet|food|kitchen|burger",
    "online": r"online|e-commerce|website|\.lk\b|app\b|daraz",
}
KEYWORD_RULES = [
    (category, re.compile(rf"\b(?:{words})", re.I)) for category, words in KEYWORDS.items()
]


def _key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def classify(bank_category: str | None, text: str) -> str:
    """Picks a shared category: the bank's own label when it is specific, otherwise
    keyword rules over the offer's title and merchant, otherwise "other".
    """
    if bank_category and (category := BANK_CATEGORIES.get(_key(bank_category))):
        return category
    for category, pattern in KEYWORD_RULES:
        if pattern.search(text):
            return category
    return "other"
