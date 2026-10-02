"""Pulls structured facts (discount, validity dates, card types) out of offer text."""

import html
import re
from calendar import monthrange
from datetime import date, timedelta

from app.models import DiscountType

MONTHS = {
    name: number
    for number, names in enumerate(
        [
            ("jan", "january"),
            ("feb", "february"),
            ("mar", "march"),
            ("apr", "april"),
            ("may",),
            ("jun", "june"),
            ("jul", "july"),
            ("aug", "august"),
            ("sep", "sept", "september"),
            ("oct", "october"),
            ("nov", "november"),
            ("dec", "december"),
        ],
        start=1,
    )
    for name in names
}
_MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))

# "31st October 2026", "1 Nov", "15th of December, 2026"
_FULL_DATE = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MONTH})\b\.?,?(?:\s+(\d{{4}}))?", re.I
)
# A bare ordinal day that borrows the month of the date right after it:
# "01st to 31st October". Not "20th to 30th of every month".
_DAY_BEFORE_RANGE = re.compile(
    rf"\b(\d{{1,2}})(?:st|nd|rd|th)\s+(?=(?:to|-|–|until|till)\s+\d{{1,2}}(?:st|nd|rd|th)?\s+"
    rf"(?:of\s+)?(?:{_MONTH})\b)",
    re.I,
)
# A month and year with no day, as an end date: "till December 2026".
_MONTH_YEAR = re.compile(rf"\b({_MONTH})\s+(\d{{4}})\b", re.I)
_STARTS = re.compile(r"\b(?:from|starting|commencing|effective)\s*$", re.I)
_SINGLE_DAY = re.compile(r"\b(?:valid|only)\s+on\s*$", re.I)

_INSTALLMENT = re.compile(
    r"\b0\s*%[^.]{0,60}?\b(?:install?ments?|instal?ments?|easy\s+payment|EPP|IPP)\b", re.I
)
_MONTHS_COUNT = re.compile(r"\b(\d{1,2})\s*months?\b", re.I)
_PERCENT = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*%")
_RUPEES = re.compile(r"\b(?:Rs\.?|LKR)\s*([\d,]+(?:\.\d+)?)", re.I)

_BRANDS = {
    "Visa": re.compile(r"\bvisa\b", re.I),
    "Mastercard": re.compile(r"\bmaster\s?card\b", re.I),
    "American Express": re.compile(r"\b(?:american\s+express|amex)\b", re.I),
    "UnionPay": re.compile(r"\bunion\s?pay\b", re.I),
}
_KINDS = {
    "Credit": re.compile(r"\bcredit\b", re.I),
    "Debit": re.compile(r"\bdebit\b", re.I),
    "Prepaid": re.compile(r"\bpre-?paid\b", re.I),
}


def html_to_text(markup: str | None) -> str:
    """Strips tags from bank-supplied HTML, keeping one line per block."""
    if not markup:
        return ""
    text = re.sub(r"<\s*(?:br|/p|/li|/div|/h\d)\s*/?>", "\n", markup, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    lines = (re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def parse_discount(text: str) -> tuple[DiscountType | None, float | None]:
    """Finds the headline discount: 0% installments, then the biggest %, then rupees off.

    For rupee amounts the first one is taken: later ones are usually spending
    thresholds ("Rs. 1,500 off on bills over Rs. 10,000").
    """
    if _INSTALLMENT.search(text):
        months = [int(m) for m in _MONTHS_COUNT.findall(text)]
        return DiscountType.INSTALLMENT, float(max(months)) if months else None
    if percents := [float(p) for p in _PERCENT.findall(text) if float(p) > 0]:
        return DiscountType.PERCENTAGE, max(percents)
    if amount := _RUPEES.search(text):
        return DiscountType.FIXED, float(amount[1].replace(",", ""))
    return None, None


def parse_validity(text: str, today: date) -> tuple[date | None, date | None]:
    """Reads an offer's validity window from text such as "Offer valid till 31st
    October 2026" or "from 01st to 31st October 2026". Returns (valid_from, valid_to).
    """
    # (position, day, month, year); a bare day's month and year come from the next date.
    parts: list[tuple[int, int, int | None, int | None]] = []
    full_dates = list(_FULL_DATE.finditer(text))
    for m in full_dates:
        parts.append((m.start(), int(m[1]), MONTHS[m[2].lower()], int(m[3]) if m[3] else None))
    for m in _DAY_BEFORE_RANGE.finditer(text):
        parts.append((m.start(), int(m[1]), None, None))
    for m in _MONTH_YEAR.finditer(text):
        if not any(d.start() <= m.start() < d.end() for d in full_dates):
            month, year = MONTHS[m[1].lower()], int(m[2])
            parts.append((m.start(), monthrange(year, month)[1], month, year))
    parts.sort()

    dates: list[tuple[int, date]] = []
    month: int | None = None
    year: int | None = None
    for position, day, part_month, part_year in reversed(parts):
        month = part_month or month
        year = part_year or year
        if month and (resolved := _safe_date(year or _nearest_year(day, month, today), month, day)):
            dates.append((position, resolved))
    dates.reverse()

    if not dates:
        return None, None
    if len(dates) > 1:
        return dates[0][1], dates[-1][1]
    position, only = dates[0]
    before = text[:position]
    if _SINGLE_DAY.search(before):
        return only, only
    if _STARTS.search(before):
        return only, None
    return None, only


def parse_card_types(text: str) -> list[str]:
    """Lists the cards an offer applies to, e.g. ["Visa Credit", "Mastercard Credit"]."""
    brands = [name for name, pattern in _BRANDS.items() if pattern.search(text)]
    kinds = [name for name, pattern in _KINDS.items() if pattern.search(text)]
    if brands and kinds:
        return [f"{brand} {kind}" for brand in brands for kind in kinds]
    return brands or kinds


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _nearest_year(day: int, month: int, today: date) -> int:
    """For a date written without a year, picks the year that puts it closest to today."""
    candidate = _safe_date(today.year, month, day)
    if candidate and candidate < today - timedelta(days=180):
        return today.year + 1
    return today.year
