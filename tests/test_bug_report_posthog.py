"""Regression gates for the on-site PostHog bug-report delivery path."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "platform" / "unified"
SURVEY = "01a1cd1f-de06-0000-eda7-520ae05958d0"

class BugReportPostHogTests(unittest.TestCase):
    def test_every_unified_page_loads_bug_report(self):
        pages = sorted(SITE.glob("*.html"))
        self.assertGreaterEqual(len(pages), 20)
        missing = [p.name for p in pages if '<script src="bug-report.js"' not in p.read_text(encoding="utf-8")]
        self.assertEqual(missing, [])

    def test_form_posts_to_same_origin_and_does_not_redirect_to_github(self):
        js = (SITE / "bug-report.js").read_text(encoding="utf-8")
        self.assertIn("fetch('/api/bug-report'", js)
        self.assertIn('status.textContent = "Report received.', js)
        self.assertIn("if (!response.ok || !result.ok || !result.received)", js)
        self.assertIn("Copy report", js)
        self.assertNotIn("github.com/jbmeadows26/Power-Atlas/issues/new", js)
        self.assertNotIn("location.assign", js)

    def test_server_uses_posthog_config_and_survey_protocol(self):
        js = (SITE / "api" / "bug-report.js").read_text(encoding="utf-8")
        for expected in (
            SURVEY, "POSTHOG_PUBLIC_TOKEN", "POSTHOG_API_HOST",
            '"survey sent"', '"survey shown"', '"survey dismissed"',
            "$survey_submission_id", "$survey_completed",
            "$survey_response_", "Capture rejected", "response.ok",
        ):
            self.assertIn(expected, js)
        self.assertNotIn("github.com", js)


    def test_qa_monitor_captures_privacy_safe_browser_failures(self):
        js = (SITE / "qa-monitor.js").read_text(encoding="utf-8")
        self.assertIn('pa_qa_browser_error', js)
        self.assertIn('unhandledrejection', js)
        self.assertIn('window.addEventListener("error"', js)
        self.assertIn('disable_session_recording:true', js)
        self.assertIn('capture_pageview:false', js)
        self.assertIn('autocapture:false', js)
        self.assertIn('pa_page:path', js)
        self.assertNotIn('captureException(', js)

    def test_web_vital_numeric_measurements_survive_privacy_redaction(self):
        js = (SITE / "qa-monitor.js").read_text(encoding="utf-8")
        self.assertIn('capture_performance:true', js)
        self.assertIn('event.event==="$web_vitals"', js)
        self.assertIn('typeof obj[k]==="number" && Number.isFinite(obj[k])', js)
        self.assertIn('event.properties.pa_page=path', js)
        self.assertIn('zip|postal|form|element|text|input|value', js)

if __name__ == "__main__":
    unittest.main()
