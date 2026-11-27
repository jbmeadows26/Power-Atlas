import importlib.util, pathlib, unittest
p=pathlib.Path(__file__).resolve().parents[1]/"business-intelligence/collect_hts_reference.py"
s=importlib.util.spec_from_file_location("hts",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestHTS(unittest.TestCase):
 def test_exact_and_conflict(self):
  rows=[{"htsno":"0123.45.67","general":"Free","special":"","other":"5%"},{"htsno":"0123.45.67.89","general":"","footnotes":[{"value":"note"}]},{"htsno":"1234.56.78","general":"1%"},{"htsno":"1234.56.78","general":"2%"},{"htsno":"0123","general":"1%"}]
  records,ambiguous=m.index_rows(rows)
  self.assertEqual(list(records),["01234567","0123456789"])
  self.assertIsNone(records["0123456789"]["general"]);self.assertTrue(records["0123456789"]["footnotesPresent"])
  self.assertEqual(ambiguous,["12345678"])
 def test_malformed(self):
  for x in [{},[None],[{"htsno":"0123.45.67","general":7}]]:
   with self.assertRaises(ValueError):m.index_rows(x)
if __name__=="__main__":unittest.main()
