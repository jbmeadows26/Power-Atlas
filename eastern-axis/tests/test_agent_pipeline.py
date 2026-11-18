import importlib.util
import pathlib
import unittest
from unittest.mock import patch

target=pathlib.Path(__file__).resolve().parents[1]/"scripts"/"agent_pipeline.py"
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

if __name__=="__main__":unittest.main()
