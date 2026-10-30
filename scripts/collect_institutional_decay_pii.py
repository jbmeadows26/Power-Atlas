"""Ingest official OECD Public Integrity Indicators SDMX-XML with full provenance.

This is a RAW normalized source extract, not an elite-impunity score. Missing
status strings are preserved, never imputed. No causal inference is performed.
No non-OECD data is silently mixed into an analysis sample.
"""
from __future__ import annotations
import json
import math
import os
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
TRUST=ROOT/"data/institutional-decay/trust-country-waves-2023-2025.json"
OUT=ROOT/"data/institutional-decay/oecd-pii-raw-2020-2025.json"
API="https://sdmx.oecd.org/public/rest/data/OECD.GOV.PSI,DSD_PII@DF_PUBLIC_INTEGRITY,"
ACCEPT="application/vnd.sdmx.structurespecificdata+xml"
MISSING={"","Data pending","Not available","Data not available","Data not provided","Not tracking","Not applicable","Data missing"}


def normalize(raw, series):
    v=raw.get("OBS_VALUE","")
    value=None
    numerator=None
    denominator=None
    fraction=re.fullmatch(r"(\\d+)/(\\d+)",str(v))
    if fraction:
        numerator,denominator=(int(fraction.group(1)),int(fraction.group(2)))
        if denominator==0 or numerator>denominator:
            raise ValueError("Invalid source criteria fraction: "+v)
        value_kind="reported_fraction"
    else:
        try:
            parsed=float(v)
            if math.isfinite(parsed):
                value=parsed
        except (TypeError,ValueError):
            pass
        value_kind=("numeric" if value is not None else
                    "source_missing" if v in MISSING else "unrecognized_text")
    record={
        "countryIso3":series["REF_AREA"],
        "referenceYear":int(raw["TIME_PERIOD"]),
        "measureCode":series["MEASURE"],
        "unitMeasureCode":series.get("UNIT_MEASURE"),
        "frequency":series.get("FREQ"),
        "ddDimension":series.get("DD_DIM"),
        "ddId":series.get("DD_ID"),
        "criteriaCode":raw.get("CRITERIA"),
        "statusCode":raw.get("OBS_STATUS"),
        "unitMultiplier":raw.get("UNIT_MULT"),
        "value":value,
        "valueKind":value_kind,
        "reportedNumerator":numerator,
        "reportedDenominator":denominator,
        "rawObservedValue":v,
    }
    if v in MISSING or value is None:
        record["value"]=None
    return record


