"""Map OECD Public Integrity measure codes to official SDMX English labels.

Never derive an indicator's meaning from its numeric identifier. Pull the
published code list from the source dataflow, preserving missing code labels.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/institutional-decay/oecd-pii-raw-2020-2025.json"
OUT=ROOT/"data/institutional-decay/oecd-pii-measure-labels.json"
SOURCE="https://sdmx.oecd.org/public/rest/dataflow/OECD.GOV.PSI/DSD_PII@DF_PUBLIC_INTEGRITY/?references=all"
ACCEPT="application/vnd.sdmx.structure+xml"


def collect():
    raw=json.loads(RAW.read_text(encoding="utf-8"))
    expected=set(r["measureCode"] for r in raw["rows"])
    labels={}
    cl=None
    code=None
    name=None
    codelists_seen=0
    with urllib.request.urlopen(
       urllib.request.Request(SOURCE,headers={
           "Accept":ACCEPT,"User-Agent":"PowerAtlasEvidenceDictionary/1.0"}),
       timeout=110
    ) as response:
        if response.status!=200 or "xml" not in response.headers.get("Content-Type","").lower():
            raise ValueError("Official DSD metadata unavailable")
        for event, elem in ET.iterparse(response, events=("start","end")):
            tag=elem.tag.rsplit("}",1)[-1]
            if event=="start" and tag=="Codelist":
                cl=elem.attrib.get("id",elem.attrib.get("ID"))
                codelists_seen+=1
            elif event=="start" and tag=="Code" and cl:
                code=elem.attrib.get("id",elem.attrib.get("ID"))
                name=None
            elif event=="end" and tag=="Name" and code and cl:
                lang=elem.attrib.get("{http://www.w3.org/XML/1998/namespace}lang",elem.attrib.get("lang","en"))
                text="".join(elem.itertext()).strip()
                if text and (not name or lang.lower().startswith("en")):
                    name=text
                elem.clear()
            elif event=="end" and tag=="Code" and cl:
                if code in expected and name:
                    labels[code]={"code":code,"englishLabel":name,"codelistId":cl}
                code=None
                name=None
                elem.clear()
            elif event=="end" and tag=="Codelist":
                cl=None
                elem.clear()
    if not labels:
        raise ValueError("No official labels found: inspect OECD dataflow structure")
    missing=sorted(expected-set(labels))
    result={
        "schema":"power-atlas.institutional-decay.oecd-pii-measure-labels.v1",
        "retrievedUTC":datetime.now(timezone.utc).isoformat(),
        "publisher":"OECD","source":SOURCE,
        "rawSourceFile":"data/institutional-decay/oecd-pii-raw-2020-2025.json",
        "status":"fully_labeled" if not missing else "partial_label_coverage",
        "coverage":{"sourceMeasureCodeCount":len(expected),
                    "labeledCount":len(labels),
                    "missingCodeCount":len(missing),
                    "codelistsParsed":codelists_seen},
        "missingCodeIds":missing,
        "measureLabels":[labels[k] for k in sorted(labels)],
        "limitations":["Names are source-provided code metadata, not measures of illegal conduct.",
                       "Labels do not establish predictor construct validity, denominator harmonization, reference-year comparability, or causation.",
                       "Only mapped codes may be presented with these English labels; unmapped codes stay unresolved."]
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    d=collect()
    print(json.dumps({"status":d["status"],"coverage":d["coverage"],"examples":d["measureLabels"][:10],"missingCodeIds":d["missingCodeIds"]},indent=2))
