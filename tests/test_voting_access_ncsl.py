"""Validate NCSL 2026 in-person voter ID index against 51 jurisdiction domain."""
import json
from pathlib import Path
import unittest
D=Path(__file__).resolve().parents[1]/"data"/"voting-access"
class NCSLIdTests(unittest.TestCase):
  def test_partition_and_provenance(self):
    d=json.loads((D/"ncsl-id-index-v1.json").read_text())
    c=json.loads((D/"state-policy-coverage-v1.json").read_text())
    rows=[x for v in d["classification"].values() for x in v]
    wanted={j["id"][3:] for j in c["jurisdictions"]}
    self.assertEqual(len(rows),len(set(rows)))
    self.assertEqual(set(rows),wanted)
    self.assertEqual(len(d["classification"]["strict_photo"])+len(d["classification"]["strict_nonphoto"])+len(d["classification"]["nonstrict_photo"])+len(d["classification"]["nonstrict_nonphoto"]),36)
    self.assertEqual(len(d["classification"]["no_id_document_required"]),15)
    self.assertEqual(d["scope"],"in_person_voting_only")
    self.assertIn("secondary_source",d["publicationStatus"])
    self.assertTrue(d["source"].startswith("https://www.ncsl.org/"))
if __name__=="__main__":unittest.main()
