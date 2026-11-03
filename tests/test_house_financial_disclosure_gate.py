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
    def test_point_net_worth_rejected(self):
        row={**BASE,"estimatedNetWorthUSD":100}
        with self.assertRaises(ValueError): validate([row])

if __name__=="__main__": unittest.main()
