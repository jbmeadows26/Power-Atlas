#!/usr/bin/env python3
"""119th House seat/Census ACS 2025 district keys; no population data imputed."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/research/political-authenticity/house-district-crosswalk-119.json"
SEATS=dict(zip("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split(),
[7,1,9,4,52,8,5,1,28,14,2,2,17,9,4,4,6,6,2,8,9,13,8,4,8,2,3,4,2,12,3,26,14,1,15,5,6,17,2,7,1,9,38,4,1,11,10,2,8,1]))
SOURCES={
"apportionment":"https://www.census.gov/data/tables/2020/dec/2020-apportionment-data.html",
"boundaries":"https://www.census.gov/programs-surveys/decennial-census/about/rdo/congressional-districts.119th_Congress.html",
"stateFips":"https://www2.census.gov/geo/docs/reference/state.txt",
"acsRelease":"https://www.census.gov/data/developers/data-sets/acs-1year.2025.html"}
def build(snapshot,states):
    if snapshot.get("schema")!="power-atlas.representation-members.v1" or states.get("schema")!="power-atlas.states.v1":raise ValueError("Unexpected source schema")
    if len(SEATS)!=50 or sum(SEATS.values())!=435:raise ValueError("Invalid apportionment")
    fips={r["postal"]:r["fips"] for r in states["states"] if r["postal"] in SEATS}
    if len(fips)!=50 or len(set(fips.values()))!=50 or any(len(v)!=2 or not v.isdigit() for v in fips.values()):raise ValueError("Invalid Census state keys")
    occupied={}
    seen=set()
    for m in snapshot["records"]:
        ident=m.get("bioguideId")
        if not ident or ident in seen:raise ValueError("Duplicate member ID")
        seen.add(ident)
        if m.get("chamber")!="House" or m.get("votingMember") is not True:continue
        state,d=m["state"],m["district"]
        if state not in SEATS or type(d)!=int or not (d==0 if SEATS[state]==1 else 1<=d<=SEATS[state]):raise ValueError("Invalid 119th House district")
        if (state,d) in occupied:raise ValueError("Duplicate voting seat")
        occupied[(state,d)]=m
    if not 400<=len(occupied)<=435:raise ValueError("Unexpected voting House roster")
    rows=[]
    for state in sorted(SEATS):
        n=SEATS[state]
        for d in ([0] if n==1 else range(1,n+1)):
            m=occupied.get((state,d))
            code=f"{d:02d}"
            rows.append({"seatKey":state+"-"+code,"state":state,"stateFips":fips[state],"districtNumber":d,
              "censusDistrictCode":code,"censusStateDistrictKey":fips[state]+code,
              "memberBioguideId":m["bioguideId"] if m else None,
              "memberAgeYears":m.get("ageYears") if m else None,
              "seatStatus":"occupied_at_snapshot" if m else "vacant_at_snapshot",
              "acs2025Age25plusEstimate":None,"acs2025Age25plusMOE":None,
              "acs2025Age25to34Estimate":None,"acs2025Age25to34MOE":None})
    if len({r["censusStateDistrictKey"] for r in rows})!=435:raise ValueError("Nonunique Census geography key")
    return {"schema":"power-atlas.political-authenticity.house-district-crosswalk.v1",
      "status":"119th_keys_validated_2025_acs_age_estimates_not_ingested",
      "memberSnapshotDate":snapshot["asOf"],"memberSourceUrl":snapshot["source"],
      "memberSourceSha256":snapshot["sourceSha256"],"sourceUrls":SOURCES,
      "boundaryCongress":119,"boundaryReferenceDate":"2025-01-01",
      "acs2025ReleaseDate":"2026-10-29","seatCount":435,
      "occupiedSeatCount":len(occupied),"vacantSeatCount":435-len(occupied),
      "warnings":["At-large state district code is 00","2025 ACS age values and margins of error are null, not zero",
        "119th district geography and October 2026 member roster differ in reference dates",
        "District geography does not authorize ANES/CES individual linkage or causal claims"],
      "records":rows}
def main():
    members=json.loads((ROOT/"data/research/political-authenticity/members.json").read_text())
    states=json.loads((ROOT/"data/geography/states.json").read_text())
    doc=build(members,states)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(doc,separators=(",",":"),ensure_ascii=False)+"\n"
    if not OUT.exists() or OUT.read_text()!=data:OUT.write_text(data)
    print(json.dumps({"seats":435,"occupied":doc["occupiedSeatCount"],"vacant":doc["vacantSeatCount"],"acs2025AgeRows":0}))
if __name__=="__main__":main()
