"""Probe state-published Washington PDC campaign finance summary schema.

Does not publish filer/person-level data because the source records explicit
noncommercial redistribution restrictions on lists of natural persons.
"""
import hashlib,json,urllib.parse,urllib.request
BASE="https://data.wa.gov"
DATASET="3h9x-7bvm"
PUBLISHER="https://www.pdc.wa.gov/political-disclosure-reporting-data/open-data"
def probe():
    url=BASE+f"/resource/{DATASET}.json?"+urllib.parse.urlencode({"$limit":4})
    req=urllib.request.Request(url,headers={"User-Agent":"PowerAtlasResearch/1.0 (source-scope discovery only)","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as r:
        if urllib.parse.urlsplit(r.geturl()).hostname!="data.wa.gov":
            raise ValueError("WA PDC official data host changed")
        raw=r.read(120_001)
    if len(raw)>120_000:raise ValueError("Source probe exceeded cap")
    data=json.loads(raw)
    if not isinstance(data,list) or not data:raise ValueError("Empty PDC data response")
    return {"publisher":PUBLISHER,"dataset":DATASET,"apiURL":url,
      "sourceSHA256":hashlib.sha256(raw).hexdigest(),
      "sampleRows":len(data),
      "schemaFieldsSorted":sorted(set().union(*(set(row.keys()) for row in data))),
      "sampleFieldTypes":{key:sorted(set(type(r[key]).__name__ for r in data if key in r)) for key in data[0].keys()},
      "licensingWarning":"Do not republish PDC lists of individuals; statutory noncommercial release condition requires explicit licensing review before product use.",
      "publicationStatus":"source_structure_only_personal_filer_rows_not_republished"}
if __name__=="__main__":
    print(json.dumps(probe(),indent=2))
