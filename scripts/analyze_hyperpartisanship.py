"""Offline generator for Power Atlas's two separately sourced Congressional aggregate series."""
import csv
import json
from pathlib import Path
from statistics import mean
ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data/hyperpartisanship"
def load(name,cols):
    with (DIR/name).open(encoding="utf-8",newline="") as f: rows=list(csv.DictReader(f))
    assert len(rows)==20 and [int(r["congress"]) for r in rows]==list(range(100,120))
    for r in rows:
        for c in cols:r[c]=int(r[c]);assert r[c]>=0
        r["congress"]=int(r["congress"])
        assert r["source_url"].startswith("https://")
    return rows
def calculate():
    L=load("pew-pre-election-laws-100-119.csv",["substantive","ceremonial"])
    C=load("senate-cloture-100-119.csv",["motions_filed","votes_on_cloture","cloture_invoked"])
    assert all(x["cutoff"]=="pre_election" for x in L[:-1]) and L[-1]["cutoff"]=="as_of_2026-10-14"
    assert all(x["cutoff"]=="full_congress" for x in C[:-1]) and C[-1]["cutoff"]=="as_of_2026-10-29"
    s=[]
    for l,c in zip(L,C):
        assert l["congress"]==c["congress"] and l["years"]==c["years"]
        assert c["cloture_invoked"]<=c["votes_on_cloture"]<=c["motions_filed"]
        total=l["substantive"]+l["ceremonial"]
        s.append(dict(congress=l["congress"],years=l["years"],substantive_laws_pre_election=l["substantive"],ceremonial_laws_pre_election=l["ceremonial"],ceremonial_share_pre_election=round(l["ceremonial"]/total,4) if total else None,cloture_motions_filed=c["motions_filed"],cloture_votes=c["votes_on_cloture"],cloture_invoked=c["cloture_invoked"],complete_congress=l["congress"]<119))
    def avg(a,k):return round(mean(r[k] for r in a),2)
    def cohort(a):return dict(congresses=[x["congress"] for x in a],mean_substantive_pre_election=avg(a,"substantive_laws_pre_election"),mean_ceremonial_pre_election=avg(a,"ceremonial_laws_pre_election"),mean_cloture_motions_full_congress=avg(a,"cloture_motions_filed"))
    a,b=cohort(s[:10]),cohort(s[10:19])
    # Files intentionally don't impute the unfinished 119th as an entire Congress.
    return dict(schema="power-atlas.hyperpartisanship.descriptive.v1",asOf="2026-10-29",publicationStatus="published_aggregate_transcription_descriptive_not_causal",scope="Congress 100–119; pre-election legislation; full-Congress Senate cloture until Congress 118",sourceRecords=[
      dict(name="Pew pre-election laws",url="https://www.pewresearch.org/chart/congress-productivity-continues-to-dwindle/",publicationDate="2026-10-15",snapshot119="2026-10-14",method="Pew-defined substantive/ceremonial categorization"),
      dict(name="U.S. Senate cloture table",url="https://www.senate.gov/legislative/cloture/clotureCounts.htm",retrieved="2026-10-29",snapshot119="2026-10-29",method="All cloture, includes nominations; filing does not necessarily equal filibuster")],
      comparability="Pew pre-election law counts versus whole-Congress historical cloture counts have DIFFERENT cutoff periods. Analyze separately; juxtaposition is descriptive, not matched-temporal evidence.",
      series=s,cohorts=dict(earlier_100_109=a,later_110_118=b,change_mean_substantive_percent=round(100*(b["mean_substantive_pre_election"]/a["mean_substantive_pre_election"]-1),2),change_mean_cloture_percent=round(100*(b["mean_cloture_motions_full_congress"]/a["mean_cloture_motions_full_congress"]-1),2),notCausal=True),
      specificComparison={"102nd_pre_election_substantive":387,"118th_pre_election_substantive":84,"change_percent":round(100*(84/387-1),2)},
      doNotInfer=["Number of landmark statutes or statutory significance","Filibuster frequency or obstruction on legislation only from total cloture motions","Causal link from party polarization to law counts","Relative influence of voters versus party without member-level model","119th Congress full-term trend before end of term"],
      nextMeasurements=["Member-by-roll-call party alignment and party-majority position using Voteview","Bill-by-sponsor and dated cross-party cosponsorship using Congress.gov","Committee bottlenecks, floor agenda gates, technical-bill baselines","Legislation-only cloture and nomination separation","FEC dated fundraising x pre-registered rhetoric x social-media engagement"])
if __name__=="__main__":
    out=DIR/"baseline-v1.json"
    data=json.dumps(calculate(),indent=2,ensure_ascii=False)+"\n"
    out.write_text(data,encoding="utf-8")
    print(json.dumps(calculate()["cohorts"],indent=2))
