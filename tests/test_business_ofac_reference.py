import importlib.util, pathlib, unittest, datetime as dt
p=pathlib.Path(__file__).resolve().parents[1]/"business-intelligence/collect_ofac_reference.py"
s=importlib.util.spec_from_file_location("ofac",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NS="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"
def fixture(n=50,claimed=None):
    rows=[]
    for i in range(n):
        rows.append(f"<sdnEntry><uid>{i+1}</uid><lastName>QA Org {i}</lastName><sdnType>{'Entity' if i<40 else 'Individual'}</sdnType><akaList><aka><category>strong</category><lastName>QA Alias</lastName></aka><aka><category>weak</category><lastName>QA Weak</lastName></aka></akaList><programList><program>TEST</program></programList><addressList><address><country>Test</country></address></addressList></sdnEntry>")
    return (f'<sdnList xmlns="{NS}"><publshInformation><Publish_Date>11/23/2026</Publish_Date><Record_Count>{n if claimed is None else claimed}</Record_Count></publshInformation>'+"".join(rows)+"</sdnList>").encode()
class TestReference(unittest.TestCase):
 def test_organization_only(self):
  r=m.parse(fixture(),"Consolidated",dt.date(2026,11,27));self.assertEqual(r["totalEntries"],50);self.assertEqual(r["organizationEntries"],40);self.assertEqual(r["entries"][0]["aliases"],["QA Alias"]);self.assertEqual(r["published"],"2026-11-23")
 def test_fail_closed(self):
  for raw in [fixture(claimed=49),b"<!DOCTYPE x><x/>",b"<x/>"]:
   with self.assertRaises(ValueError):m.parse(raw,"Consolidated",dt.date(2026,11,27))
  with self.assertRaises(ValueError):m.parse(fixture(),"Consolidated",dt.date(2026,11,22))
if __name__=="__main__":unittest.main()
