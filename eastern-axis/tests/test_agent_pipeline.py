import asyncio
import importlib.util
import pathlib
import tempfile
import types
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
 def test_allied_government_assessments_indexed_with_original_sources(self):
  reports,portals=m.allied_assessments({"assessments":[
   {"id":"ca-test","title":"Canadian public intelligence report","group":"Five Eyes",
    "agency":"Canadian Security Intelligence Service","published":"2026-11-17",
    "url":"https://www.canada.ca/en/security-intelligence-service/corporate/publications.html",
    "countries":["CN","RU","INVALID"],"finding":"Unverified interpretation must not be published."},
   {"id":"au-context","title":"Regional cyber report","group":"Five Eyes","agency":"Australian Signals Directorate",
    "published":"2026-11","url":"https://www.cyber.gov.au/","countries":[]},
   {"id":"research","title":"Non-allied publisher","group":"Research","agency":"External research",
    "url":"https://example.org","countries":["CN"]},
   {"id":"insecure","title":"Insecure example","group":"Five Eyes","agency":"Example",
    "url":"http://example.org","countries":["CN"]}],
   "sources":[
    {"name":"NZ NCSC","group":"Five Eyes","url":"https://www.ncsc.govt.nz/","what":"Public cyber advisories"},
    {"name":"Research website","group":"Research","url":"https://example.org/"},
    {"name":"Bad link","group":"Five Eyes","url":"http://example.org/"}]})
  self.assertEqual(len(reports),2)
  self.assertEqual(reports[0]["countries"],["CN","RU"])
  self.assertEqual(reports[1]["countries"],[])
  self.assertEqual(reports[0]["sourceId"],"allied-assessment")
  self.assertEqual(reports[0]["changeType"],"baseline")
  self.assertNotIn("finding",str(reports))
  self.assertEqual(len(portals),1)
  self.assertEqual(portals[0]["mode"],"linked-official-source-not-ingested-evidence")
 def test_allied_schema_fails_closed(self):
  with self.assertRaises(ValueError):m.allied_assessments({"assessments":"incorrect","sources":[]})
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


 def test_title_country_inference_preserves_provenance(self):
  from country_mentions import infer_country_mentions
  cases=[
   ("Haiti: UN calls for protection", "official-source-monitor", ["HT"]),
   ("Syria: fragile recovery in Lebanon", "official-source-monitor", ["LB", "SY"]),
   ("Hegseth, Polish Counterpart Announce Military Cooperation", "official-source-monitor", ["PL"]),
   ("Army, Allies Prepare for Air Assault in Hawaii", "official-source-monitor", ["US"]),
   ("Iranian Ministry of Intelligence and Security", "ofac", ["IR"]),
   ("UK and Russian defense ministers meet", "official-source-monitor", ["GB", "RU"]),
   ("South Sudan humanitarian situation", "official-source-monitor", ["SS"]),
   ("Nigeria and Niger host talks", "official-source-monitor", ["NE", "NG"]),
   ("An Indian Ocean naval exercise", "official-source-monitor", []),
   ("Georgian defense minister speaks", "official-source-monitor", []),
   ("Apache Axis unsafe reflection vulnerability", "cisa", []),
   ("Enterprise Singapore (Americas)", "fara", []),
   ("Vulnerability report from the United States", "cisa", []),
   ("Unspecified cyber incident", "official-source-monitor", []),
   ("A new aircraft program with no named place", "official-source-monitor", []),
   ("Moscow and Taipei hold talks", "official-source-monitor", ["RU","TW"]),
  ]
  for title,source,expected in cases:
   with self.subTest(title=title):
    matches=infer_country_mentions({"title":title,"publisher":"UK Ministry of Defence","sourceId":source})
    self.assertEqual([m["code"] for m in matches],expected)
    for match in matches:
     self.assertIn(match["matchedText"].lower(),title.lower())
     self.assertIn(match["basis"],("title-country-name","title-place-name"))
     self.assertIn(match["confidence"],("high","medium"))
  self.assertEqual(infer_country_mentions({"title":"Expeditionary Wing Sharpens Skills","publisher":"U.S. Defense", "sourceId":"official-source-monitor"}),[])

 def test_title_associations_are_not_source_country_tags(self):
  from analyst_briefs import build_analysis
  rows=[
    {"id":"a","title":"Haiti: UN raises concerns","publisher":"UN News","url":"https://example.org/a","countries":[],"date":"2026-11-21","changeType":"baseline","sourceId":"official-source-monitor"},
    {"id":"b","title":"Syria and Lebanon update","publisher":"UN News","url":"https://example.org/b","countries":["SY"],"date":"2026-11-21","changeType":"baseline","sourceId":"official-source-monitor"},
    {"id":"c","title":"Unassigned cybersecurity advisory","publisher":"CISA","url":"https://example.org/c","countries":[],"date":"2026-11-21","changeType":"baseline","sourceId":"cisa"},
  ]
  analysis=build_analysis(rows,use_model=False)
  self.assertEqual(rows[0]["countries"],[])
  self.assertEqual(rows[0]["inferredCountries"][0]["code"],"HT")
  self.assertEqual(rows[1]["countries"],["SY"])
  self.assertEqual([m["code"] for m in rows[1]["inferredCountries"]],["LB","SY"])
  self.assertEqual(analysis["quality"]["countryTaggedCount"],1)
  self.assertEqual(analysis["quality"]["inferredOnlyCount"],1)
  self.assertEqual(analysis["quality"]["unassignedCount"],1)
  self.assertEqual([b["code"] for b in analysis["countryBriefs"]],["SY"])
  self.assertEqual([b["code"] for b in analysis["inferredCountryBriefs"]],["HT","LB"])

 def test_keyless_local_research_drafts_not_in_public_manifest(self):
  class MockResearcher:
   def __init__(self,query,report_type): self.query=query
   async def conduct_research(self): pass
   async def write_report(self): return "This is an unreviewed draft with original-source links. "+("Traceable source context. "*10)
   def get_research_sources(self): return [{"url":"https://www.cisa.gov/news-events/alerts"}]
  fake=types.ModuleType("gpt_researcher")
  fake.GPTResearcher=MockResearcher
  with tempfile.TemporaryDirectory() as tmp:
   with patch.dict("os.environ",{"EA_FREE_LLM_LOCAL":"true","OPENAI_API_KEY":"","TAVILY_API_KEY":""}):
    with patch.dict("sys.modules",{"gpt_researcher":fake}):
     result=asyncio.run(m.draft("Research source publications",pathlib.Path(tmp)))
    self.assertEqual(result["gpt-researcher"]["status"],"ok")
    self.assertTrue((pathlib.Path(tmp)/"GPT-Researcher-UNREVIEWED.md").exists())
    self.assertFalse((pathlib.Path(tmp)/"manifest.json").exists())
 def test_missing_attribution_prevents_research_success(self):
  class Unsourced:
   def __init__(self,query,report_type):pass
   async def conduct_research(self):pass
   async def write_report(self):return "An unsourced draft "*30
   def get_research_sources(self):return []
  fake=types.ModuleType("gpt_researcher")
  fake.GPTResearcher=Unsourced
  with tempfile.TemporaryDirectory() as tmp:
   with patch.dict("os.environ",{"EA_FREE_LLM_LOCAL":"true","OPENAI_API_KEY":"","TAVILY_API_KEY":""}):
    with patch.dict("sys.modules",{"gpt_researcher":fake}):
     result=asyncio.run(m.draft("Test report provenance",pathlib.Path(tmp)))
    self.assertEqual(result["gpt-researcher"]["status"],"error")

if __name__=="__main__":unittest.main()
