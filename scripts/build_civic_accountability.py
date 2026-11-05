"""Build a small, reviewable civic-accountability feed from published official-source extracts.

Never infer donor-to-lawmaker influence, campaign purpose of IRS grants, or undisclosed
beneficial owners. Curated bill/action records come from reviewed primary source URLs.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/money-influence/civic-accountability-seed-v1.json"
CATALOG = ROOT / "data/money-influence/civic-power-reforms-v1.json"
FEC = ROOT / "data/finance/fec-committee-transfers.json"
IRS = ROOT / "data/finance/irs-schedule-i-grants-v1.json"
NYC = ROOT / "data/finance/nyc-cfb/campaign-financial-analysis-2025.json"
GRAPH = ROOT / "data/money-influence/dark-money-graph-v1.json"
OUT = ROOT / "data/money-influence/civic-accountability-evidence-v1.json"
ALLOWED_HOSTS = {
    "www.govinfo.gov", "www.congress.gov", "www.fec.gov", "www.nyccfb.info",
    "www.seattle.gov", "www.sos.ca.gov", "www.maine.gov"
}
KINDS = {"bill", "enforcement", "program", "rule"}
STATES = {"introduced_record_verified", "house_passed_senate_cloture_failed",
          "official_conciliation", "official_program_rule", "official_state_rule",
          "official_current_structure", "official_current_rule"}
POSITIONS = {"reform_proposal", "restricts_reform", "enforcement_example", "program_in_use", "current_rule"}

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def build():
    seed, catalog, fec, irs, nyc, graph = map(
        read, (SOURCE, CATALOG, FEC, IRS, NYC, GRAPH)
    )
    assert seed["schema"] == "power-atlas.civic-accountability-seed.v1"
    assert catalog["schema"] == "power-atlas.civic-power-reforms.v1"
    assert fec["schema"] == "power-atlas.fec.oth-transfers.v1"
    assert irs["schema"] == "power-atlas.irs-schedule-i-grants.v1"
    assert nyc["schema"] == "power-atlas.nyc-cfb.campaign-financial-analysis.v1"
    assert graph["schema"] == "power-atlas.dark-money.graph.v1"
    policy_ids = [r["id"] for r in catalog["records"]]
    assert len(policy_ids) == len(set(policy_ids)) == 16
    evidence_ids = set()
    by_policy = {p: [] for p in policy_ids}
    for rec in seed["records"]:
        assert rec["id"] not in evidence_ids, "Duplicate evidence ID"
        evidence_ids.add(rec["id"])
        assert rec["kind"] in KINDS and rec["status"] in STATES
        assert rec["position"] in POSITIONS
        assert rec["date"] <= seed["asOf"], "Future-dated evidence"
        assert rec["title"] and rec["summary"] and rec["caveat"] and rec["scope"]
        src = urlsplit(rec["source"])
        assert src.scheme == "https" and src.hostname in ALLOWED_HOSTS, rec["id"]
        assert rec["reformIds"] and len(set(rec["reformIds"])) == len(rec["reformIds"])
        for ref in rec["reformIds"]:
            assert ref in by_policy, "Unrecognized reform ID"
            by_policy[ref].append(rec["id"])
    vote_ids = set()
    for vote in seed["votes"]:
        assert vote["id"] not in vote_ids
        vote_ids.add(vote["id"])
        assert vote["billRecordId"] in evidence_ids
        assert vote["chamber"] in ("House", "Senate")
        assert vote["result"] in ("passed", "rejected")
        assert vote["yea"] >= 0 and vote["nay"] >= 0
        assert vote["date"] <= seed["asOf"]
        assert vote["question"] and vote["required"] and vote["caveat"]
        assert urlsplit(vote["source"]).hostname in ("clerk.house.gov", "www.senate.gov")
        if vote["chamber"] == "House":
            assert sum(v["yea"] for v in vote["partyTallies"].values()) == vote["yea"]
            assert sum(v["nay"] for v in vote["partyTallies"].values()) == vote["nay"]
    assert graph["metrics"]["filedTransferEdges"] == len(fec["records"])
    assert fec["selection"]["selectedRows"] == len(fec["records"])
    assert irs["validatedCampaignFundingEdges"] == 0
    assert irs["originalDonorIdentitiesExtracted"] is False
    assert graph["metrics"]["verifiedOriginalDonorAttributions"] == 0
    assert nyc["recordCount"] == len(nyc["records"])
    assert nyc["donorToRecipientEdgesCreated"] == 0
    finance = [
        {"id": "fec_2026_receipts", "value": len(fec["records"]),
         "label": "FEC sampled committee receipts", "unit": "itemized rows",
         "period": "2026 cycle", "source": fec["sourceMetadata"]["sourceArchiveURL"],
         "dataset": "data/finance/fec-committee-transfers.json",
         "scope": "Top-dollar bounded sample from selected committees; may contain unreconciled amendments. NOT a national total.",
         "relation": "background_only_no_policy_or_person_link"},
        {"id": "irs_2024_grants", "value": len(irs["records"]),
         "label": "IRS outbound nonprofit grants", "unit": "grant records",
         "period": "2024 tax year pilot", "source": irs["sourceLandingPage"],
         "dataset": "data/finance/irs-schedule-i-grants-v1.json",
         "scope": "Outbound organizational grants; NOT campaign donations, documented lobbying payments or original dark-money donors.",
         "relation": "background_only_no_policy_or_person_link"},
        {"id": "nyc_2025_campaign", "value": len(nyc["records"]),
         "label": "NYC campaign finance analysis", "unit": "source analysis rows",
         "period": "2025 cycle", "source": nyc["sourceURL"],
         "dataset": "data/finance/nyc-cfb/campaign-financial-analysis-2025.json",
         "scope": "Candidate/district/source-variant rows; matching CLAIMS are not disbursements and rows are not safe to sum across variants.",
         "relation": "background_only_no_policy_or_person_link"}
    ]
    return {
        "schema": "power-atlas.civic-accountability-evidence.v1",
        "asOf": seed["asOf"],
        "recordType": "curated_topic_links_not_causal_attributions",
        "records": seed["records"],
        "votes": seed["votes"],
        "policyCoverage": by_policy,
        "metrics": {
            "indexedPolicyActionExamples": len(seed["records"]),
            "indexedPolicyThemes": sum(bool(v) for v in by_policy.values()),
            "notYetIndexedPolicyThemes": sum(not v for v in by_policy.values()),
            "officialRollcallEvents": len(seed["votes"]),
            "officialEnforcementExamples": sum(r["kind"] == "enforcement" for r in seed["records"])
        },
        "financialContext": finance,
        "limitations": [
            "This is a small reviewed illustrative sample, not a census of all introduced legislation or votes.",
            "Bill-version dates identify published source actions; another legislative action may have occurred later.",
            "Senate procedural votes are not final-passage votes. A vote for or against a bill does not establish motivation.",
            "Records share a reform topic, not a proven donor-to-legislator relationship or causal influence.",
            "FEC receipt-side rows may be selected or amendment-unreconciled; do not sum as all federal campaign spending.",
            "IRS grants have unverified political purpose and do not expose original hidden donors.",
            "NYC matching claims do not establish awarded payments. No individual donor data is imported."
        ]
    }

def main():
    result = build()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {len(result['records'])} curated evidence items, "
          f"{len(result['votes'])} roll calls, "
          f"{result['metrics']['indexedPolicyThemes']} of 16 themes with indexed examples")

if __name__ == "__main__":
    main()
