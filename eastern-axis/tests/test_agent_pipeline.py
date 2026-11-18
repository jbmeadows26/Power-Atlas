import importlib.util
import pathlib
import sys
import unittest
from unittest.mock import patch

target=pathlib.Path(__file__).resolve().parents[1]/"scripts"/"agent_pipeline.py"
sys.path.insert(0,str(target.parent))
spec=importlib.util.spec_from_file_location("ea_analyst",target)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class AnalystTests(unittest.TestCase):
 def test_bad_source_schema_rejected(self):
  with self.assertRaises(ValueError):m.digest({"records":""})
 def test_no_uncorroborated_prose_published(self):
  rows=m.digest({"records":[
   {"url":"http://bad.example","title":"Bad"},
   {"id":"a","url":"https://www.defense.gov/news","title":"Official report",
    "publisher":"Defense.gov","countryMentions":["CN","RU","INVALID"],
    "excerpt":"unverified AI accusation","changeType":"new-publication"}]})
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]["countries"],["CN","RU"])
  self.assertNotIn("excerpt",rows[0])
 def test_secrets_not_published(self):
  with patch.dict("os.environ",{"EA_OPENCTI_URL":"https://cti.example.org","EA_OPENCTI_TOKEN":"SECRET_SENTINEL"}):
   with patch.object(m,"fetch",return_value={"data":{"__typename":"Query"}}):
    entry=m.opencti()
  self.assertEqual(entry["status"],"ok")
  self.assertNotIn("SECRET_SENTINEL",str(entry))
 def test_absent_endpoints_not_connected(self):
  with patch.dict("os.environ",{},clear=True):
   self.assertEqual(m.openaleph()["status"],"not-configured")
   self.assertEqual(m.opencti()["status"],"not-configured")
 def test_https_enforced(self):
  for url in ("file:///etc/passwd","http://bad.example","https://user:pass@ok.example"):
   with self.assertRaises(ValueError):m.https(url)


 def test_public_government_intake_metadata_only(self):
  rows=m.government_intake({"records":[
   {"sourceId":"doj","id":"123","title":"Published legal record","sourceUrl":"https://www.justice.gov/opa/pr/sample","countryMention":"RU","summary":"UNVERIFIED CLAIM","date":"2026-11-18"},
   {"sourceId":"unknown","title":"Untrusted","sourceUrl":"https://bad.example/x"},
   {"sourceId":"cisa","title":"An advisory","sourceUrl":"http://insecure.invalid","countryMention":"CN"}]})
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]["countries"],["RU"])
  self.assertEqual(rows[0]["changeType"],"baseline")
  self.assertNotIn("summary",rows[0])
 def test_publisher_coverage_is_not_threat_score(self):
  from analyst_briefs import build_analysis, tags
  rows=[
   {"id":"a","title":"Official report on missile supplies","url":"https://gov.uk/a","date":"2026-11-18","publisher":"UK MOD","countries":["UA"],"changeType":"baseline","sourceId":"monitor"},
   {"id":"b","title":"Cyber vulnerability advisory","url":"https://cisa.gov/b","date":"2026-11-18","publisher":"CISA","countries":["UA"],"changeType":"new-publication","sourceId":"cisa"}]
  brief=build_analysis(rows,use_model=False)
  self.assertEqual(brief["recordsAnalyzed"],2)
  self.assertEqual(brief["countryBriefs"][0]["sourceCount"],2)
  self.assertEqual(brief["countryBriefs"][0]["publisherCount"],2)
  self.assertEqual(brief["countryBriefs"][0]["changedCount"],1)
  self.assertIn("coverage, not a threat",brief["countryBriefs"][0]["statement"].lower())
  self.assertEqual(brief["semantic"]["status"],"disabled")
  self.assertIn("cyber",tags(rows[1]))
 def test_no_correlations_in_single_source(self):
  from analyst_briefs import build_analysis
  rows=[{"id":"1","title":"Minister speaks","publisher":"Official office","url":"https://example.com","countries":["CN"],"date":"","changeType":"baseline"}]
  result=build_analysis(rows,use_model=False)
  self.assertEqual(result["relatedReports"],[])
  self.assertEqual(result["quality"]["sourceTitlesWithoutDates"],1)

if __name__=="__main__":unittest.main()
