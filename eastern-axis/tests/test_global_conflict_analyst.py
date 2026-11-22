#!/usr/bin/env python3
"""Offline regression gates for global conflict screens: no live-source dependency."""
import importlib.util
import io
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import TestCase, mock

MODULE = Path(__file__).resolve().parents[1] / "scripts/global_conflict_analyst.py"
spec = importlib.util.spec_from_file_location("global_conflict_analyst", MODULE)
analyst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyst)


def conflict_history():
    anchor = date(2026, 10, 31)
    events = []
    for i in range(8, 0, -1):
        end = anchor - timedelta(days=28 * i)
        for offset in (20, 19):
            events.append({"id": "historical-" + str(len(events)), "country": "Sudan",
                           "date": end - timedelta(days=offset), "fatalities": 2,
                           "actors": ["Government", "Opposition"]})
    # Include the beginning of the oldest complete 28-day baseline.
    events.append({"id": "oldest", "country": "Sudan",
                   "date": anchor - timedelta(days=251), "fatalities": 1,
                   "actors": ["Government", "Opposition"]})
    for i in range(24):
        events.append({"id": "recent-" + str(i), "country": "Sudan",
                       "date": anchor - timedelta(days=i), "fatalities": 1,
                       "actors": ["Government", "Opposition"]})
    return events


def articles(when="2026-10-31"):
    return [
        {"id": "news-" + str(i), "date": when, "publisher": "publisher" + str(i) + ".org",
         "title": "Reported event for review", "url": "https://publisher" + str(i) + ".org/news"}
        for i in range(3)
    ]


