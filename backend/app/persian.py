"""Persian text and calendar helpers.

Iranian users type Persian and Arabic-Indic digits, and the product shows dates
in the Jalali calendar. Mixing those with the Gregorian ISO dates the database
stores is a recurring source of bugs, so the conversions live here and are
covered by tests.
"""

from __future__ import annotations

from datetime import date, datetime

# Persian (۰-۹) and Arabic-Indic (٠-٩) digits mapped to ASCII.
_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_ARABIC_LETTER_MAP = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "‌": " "})


def normalize_digits(value: str) -> str:
    """Convert Persian/Arabic digits to ASCII so numbers can be parsed."""
    return value.translate(_DIGIT_MAP)


def normalize_persian(value: str) -> str:
    """Normalize Arabic letter variants and ZWNJ so comparisons match.

    ``ي``/``ك`` are what Persian keyboards often emit for ``ی``/``ک``, and the
    zero-width non-joiner is invisible but changes equality checks.
    """
    return value.translate(_ARABIC_LETTER_MAP).strip()


def to_ascii_number(value: str) -> float:
    """Parse a number that may contain Persian digits, spaces and Arabic separators."""
    cleaned = normalize_digits(value).replace("٬", "").replace("،", "").replace(",", "").strip()
    return float(cleaned)


def gregorian_to_jalali(value: date) -> tuple[int, int, int]:
    """Convert a Gregorian date to the Jalali (Solar Hijri) calendar.

    Algorithm from the widely used jalaali-js conversion; accurate for the
    supported range (roughly 1800-2256 Gregorian).
    """
    gy, gm, gd = value.year, value.month, value.day
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1

    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    for index in range(gm2):
        g_day_no += g_days_in_month[index]
    if gm2 > 1 and ((gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0):
        g_day_no += 1
    g_day_no += gd2

    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    jm = 0
    for index in range(11):
        if j_day_no < j_days_in_month[index]:
            break
        j_day_no -= j_days_in_month[index]
        jm = index + 1

    return jy, jm + 1, j_day_no + 1


def format_jalali(value: date | datetime) -> str:
    """Format a date as ``YYYY/MM/DD`` in the Jalali calendar."""
    if isinstance(value, datetime):
        value = value.date()
    year, month, day = gregorian_to_jalali(value)
    return f"{year:04d}/{month:02d}/{day:02d}"
