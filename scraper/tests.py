from datetime import date

from django.test import SimpleTestCase

from scraper.services.exceptions import ParseScraperError
from scraper.services.validators import to_int, to_iso_date, to_str


class ValidatorsTests(SimpleTestCase):
    # --- to_int (4 cas) ---

    def test_to_int_from_int(self):
        self.assertEqual(to_int(75981, field="game_id"), 75981)

    def test_to_int_from_str(self):
        self.assertEqual(to_int("75981", field="game_id"), 75981)

    def test_to_int_invalid_string(self):
        with self.assertRaises(ParseScraperError):
            to_int("abc", field="game_id")

    def test_to_int_none(self):
        with self.assertRaises(ParseScraperError):
            to_int(None, field="game_id")

    # --- to_iso_date (4 cas) ---

    def test_to_iso_date_from_iso_string(self):
        self.assertEqual(to_iso_date("2026-04-11", field="game_date"), date(2026, 4, 11))

    def test_to_iso_date_from_date(self):
        d = date(2026, 4, 11)
        self.assertEqual(to_iso_date(d, field="game_date"), d)

    def test_to_iso_date_invalid_format(self):
        with self.assertRaises(ParseScraperError):
            to_iso_date("11/04/2026", field="game_date")

    def test_to_iso_date_none(self):
        with self.assertRaises(ParseScraperError):
            to_iso_date(None, field="game_date")

    # --- to_str (5 cas) ---

    def test_to_str_strips_whitespace(self):
        self.assertEqual(to_str("  LEC  ", field="tournament"), "LEC")

    def test_to_str_required_non_empty_ok(self):
        self.assertEqual(to_str("CD 2026", field="tournament"), "CD 2026")

    def test_to_str_required_rejects_empty(self):
        with self.assertRaises(ParseScraperError):
            to_str("", field="game_name")

    def test_to_str_required_rejects_whitespace_only(self):
        with self.assertRaises(ParseScraperError):
            to_str("   ", field="game_name")

    def test_to_str_allow_empty(self):
        self.assertEqual(to_str("", field="champ", allow_empty=True), "")
        self.assertEqual(to_str(None, field="champ", allow_empty=True), "")