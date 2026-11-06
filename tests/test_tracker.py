import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from tracker.env import get_bool, get_float, get_int, get_str, load_env  # noqa: E402
from tracker.extractor import iter_offers, offer_total, select_best  # noqa: E402
from tracker.interceptor import CapturedPayload  # noqa: E402
from tracker.logbook import append_history, historical_min, render_entry, write_logbook  # noqa: E402
from tracker.models import Offer, SearchResult  # noqa: E402
from tracker.rules import evaluate  # noqa: E402

S = {s.id: s for s in config.SEARCHES}

HOTEL_JSON = {
    "resort": {"name": "Disney's Pop Century Resort"},
    "rooms": [
        {"roomTypeName": "Standard Room", "pricing": {"totalPrice": {"amount": 1900.0, "currency": "USD"},
                                                     "avgNightlyRate": 316.67, "taxes": 237.5}},
        {"roomTypeName": "Preferred Room", "pricing": {"totalPrice": {"amount": 2100.0, "currency": "USD"},
                                                      "avgNightlyRate": 350.0, "originalPrice": 2500}},
        {"roomTypeName": "Family Suite", "pricing": {"totalPrice": {"amount": 4000.0}}},
    ],
}

CAR_JSON = {"vehicles": [
    {"make_model": "Chevrolet Tahoe or similar", "category": "Full-Size SUV", "rate": {"estimatedTotal": "$289.40"}},
    {"make_model": "Toyota Corolla or similar", "category": "Compact", "rate": {"estimatedTotal": "$120.10"}},
    {"make_model": "Chevrolet Suburban or similar", "category": "Premium SUV", "rate": {"estimatedTotal": "$251.00"}},
]}


class ExtractorTests(unittest.TestCase):
    def test_hotel_picks_preferred_total_with_tax(self):
        best, total, any_best, any_total = select_best([CapturedPayload("u", 200, "GET", HOTEL_JSON)], S["pop_quad"])
        self.assertIn("Preferred", best.label)
        self.assertEqual(best.raw_price, 2100.0)
        self.assertAlmostEqual(total, 2100 * 1.125)
        self.assertIn("Standard", any_best.label)

    def test_nightly_multiplied(self):
        o = Offer("Preferred", 350.0, "avgNightlyRate", nightly=True)
        self.assertAlmostEqual(offer_total(o, S["pop_quad"]), 350 * 6 * 1.125)

    def test_excluded_keys_ignored(self):
        keys = {o.price_key for o in iter_offers(HOTEL_JSON)}
        self.assertFalse(any("original" in k.lower() or k.lower().endswith("taxes") for k in keys))

    def test_car_money_strings_and_keywords(self):
        best, total, _, _ = select_best([CapturedPayload("u", 200, "GET", CAR_JSON)], S["avis_suv"])
        self.assertIn("Suburban", best.label)
        self.assertEqual(total, 251.0)


def res(sid, price, matched=True):
    return SearchResult(sid, price=price, matched=matched, offer=Offer("x", price or 0, "total"))


class RulesTests(unittest.TestCase):
    def run_rules(self, results, hist=None):
        return evaluate({r.search_id: r for r in results}, config.HOTEL_GROUPS, config.CAR_RULES,
                        tolerance=400, historical_min=hist)

    def test_direct_saving(self):
        alerts = self.run_rules([res("cabana_quad", 1100)])
        self.assertEqual([a.kind for a in alerts], ["AHORRO DIRECTO"])

    def test_no_alert_when_more_expensive(self):
        self.assertEqual(self.run_rules([res("cabana_quad", 1300), res("cabana_doble", 800)]), [])

    def test_privacy_rule_boundary(self):
        # 2 x 787 = 1574 = 1174 + 400 -> alerta (<=)
        alerts = self.run_rules([res("cabana_doble", 787)])
        self.assertEqual([a.kind for a in alerts], ["PRIVACIDAD"])
        self.assertEqual(self.run_rules([res("cabana_doble", 788)]), [])

    def test_upgrade(self):
        alerts = self.run_rules([res("caribbean_quad", 2406)])
        self.assertEqual([a.kind for a in alerts], ["UPGRADE"])

    def test_unmatched_ignored(self):
        self.assertEqual(self.run_rules([res("cabana_quad", 500, matched=False)]), [])

    def test_car(self):
        alerts = self.run_rules([res("avis_suv", 240)])
        self.assertEqual([a.kind for a in alerts], ["AHORRO DIRECTO"])

    def test_hardrock_without_base(self):
        alerts = self.run_rules([res("hardrock_quad", 900), res("hardrock_doble", 600)],
                                hist={"hardrock_quad": 950})
        self.assertEqual(sorted(a.kind for a in alerts), ["MÍNIMO HISTÓRICO", "PRIVACIDAD"])

    def test_suspicious_flag(self):
        alerts = self.run_rules([res("pop_quad", 400)])
        self.assertTrue(alerts[0].suspicious)


class LogbookTests(unittest.TestCase):
    def test_write_newest_first_and_history(self):
        with tempfile.TemporaryDirectory() as d:
            md, csv_path = Path(d) / "b.md", Path(d) / "h.csv"
            results = {"cabana_quad": res("cabana_quad", 1100),
                       "pop_quad": SearchResult("pop_quad", error="Flujo sin calibrar")}
            alerts = self.run_alerts(results)
            for hour in (9, 21):
                when = datetime(2026, 11, 6, hour, 0)
                write_logbook(md, "Florida 2027", render_entry(when, config.SEARCHES, results, alerts, {}))
                append_history(csv_path, when, results)
            text = md.read_text(encoding="utf-8")
            self.assertLess(text.index("2026-11-06 21:00"), text.index("2026-11-06 09:00"))
            self.assertIn("AHORRO DIRECTO", text)
            self.assertEqual(text.count("# 📒"), 1)
            self.assertEqual(historical_min(csv_path), {"cabana_quad": 1100.0})

    @staticmethod
    def run_alerts(results):
        return evaluate(results, config.HOTEL_GROUPS, config.CAR_RULES)


class EnvTests(unittest.TestCase):
    def test_native_parser_and_getters(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            test_env = Path(d) / ".env.test"
            test_env.write_text(
                "# Comentario\n"
                "TEST_STR=\"Florida 2027\"\n"
                "TEST_FLOAT=123.45\n"
                "TEST_INT=42\n"
                "TEST_BOOL=true\n"
                "TEST_EMPTY=\n",
                encoding="utf-8",
            )
            load_env(test_env)
            self.assertEqual(get_str("TEST_STR"), "Florida 2027")
            self.assertEqual(get_float("TEST_FLOAT"), 123.45)
            self.assertEqual(get_int("TEST_INT"), 42)
            self.assertTrue(get_bool("TEST_BOOL"))
            self.assertEqual(get_str("TEST_EMPTY", "default"), "default")
            self.assertIsNone(get_float("TEST_NON_EXISTENT"))


if __name__ == "__main__":
    unittest.main()

