"""Validate the ANES observed counts and guard against fake respondent joins."""
import json
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/"data/research/political-authenticity/anes-2024-efficacy-aggregates.json"
class AnesPublishedFrequencyTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads(PATH.read_text(encoding="utf-8"))
    def test_exact_anes_valid_response_counts(self):
        rows={v["variable"]:v for v in self.doc["questions"]}
        expectations={"V242200":(4928,3507),"V242201":(4932,3153)}
        for key,(total,agree) in expectations.items():
            v=rows[key]
            freqs={int(k):int(n) for k,n in v["responseCounts"].items()}
            self.assertEqual(sum(freqs.values()),total)
            self.assertEqual(freqs[1]+freqs[2],agree)
            self.assertAlmostEqual(v["agreeShareValid"],agree/total,places=6)
    def test_no_fake_person_level_geo_or_mixed_wave_claim(self):
        self.assertIn("UNWEIGHTED",self.doc["note"].upper())
        self.assertEqual(self.doc["surveyWave"],"2024 POST")
        for key in ("respondents","zip4","regressionCoefficients","districtResults"):
            self.assertNotIn(key,self.doc)
if __name__=="__main__":unittest.main()
