import unittest
from scripts.validate_house_financial_disclosure import validate

BASE = {"bioguideId":"A000001","filingYear":2025,"documentId":"sample","status":"not_reviewed","originalFilingUrl":None,"assetLowerUSD":None,"assetUpperUSD":None,"estimatedNetWorthUSD":None}

class DisclosureTests(unittest.TestCase):
    def test_null_record(self): self.assertEqual(validate([BASE.copy()]),1)
    def test_duplicate(self):
        with self.assertRaises(ValueError): validate([BASE.copy(),BASE.copy()])
    def test_unverified_interval_rejected(self):
        row={**BASE,"assetLowerUSD":1,"assetUpperUSD":2}
        with self.assertRaises(ValueError): validate([row])
    def test_bad_official_url(self):
        row={**BASE,"status":"verified_filing","originalFilingUrl":"https://example.com/report","reviewedAtUTC":"2026-11-03T11:35:00Z","filingType":"annual"}
        with self.assertRaises(ValueError): validate([row])
    def test_verified_interval(self):
        row={**BASE,"status":"verified_filing","originalFilingUrl":"https://disclosures-clerk.house.gov/example.pdf","reviewedAtUTC":"2026-11-03T11:35:00Z","filingType":"annual","assetLowerUSD":1000,"assetUpperUSD":15000}
        self.assertEqual(validate([row]),1)
    def test_open_ended_verified_interval(self):
        row={**BASE,"status":"verified_filing","originalFilingUrl":"https://disclosures-clerk.house.gov/report.pdf","reviewedAtUTC":"2026-11-04T12:00:00Z","filingType":"annual","assetLowerUSD":50000000,"assetUpperUSD":None,"assetUpperOpenEnded":True}
        self.assertEqual(validate([row]),1)
    def test_open_ended_without_lower_rejected(self):
        row={**BASE,"assetUpperOpenEnded":True}
        with self.assertRaises(ValueError): validate([row])
    def test_open_ended_with_upper_rejected(self):
        row={**BASE,"status":"verified_filing","originalFilingUrl":"https://disclosures-clerk.house.gov/report.pdf","reviewedAtUTC":"2026-11-04T12:00:00Z","filingType":"annual","assetLowerUSD":10,"assetUpperUSD":20,"assetUpperOpenEnded":True}
        with self.assertRaises(ValueError): validate([row])
    def test_spoofed_official_host_rejected(self):
        row={**BASE,"status":"verified_filing","originalFilingUrl":"https://disclosures-clerk.house.gov.evil.test/report.pdf","reviewedAtUTC":"2026-11-04T12:00:00Z","filingType":"annual"}
        with self.assertRaises(ValueError): validate([row])
    def test_nonfinite_and_boolean_bounds_rejected(self):
        for lower in (float("nan"),float("inf"),True,-1):
            row={**BASE,"status":"verified_filing","originalFilingUrl":"https://disclosures-clerk.house.gov/report.pdf","reviewedAtUTC":"2026-11-04T12:00:00Z","filingType":"annual","assetLowerUSD":lower,"assetUpperUSD":100}
            with self.subTest(lower=lower), self.assertRaises(ValueError): validate([row])
    def test_point_net_worth_rejected(self):
        row={**BASE,"estimatedNetWorthUSD":100}
        with self.assertRaises(ValueError): validate([row])

if __name__=="__main__": unittest.main()
