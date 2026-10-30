"""Audit-safe demonstration of the IDI algebra (not a validated politician rating)."""
from decimal import Decimal,InvalidOperation
import json
from pathlib import Path

WEIGHTS={"W":Decimal("0.25"),"O":Decimal("0.25"),"S":Decimal("0.35"),"C":Decimal("0.15")}
FIELDS=("W","O","S","C")
def bounded(value):
    if value is None:return None
    if isinstance(value,bool):raise ValueError("Boolean is not a normalized score")
    a=value if isinstance(value,list) else [value,value]
    if len(a)!=2:raise ValueError("Expected [lower,upper]")
    try:lo,hi=[Decimal(str(x)) for x in a]
    except (InvalidOperation,TypeError) as exc:raise ValueError("Invalid numeric component") from exc
    if any(not n.is_finite() or n<0 or n>1 for n in (lo,hi)) or lo>hi:
        raise ValueError("Scores must be ordered finite [0,1] intervals")
    return lo,hi

def evaluate(row,kind="synthetic"):
    if kind not in ("synthetic","observed"):raise ValueError("Unknown dataKind")
    fields={k:bounded(row.get(k)) for k in FIELDS}
    unknown=[k for k,x in fields.items() if x is None]
    base={"memberId":row["memberId"],"status":"insufficient_evidence" if unknown else "not_validated_for_public_ranking",
          "missing":unknown,"low":None,"high":None,"point":None}
    if unknown:return base
    if kind=="observed":
        # This project has not validated externally sourced W/O/S/C measurements.
        return base
    w,o,s,c=[fields[k] for k in FIELDS]
    lo=WEIGHTS["W"]*w[0]+WEIGHTS["O"]*o[0]+WEIGHTS["S"]*(1-s[1])+WEIGHTS["C"]*c[0]
    hi=WEIGHTS["W"]*w[1]+WEIGHTS["O"]*o[1]+WEIGHTS["S"]*(1-s[0])+WEIGHTS["C"]*c[1]
    base.update(status="synthetic_calculation_only",low=float(lo),high=float(hi),
                point=float(lo) if lo==hi else None)
    return base

def assess(document):
    if document.get("schema")!="power-atlas.idi-illustration.v1":raise ValueError("Bad schema")
    records=document.get("records")
    if not isinstance(records,list):raise ValueError("Expected records")
    ids=[r.get("memberId") for r in records]
    if len(set(ids))!=len(ids) or any(not isinstance(x,str) or not x for x in ids):
        raise ValueError("Duplicate/invalid identity")
    return {"schema":"power-atlas.idi-results.v1","dataKind":document["dataKind"],
       "publicationStatus":"SYNTHETIC_ONLY_NOT_VALIDATED",
       "weights":{k:str(v) for k,v in WEIGHTS.items()},
       "formula":"0.25 W + 0.25 O + 0.35 (1-S) + 0.15 C",
       "records":[evaluate(r,document["dataKind"]) for r in records]}

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    input_path=root/"data/research/political-authenticity/idi-synthetic.json"
    out=root/"data/research/political-authenticity/idi-synthetic-results.json"
    result=assess(json.loads(input_path.read_text(encoding="utf-8")))
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("synthetic examples:",len(result["records"]))
