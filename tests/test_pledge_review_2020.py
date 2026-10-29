"""The review template must never imply complete extraction or human adjudication."""
import copy
import unittest
from scripts.prepare_pledge_adjudication import make,validate_score,effort_index

class PledgeReview2020Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=make()

    def test_explicitly_incomplete_document_and_pledge_census(self):
        self.assertEqual(self.doc["reviewedPledgeCandidates"],32)
        self.assertEqual(self.doc["knownDocumentsCount"],5)
        self.assertFalse(self.doc["sourceCollectionRule"]["allPlatformSentencesEnumerated"])
        self.assertFalse(self.doc["sourceCollectionRule"]["candidateReleaseCensusComplete"])
        self.assertFalse(self.doc["sourceCollectionRule"]["fullDenominatorFrozen"])
        self.assertEqual(self.doc["humanIndependentAdjudications"],0)

    def test_republican_2020_did_not_adopt_new_platform(self):
        rr=[x for x in self.doc["knownPrimaryDocuments"] if x["side"]=="REP"]
        self.assertTrue(any(x["primarySourceScope"]=="no_new_platform_adopted_in_2020" for x in rr))
        self.assertTrue(all(x["governingPartyFor2021_2025"] is False for x in rr))

    def test_no_existing_provisional_label_is_treated_as_adjudicated(self):
        self.assertEqual(len(self.doc["records"]),32)
        self.assertTrue(all(r["ordinalOutcome"] is None and r["legislativeEffortScore"] is None
                         and r["actorIntentClassification"] is None for r in self.doc["records"]))
        self.assertEqual(len([x for x in self.doc["records"] if x["existingProvisionalLabelNotIndependent"]]),8)

    def test_zero_is_not_an_unknown_synonym(self):
        row=copy.deepcopy(self.doc["records"][0])
        row["ordinalOutcome"]=0
        with self.assertRaisesRegex(ValueError,"two independent reviewers"):
            validate_score(row)
        row["reviewerOne"]={"reviewerId":"independent-1","independentlySubmitted":True,"sourceURL":row["sourceURL"]}
        row["reviewerTwo"]={"reviewerId":"independent-2","independentlySubmitted":True,"sourceURL":row["sourceURL"]}
        row["adjudicated"]=True
        with self.assertRaisesRegex(ValueError,"exhaustive negative action search"):
            validate_score(row)
        row["searchCompleteness"]={k:True for k in row["searchCompleteness"]}
        self.assertEqual(validate_score(row),0)

    def test_independent_raters_must_have_different_ids(self):
        row=copy.deepcopy(self.doc["records"][0])
        row["ordinalOutcome"]=3
        reviewer={"reviewerId":"1","independentlySubmitted":True,"sourceURL":row["sourceURL"]}
        row["reviewerOne"]=reviewer
        row["reviewerTwo"]=reviewer
        row["adjudicated"]=True
        with self.assertRaisesRegex(ValueError,"two independent reviewers"):
            validate_score(row)

    def test_effort_index_null_when_unknown(self):
        row=self.doc["records"][0]
        self.assertIsNone(effort_index(row["effortEvidence"]))
        e=copy.deepcopy(row["effortEvidence"])
        for dim in e.values():
            dim["applicable"]=False
        self.assertIsNone(effort_index(e))

    def test_effort_index_only_counts_applicable_sourced_actions(self):
        e=copy.deepcopy(self.doc["records"][0]["effortEvidence"])
        for dim in e.values():
            dim.update({"applicable":True,"evidencePresent":False})
        e["legislativeSponsorship"].update({"evidencePresent":True,"url":"https://www.congress.gov/bill/117th-congress/house-bill/1234"})
        result=effort_index(e)
        self.assertEqual(result,{"positiveEvidenceCount":1,"applicableDimensions":3})
        e["administrativePreparations"]["applicable"]=False
        self.assertEqual(effort_index(e),{"positiveEvidenceCount":1,"applicableDimensions":2})

    def test_unsourced_action_is_rejected(self):
        e=copy.deepcopy(self.doc["records"][0]["effortEvidence"])
        for dim in e.values():
            dim.update({"applicable":False,"evidencePresent":False})
        e["executiveBudgetOrAgenda"]["applicable"]=True
        e["executiveBudgetOrAgenda"]["evidencePresent"]=True
        with self.assertRaisesRegex(ValueError,"original evidence link"):
            effort_index(e)


if __name__=="__main__":
    unittest.main()
