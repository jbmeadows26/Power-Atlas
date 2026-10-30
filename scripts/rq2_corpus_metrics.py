"""Rhetorical Q&A corpus QC; human coding required before empirical claims."""
import argparse,csv,json,re
from pathlib import Path
HEDGES={"may","might","could","perhaps","possibly","probably","generally","roughly","likely"}
BINARY={"DIRECT_ANSWER","PARTIAL_ANSWER","PIVOT","ACKNOWLEDGED_UNCERTAINTY","REPETITIVE_SLOGAN",
        "SOURCE_VERIFIED_CONTRADICTION","VERIFIABLE_COMMITMENT","QUESTION_ATTACK",
        "EXPLICIT_REFUSAL","COMPARISON_WITHOUT_RELEVANCE"}
def hedging(text):
    if not isinstance(text,str) or not text.strip():return None
    words=re.findall(r"[a-z']+",text.lower())
    if not words:return None
    return round(sum(w in HEDGES for w in words)/len(words),6)
def fleiss_binary(coders):
    """3 independent binary labels per item; null when chance agreement undefined."""
    if not coders:return None
    if any(len(x)!=3 or any(v not in (0,1) for v in x) for x in coders):
        raise ValueError("Each item needs exactly three binary annotations")
    n=len(coders)
    pp=sum((sum(v)*(sum(v)-1)+(3-sum(v))*(2-sum(v)))/6 for v in coders)/n
    yes=sum(sum(v) for v in coders)/(3*n)
    pe=yes**2+(1-yes)**2
    return None if abs(1-pe)<1e-12 else round((pp-pe)/(1-pe),6)
def analyze(rows):
    results=[]
    for x in rows:
        if not x.get("sourceUrl","").startswith("https://") or not x.get("eventUTC"):
            raise ValueError("Source URL and event date required")
        kind=x.get("unitType")
        if kind not in ("interview_question_answer","standalone_speech","official_press_release","social_post"):
            raise ValueError("Invalid source unit")
        if kind=="interview_question_answer" and not x.get("questionText"):
            raise ValueError("Q/A unit requires question context")
        annotations=x.get("annotations",[])
        if annotations and (len(annotations)!=3 or len(set(a["coderId"] for a in annotations))!=3):
            raise ValueError("Require independent identified triple-coding")
        if annotations and any(set(a.get("codes",{}))!=BINARY or any(v not in (0,1) for v in a["codes"].values()) for a in annotations):
            raise ValueError("Coding categories are fixed and binary")
        if annotations and any(a["codes"]["SOURCE_VERIFIED_CONTRADICTION"] == 1 for a in annotations):
            if not str(x.get("secondPrimarySourceUrl","")).startswith("https://"):
                raise ValueError("A verified contradiction needs two independently identified primary sources")
        results.append({"id":x["id"],"unitType":kind,"sourceUrl":x["sourceUrl"],
            "hedgingDensity":hedging(x.get("answerText") or x.get("text") or ""),
            "annotations":annotations})
    kappas={}
    for code in sorted(BINARY):
        grouped=[[a["codes"][code] for a in r["annotations"]] for r in results if r["annotations"]]
        kappas[code]={"nTripleCoded":len(grouped),"fleissKappa":fleiss_binary(grouped)}
    return {"schema":"power-atlas.rhetoric-corpus-quality.v1","sampled":len(results),
        "tripleCoded":sum(bool(r["annotations"]) for r in results),
        "kappaByCode":kappas,
        "researchStatus":"not_empirically_qualified" if len(results)<1000 or any(v["nTripleCoded"]<1000 or v["fleissKappa"] is None or v["fleissKappa"]<.8 for v in kappas.values()) else "meets_proposed_coding_coverage_threshold_only",
        "warning":"Lexical hedging is not deception. Kappa is reliability, not validity; coding alone cannot prove internal scripting or motives."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    rows=[json.loads(line) for line in a.input.read_text().splitlines() if line.strip()]
    out=analyze(rows)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__":main()