def collect():
    trust=json.loads(TRUST.read_text(encoding="utf-8"))
    countries=sorted(r["countryCode"] for r in trust["rows"])
    assert len(countries)==39 and all(re.fullmatch(r"[A-Z]{3}",c) for c in countries)
    url=API+"/"+("+".join(countries))+".A..._T.?startPeriod=2020&endPeriod=2025"
    request=urllib.request.Request(url,headers={"Accept":ACCEPT,"User-Agent":"PowerAtlasPublicEvidenceCollector/1.0"})
    rows=[];active=None;seriesCount=0; seen=set();tagcounts=Counter()
    with urllib.request.urlopen(request,timeout=100) as response:
        if response.status!=200:raise RuntimeError("Source did not respond HTTP200")
        ctype=response.headers.get("Content-Type","")
        if "xml" not in ctype.lower():raise RuntimeError("Unexpected source content type: "+ctype)
        for event,elem in ET.iterparse(response,events=("start","end")):
            tag=elem.tag.rsplit("}",1)[-1]
            if event=="start" and tag=="Series":
                active=dict(elem.attrib);seriesCount+=1
                if "REF_AREA" not in active or "MEASURE" not in active:raise ValueError("Missing official source dimensions")
            elif event=="end" and tag=="Obs":
                if active is None:raise ValueError("Observation without series dimensions")
                record=normalize(dict(elem.attrib),active)
                if record["countryIso3"] not in countries:raise ValueError("Unexpected source country")
                if not 2020<=record["referenceYear"]<=2025:raise ValueError("Unexpected year")
                key=tuple(record[k] for k in ("countryIso3","referenceYear","measureCode","unitMeasureCode","frequency","ddDimension","ddId","criteriaCode"))
                if key in seen:raise ValueError("Duplicate source dimensional key")
                seen.add(key);rows.append(record)
                if len(rows)>100000:raise ValueError("Unbounded source output")
                elem.clear()
            elif event=="end" and tag=="Series":
                active=None
                elem.clear()
    if not rows or not any(r["value"] is not None for r in rows):
        raise ValueError("Source yielded no verified numeric observations")
    rows.sort(key=lambda r:(r["countryIso3"],r["measureCode"],r["referenceYear"],str(r["ddId"]),str(r["criteriaCode"])))
    nums=[r for r in rows if r["value"] is not None]
    fractions=[r for r in rows if r["valueKind"]=="reported_fraction"]
    status_records=[r for r in rows if r["valueKind"]=="source_missing"]
    unexpected=[r for r in rows if r["valueKind"]=="unrecognized_text"]
    labels=Counter(r["rawObservedValue"] for r in status_records)
    byyear=Counter(str(r["referenceYear"]) for r in nums)
    bycountry=Counter(r["countryIso3"] for r in nums)
    output={
        "schema":"power-atlas.institutional-decay.oecd-pii-raw.v1",
        "retrievedUTC":datetime.now(timezone.utc).isoformat(),
        "publisher":"OECD","dataset":"Public Integrity Indicators",
        "sourceApiUrl":url,"sourceAccept":ACCEPT,
        "officialExplorer":"https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.GOV.PSI&df%5Bid%5D=DSD_PII%40DF_PUBLIC_INTEGRITY",
        "reuseNotice":"OECD source attribution required. Consult OECD data terms for redistribution and third-party rights. This extract is a transformed official dataset, not an OECD-endorsed assessment.",
        "researchStatus":"raw_code_level_source_data_not_harmonized_to_trust_or_causally_identified",
        "aggregationRule":"One value per complete source dimensional key, no interpolation or forward-fill",
        "coverage":{
            "requestedCountries":countries,
            "requestedCountryCount":len(countries),
            "countriesWithNumericData":len(bycountry),
            "yearCountsNumeric":dict(sorted(byyear.items())),
            "seriesCount":seriesCount,"totalRecords":len(rows),"numericRecords":len(nums),
            "nonDecimalRecords":len(rows)-len(nums),
            "fractionRecords":len(fractions),
            "missingStatusRecords":len(status_records),
            "unrecognizedTextRecords":len(unexpected),
            "missingReasonCounts":dict(labels),
            "measureCodeCount":len(set(r["measureCode"] for r in rows)),
        },
        "dataQualityWarnings":[
            "Numeric values have official MEASURE and UNIT_MEASURE codes, not yet user-facing labels.",
            "Only documented missing-status tokens such as Data pending are marked source_missing; a fraction such as 3/7 is a reported fraction, not missing.",
            "Reported fractions preserve numerator/denominator without an unjustified percentage conversion; use official unit metadata before harmonizing.",
            "Reference year varies by measurement; OECD survey trust dates cannot be joined by forward-fill.",
            "A measure with criteria denominator or percentage score is not a direct rate of corruption or elite impunity.",
            "Source OBS_STATUS code meaning must be verified from metadata before selecting causal predictors.",
            "This is a code-level raw extract; it is not a complete causally identified accountability panel.",
        ],
        "rows":rows,
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    return output


if __name__=="__main__":
    d=collect()
    print(json.dumps({"status":"raw_source_ingested_not_model_ready","output":str(OUT.relative_to(ROOT)),
                     "coverage":d["coverage"],"firstNumericRows":[r for r in d["rows"] if r["value"] is not None][:3]},indent=2))
