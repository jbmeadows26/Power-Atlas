import importlib.util, pathlib, unittest, datetime as dt
p=pathlib.Path(__file__).resolve().parents[1]/"business-intelligence/public_analyst.py"
s=importlib.util.spec_from_file_location("public_analyst",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestPublicAnalyst(unittest.TestCase):
 def test_gate(self):
  source="https://www.worldbank.org/en/research/commodity-markets"
  rows=m.extract({"forecasts":[{"evidence":[{"kind":"input-price","title":"Copper","period":"2026-10","changePct":6,"url":source},{"kind":"input-price","title":"Oil","period":"2024-10","changePct":12,"url":source},{"kind":"input-price","title":"Other","period":"2026-10","changePct":9,"url":"https://example.org"}]}]},dt.date(2026,11,27))
  self.assertEqual(len(rows),1)
  self.assertEqual(m.validate({"status":"ok","provider":"ollama","model":"local","text":"{\"review_ids\":[\"E1\"]}"},rows)["status"],"review-only")
  for result in [{"status":"deferred"},{"status":"ok","provider":"groq","text":"{\"review_ids\":[\"E1\"]}"},{"status":"ok","provider":"ollama","text":"{\"review_ids\":[\"E99\"]}"},{"status":"ok","provider":"ollama","text":"{\"review_ids\":[\"E1\"],\"forecast\":\"shortage\"}"}]:
   with self.assertRaises((ValueError,KeyError)): m.validate(result,rows)
if __name__=="__main__":unittest.main()
