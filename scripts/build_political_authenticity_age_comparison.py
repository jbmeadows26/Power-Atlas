#!/usr/bin/env python3
"""Reproduce age-gap descriptive comparisons; never infer motive or causality."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"data/research/political-authenticity"
# U.S. Census Bureau, 2024 ACS one-year supplemental Table K200104.
# Source: https://data.census.gov/table/ACSSE2024.K200104
ACS={"allResidents":340110990,"under18":72929312,"age18to24":31270959,
     "age25to34":46198405,"age35to44":45956885,"age45to54":40822885,
     "age55to64":41687261,"age65plus":61245283}
def build(snapshot):
    if sum(v for k,v in ACS.items() if k!="allResidents")!=ACS["allResidents"]:
        raise ValueError("ACS source categories do not add to national total")
    records=snapshot["records"]
    house=[r for r in records if r["chamber"]=="House" and r["votingMember"]]
    senator=[r for r in records if r["chamber"]=="Senate"]
    if len(house)<400 or len(senator)!=100:
        raise ValueError("Unexpected snapshot chamber coverage")
    if any(r["ageYears"] is None for r in house+senator):
        raise ValueError("Cannot compare ages with incomplete birthday matching")
    adults25=sum(ACS[k] for k in ("age25to34","age35to44","age45to54","age55to64","age65plus"))
    house25to34=sum(25<=r["ageYears"]<=34 for r in house)
    house65plus=sum(r["ageYears"]>=65 for r in house)
    p=ACS["age25to34"]/adults25
    h=house25to34/len(house)
    return {
      "schema":"power-atlas.political-authenticity-age-descriptive.v1",
      "legislatorSnapshotDate":snapshot["asOf"],"populationReferenceYear":2024,
      "publicationStatus":"descriptive_two_vintage_not_causal_and_not_eligibility_adjusted",
      "populationSource":"https://data.census.gov/table/ACSSE2024.K200104",
      "memberSource":snapshot["source"],"memberSourceSha256":snapshot["sourceSha256"],
      "populationUniverse":"all U.S. residents aged 25+; includes noncitizens; NOT a pool of legally eligible candidates or voting adults",
      "legislatorUniverse":"voting House members in roster snapshot; excludes six nonvoting delegates",
      "populationAge25plus":adults25,"populationAge25to34":ACS["age25to34"],
      "populationAge25to34Share":round(p,6),
      "houseVotingCount":len(house),"houseVotingAge25to34Count":house25to34,
      "houseVotingAge25to34Share":round(h,6),
      "houseMinusPopulation25to34PercentagePoints":round((h-p)*100,3),
      "houseVsPopulation25to34Ratio":round(h/p,4),
      "houseAge65plusCount":house65plus,
      "houseAge65plusShare":round(house65plus/len(house),6),
      "populationAge65plusShareAmongAge25plus":round(ACS["age65plus"]/adults25,6),
      "senateMeanAgeYears":round(sum(r["ageYears"] for r in senator)/len(senator),2),
      "houseVotingMeanAgeYears":round(sum(r["ageYears"] for r in house)/len(house),2),
      "cautions":["2024 population vs 2026 member snapshot","resident rather than citizenship-and-years-of-citizenship eligible universe",
                 "raw counts only; source margins of error not imported; no statistical significance claim",
                 "age differences do not show policy responsiveness or moral conduct",
                 "voting House membership count can vary because of vacancies"]
    }

def main():
    snapshot=json.loads((TARGET/"members.json").read_text(encoding="utf-8"))
    obj=build(snapshot)
    path=TARGET/"age-comparison.json"
    contents=json.dumps(obj,indent=2,ensure_ascii=False)+"\n"
    if not path.exists() or path.read_text(encoding="utf-8")!=contents:
        path.write_text(contents,encoding="utf-8")
    print(json.dumps({"populationAge25to34Pct":obj["populationAge25to34Share"]*100,
       "houseAge25to34Pct":obj["houseVotingAge25to34Share"]*100,
       "houseVotingCount":obj["houseVotingCount"]}))
if __name__=="__main__":main()
