"""Persian digit normalization and Jalali calendar conversion."""

from datetime import date

import pytest

from app.persian import (
    format_jalali,
    gregorian_to_jalali,
    normalize_digits,
    normalize_persian,
    to_ascii_number,
)


def test_persian_digits_are_normalized():
    assert normalize_digits("۱۲۳۴۵۶۷۸۹۰") == "1234567890"
    assert normalize_digits("٠١٢٣٤٥٦٧٨٩") == "0123456789"
    assert normalize_digits("متراژ ۱۲۵") == "متراژ 125"


def test_numbers_parse_with_persian_digits_and_separators():
    assert to_ascii_number("۱٬۲۵۰") == 1250
    assert to_ascii_number("1250") == 1250
    assert to_ascii_number(" ۱٬۲۵۰ ") == 1250


def test_arabic_letter_variants_and_zwnj_are_normalized():
    assert normalize_persian("علي‌رضا") == normalize_persian("علی رضا")
    assert normalize_persian("كتاب") == "کتاب"


@pytest.mark.parametrize(
    ("gregorian", "jalali"),
    [
        (date(2024, 3, 20), (1403, 1, 1)),  # Nowruz 1403
        (date(2025, 3, 21), (1404, 1, 1)),  # Nowruz 1404
        (date(2024, 1, 1), (1402, 10, 11)),
        (date(2026, 11, 18), (1405, 8, 27)),
    ],
)
def test_gregorian_to_jalali(gregorian, jalali):
    assert gregorian_to_jalali(gregorian) == jalali


def test_format_jalali_is_zero_padded():
    assert format_jalali(date(2024, 3, 20)) == "1403/01/01"
    assert format_jalali(date(2026, 11, 18)) == "1405/08/27"
