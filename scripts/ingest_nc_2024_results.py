"""Ingest original 2024 North Carolina official precinct returns and reconcile.

The ORIGINAL state-board results ZIP is distinct from the privacy-noised
'precinct sorted' product. Both the original archive and derived county and
judicial aggregates retain byte-level provenance. The 2024 canvass is linked
at https://www.ncsbe.gov/results-data/election-results/historical-election-results-data

Authority: NC State Board of Elections. 2024-11-26 certified canvass reference.
"""
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from scripts.probe_nc_official_returns import URL, PUBLISHER
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"data/elections/nc-2024"
SRC_SHA256="2fab44e9b12e03c0d88ef832c2e6dc8c569e2b020d64df06a8b551b62bbdb426"
PDF="https://s3.amazonaws.com/dl.ncsbe.gov/State_Board_Meeting_Docs/2024-11-26/Canvass/Certification%20of%20State%20Jurisdiction%20Contests%20112624.pdf"
PDF_COUNTY="https://s3.amazonaws.com/dl.ncsbe.gov/State_Board_Meeting_Docs/2024-11-26/Canvass/Authentication%20of%20Composite%20Abstract%20112624.pdf"
REQUIRED={"County","Election Date","Precinct","Contest Group ID","Contest Type","Contest Name",
 "Choice","Choice Party","Vote For","Election Day","Early Voting","Absentee by Mail",
 "Provisional","Total Votes","Real Precinct"}

CERTIFIED={
 ("US PRESIDENT","Donald J. Trump","REP"):2898424,
 ("US PRESIDENT","Kamala D. Harris","DEM"):2715378,
 ("NC GOVERNOR","Josh Stein","DEM"):3069499,
 ("NC GOVERNOR","Mark Robinson","REP"):2241310,
}

def fetch():
    req=urllib.request.Request(URL,headers={"User-Agent":"PowerAtlasPublicResearch/1.0 verified NC results"})
    with urllib.request.urlopen(req,timeout=90) as r:
        data=r.read(70_000_001)
    if len(data)>70_000_000 or hashlib.sha256(data).hexdigest()!=SRC_SHA256:
        raise ValueError("Official NC 2024 original ZIP source changed; audit required")
    return data

def source_rows(source):
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        members=z.namelist()
        if members!=["results_pct_20241105.txt"]:
            raise ValueError("Unexpected original NC results ZIP members")
        if z.infolist()[0].file_size>30_000_000:
            raise ValueError("Unexpected original NC vote file expanded bytes")
        with z.open(members[0]) as r:
            t=io.TextIOWrapper(r,encoding="utf-8-sig",errors="strict",newline="")
            reader=csv.DictReader(t,delimiter="\t")
            if not REQUIRED.issubset(set(reader.fieldnames or [])):
                raise ValueError("Unexpected NC election tabular column schema")
            for x in reader:
                yield x

def summarize(source):
    counties=set();count=0
    counties_groups=defaultdict(int)
    contests=defaultdict(int)
    seen=set()
    for row in source_rows(source):
        count+=1
        if count>1_000_000:raise ValueError("NC vote record volume cap exceeded")
        county=row["County"].strip()
        if not county:raise ValueError("Missing NC county")
        counties.add(county)
        if row["Election Date"]!="11/05/2024":
            raise ValueError("Unexpected NC election date")
        contest=row["Contest Name"].strip()
        choice=row["Choice"].strip()
        party=row["Choice Party"].strip()
        precinct=row["Precinct"].strip()
        if not all((precinct,contest,choice)):raise ValueError("Missing contest/candidate/precinct key: "+repr({k:row[k] for k in ("County","Precinct","Contest Name","Choice","Real Precinct","Contest Group ID")}))
        key=(county,precinct,row["Contest Group ID"],contest,choice,party)
        if key in seen:raise ValueError("Duplicate source key "+str(key))
        seen.add(key)
        v={}
        for field in ("Election Day","Early Voting","Absentee by Mail","Provisional","Total Votes"):
            s=row[field].strip().replace(",","")
            if not s.isdigit():raise ValueError("Nonnumeric NC vote count in "+field)
            v[field]=int(s)
        if sum(v[f] for f in ("Election Day","Early Voting","Absentee by Mail","Provisional"))!=v["Total Votes"]:
            raise ValueError("Original source vote-method reconciliation mismatch "+str(key))
        ckey=(contest,choice,party)
        counties_groups[(county,*ckey)]+=v["Total Votes"]
        contests[ckey]+=v["Total Votes"]
    if len(counties)!=100:
        raise ValueError("Incomplete NC county set: "+str(len(counties)))
    check=[]
    for ckey,official in CERTIFIED.items():
        observed=contests.get(ckey)
        check.append({"contest":ckey[0],"choice":ckey[1],"party":ckey[2],
                      "certifiedVotes":official,"aggregatedPrecinctVotes":observed,
                      "difference":None if observed is None else observed-official,
                      "comparison":"NCSBE certified 2024-11-26 statewide canvass PDF"})
    # Don't silently report mismatch as a successful reconciliation. However,
    # return a documented discrepancy table rather than making up a total.
    reconciliation_pass=all(x["difference"]==0 for x in check)
    county_rows=[{"county":k[0],"contest":k[1],"choice":k[2],"party":k[3],"votes":v}
      for k,v in sorted(counties_groups.items())]
    judges=[{"contest":k[0],"candidate":k[1],"party":k[2],"votes":v,
             "certificationStatus":"official_precinct_source_not_independently_certified_per_judicial_race"}
      for k,v in sorted(contests.items())
      if any(j in k[0] for j in ("SUPREME COURT","COURT OF APPEALS","DISTRICT COURT","SUPERIOR COURT"))]
    return {
      "countyRows":county_rows,"judicialRows":judges,
      "metadata":{
        "schema":"power-atlas.official-nc-2024-local-election-reconciliation.v1",
        "publicationStatus":"source_level_state_county_results_ingested_partial_certification_crosschecks",
        "sourceURL":URL,"sourcePublisherURL":PUBLISHER,
        "sourceZIPSHA256":SRC_SHA256,"sourceZIPOriginalBytes":len(source),
        "state":"NC","electionDate":"2024-11-05",
        "precinctCandidateRowsInspected":count,
        "countiesWithVotes":len(counties),
        "countyContestChoiceRows":len(county_rows),
        "uniqueContestChoiceRows":len(contests),
        "judicialContestChoiceRows":len(judges),
        "certifiedCanvassSourceURL":PDF,
        "countyCanvassPDF":PDF_COUNTY,
        "certifiedSpotChecks":check,
        "spotChecksAllMatch":reconciliation_pass,
        "reconciliationInterpretation":"Spot checks for four certified statewide candidate choices; NOT proof every local race, write-in, and precinct is certified.",
        "legalQualityGate":"Do not label complete statewide local-to-certified reconciliation until all contest/choice outcomes are independently verified against authenticated state/county canvasses.",
        "exclusions":"The separate statistically noised NC precinct-sorted result dataset is intentionally excluded because it cannot reproduce official vote totals.",
      }
    }

def main():
    raw=fetch()
    result=summarize(raw)
    DIR.mkdir(parents=True,exist_ok=True)
    (DIR/"original-results-2024.zip").write_bytes(raw)
    for name,body in (("county-choice-totals.json",result["countyRows"]),
                      ("judicial-candidate-totals.json",result["judicialRows"]),
                      ("reconciliation.json",result["metadata"])):
        (DIR/name).write_text(json.dumps(body,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result["metadata"],indent=2))
if __name__=="__main__":
    main()