class GlobalConflictAnalystTests(TestCase):
    def test_ucdp_candidate_csv_works_without_any_api_token(self):
        historical = (date.today() - timedelta(days=300)).isoformat()
        recent = (date.today() - timedelta(days=10)).isoformat()
        def reader(url):
            if url.endswith("GEDEvent_v26_01_26_09.csv"):
                return ("id,country,date_start,best,side_a,side_b\n" +
                        "11,Sudan," + historical + ",2,Government,Opposition\n").encode()
            if url.endswith("GEDEvent_v26_0_10.csv"):
                return ("id,country,date_start,best,side_a,side_b\n" +
                        "12,Sudan," + recent + ",4,Government,Opposition\n").encode()
            raise AssertionError("Unreviewed source URL " + url)
        events, meta = analyst.collect_ucdp(reader=reader)
        self.assertEqual(meta["status"], "ok")
        self.assertEqual(meta["format"], "two official downloadable CSV releases")
        self.assertEqual(len(events), 2)
        self.assertEqual(sorted(e["fatalities"] for e in events), [2,4])
        self.assertIn("jan-sep-2026", meta["releases"])
        self.assertIn("oct-2026", meta["releases"])
        self.assertIn("GEDEvent_v26_0_10.csv", meta["releases"]["oct-2026"]["url"])

    def test_october_only_cannot_pretend_it_contains_a_full_history(self):
        recent = (date.today()-timedelta(days=10)).isoformat()
        csv_sample = ("id,country,date_start,best\n" +
                      "12,Sudan," + recent + ",4\n").encode()
        with self.assertRaises(ValueError):
            analyst.collect_ucdp(reader=lambda url: csv_sample)

    def test_unverified_or_empty_csv_fails_closed(self):
        with self.assertRaises(ValueError):
            analyst.collect_ucdp(reader=lambda url: b"<html>Error</html>")
        with self.assertRaises(ValueError):
            analyst.collect_ucdp(reader=lambda url: b"")

    def test_anomaly_uses_eight_real_historical_windows(self):
        report, stats = analyst.assess(
            conflict_history(), {"sudan": {"status": "ok", "articles": articles()}},
            datetime(2026, 11, 10, tzinfo=timezone.utc))
        sudan = next(z for z in report if z["id"] == "sudan")
        self.assertEqual(sudan["change"]["status"], "assessable")
        self.assertEqual(len(sudan["change"]["history"]), 8)
        self.assertEqual(sudan["direction"], "deteriorating")
        self.assertEqual(sudan["status"], "review")
        self.assertFalse(sudan["promoted"])
        self.assertEqual(stats["latestCodedEvent"], "2026-10-31")

    def test_no_history_does_not_mean_zero_events(self):
        report, _ = analyst.assess([], {}, datetime(2026, 11, 10, tzinfo=timezone.utc))
        self.assertTrue(all(z["status"] == "data-gap" for z in report))
        self.assertIsNone(report[0]["change"]["recent"])

    def test_old_observation_blocks_escalation_even_with_news(self):
        report, _ = analyst.assess(
            conflict_history(), {"sudan": {"status": "ok", "articles": articles("2026-11-21")}},
            datetime(2027, 2, 14, tzinfo=timezone.utc))
        sudan = next(z for z in report if z["id"] == "sudan")
        self.assertFalse(sudan["measurementFresh"])
        self.assertNotEqual(sudan["status"], "review")
        self.assertFalse(sudan["promoted"])

    def test_media_diversity_is_not_an_independent_event_measurement(self):
        report, _ = analyst.assess(
            conflict_history(), {"sudan": {"status": "ok", "articles": articles()}},
            datetime(2026, 11, 10, tzinfo=timezone.utc))
        sudan = next(z for z in report if z["id"] == "sudan")
        self.assertEqual(sudan["media"]["publishers"], 3)
        self.assertEqual(sudan["sourceCount"], 1)
        self.assertFalse(sudan["promoted"])
        self.assertIn("not event or death verification", sudan["media"]["limitation"].lower())

    def test_ai_review_requires_evidence_and_temporal_alignment(self):
        zones, _ = analyst.assess(
            conflict_history(), {"sudan": {"status": "ok", "articles": articles("2026-07-01")}},
            datetime(2026, 11, 10, tzinfo=timezone.utc))
        sudan = next(z for z in zones if z["id"] == "sudan")
        response = {
            "decision": "review", "whoBenefits": "Potential relative advantage is unknown.",
            "globalRisks": "Humanitarian spillover could spread regionally.",
            "potentialUpside": "A lasting settlement could reduce displacement.",
            "reason": "Event counts diverge from recorded baseline.",
            "confidence": "low"
        }
        report = {"zones": [sudan], "analyst": {}, "summary": {}}
        with mock.patch.object(analyst, "model_review", return_value=response):
            analyst.apply_review(report, "http://127.0.0.1:11434")
        self.assertTrue(sudan["modelReviewed"])
        self.assertFalse(sudan["promoted"])
        self.assertEqual(sudan["status"], "review")
        self.assertEqual(report["summary"]["assessed"], 0)

    def test_reviewed_time_aligned_exception_can_be_published_only_in_defense(self):
        zones, _ = analyst.assess(
            conflict_history(), {"sudan": {"status": "ok", "articles": articles()}},
            datetime(2026, 11, 10, tzinfo=timezone.utc))
        sudan = next(z for z in zones if z["id"] == "sudan")
        response = {
            "decision": "review", "whoBenefits": "No demonstrated victor in the supplied sources.",
            "globalRisks": "Conflict could put pressure on regional food supplies.",
            "potentialUpside": "Sustained de-escalation could improve civilian access.",
            "reason": "Historical event rate is well above the baseline.",
            "confidence": "medium"
        }
        report = {"zones": [sudan], "analyst": {}, "summary": {}}
        with mock.patch.object(analyst, "model_review", return_value=response):
            analyst.apply_review(report, "http://127.0.0.1:11434")
        self.assertTrue(sudan["promoted"])
        self.assertEqual(sudan["status"], "assessed")
        self.assertEqual(report["summary"]["assessed"], 1)
        self.assertEqual(report["summary"]["deteriorating"], 1)

    def test_public_rss_has_real_publisher_and_original_article_link(self):
        sample = (b'<rss><channel><item><title>Sudan humanitarian update</title>'
                  b'<link>https://news.un.org/en/story/2026/11/99999</link>'
                  b'<pubDate>Sun, 22 Nov 2026 02:00:00 GMT</pubDate>'
                  b'</item></channel></rss>')
        parsed = analyst.parse_public_rss(sample, "UN News",
                                          checked=date(2026, 11, 22))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["publisher"], "UN News")
        self.assertEqual(parsed[0]["date"], "2026-11-22")
        index = analyst.match_rss_to_theaters(parsed, [{"name": "UN News", "status": "ok"}])
        self.assertEqual(len(index["sudan"]["articles"]), 1)
        self.assertEqual(len(index["taiwan"]["articles"]), 0)

    def test_stale_or_unsafe_rss_article_cannot_be_corroboration(self):
        stale = (b'<rss><channel><item><title>Sudan update</title>'
                 b'<link>http://unsafe.example/a</link>'
                 b'<pubDate>Thu, 01 Jan 2026 02:00:00 GMT</pubDate>'
                 b'</item></channel></rss>')
        self.assertEqual(analyst.parse_public_rss(stale, "Test", checked=date(2026, 11, 22)), [])

    def test_url_restrictions_and_deduplication(self):
        self.assertIsNone(analyst.safe_evidence_url("http://unsafe.example/a"))
        self.assertIsNone(analyst.safe_evidence_url("https://user:pass@x.example/a"))
        sample = {"articles": [
            {"url": "https://example.org/a", "seendate": date.today().isoformat(), "title": "Story"},
            {"url": "https://example.org/a", "seendate": date.today().isoformat(), "title": "Duplicate"}]}
        parsed = analyst.parse_gdelt_articles(sample)
        self.assertEqual(len(parsed), 1)

    def test_failed_ucdp_feed_cannot_create_alerts(self):
        with mock.patch.object(analyst, "collect_ucdp", side_effect=ValueError("unavailable")), \
             mock.patch.object(analyst, "collect_public_rss", return_value=([], [])):
            report = analyst.build()
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["summary"]["assessed"], 0)
        self.assertEqual(report["analyst"]["commandEligible"], 0)
        self.assertTrue(all(z["status"] == "data-gap" and not z["promoted"] for z in report["zones"]))


if __name__ == "__main__":
    import unittest
    unittest.main()
