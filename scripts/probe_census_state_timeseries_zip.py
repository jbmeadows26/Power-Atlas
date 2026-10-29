#!/usr/bin/env python3
"""Discover official Census state-finance time-series ZIP schema without an API key.

This is a read-only metadata probe. It does not publish any rows or calculate
spending shares. URL: Census Bureau's publicly indexed data/api_dataset ZIP.
"""
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import Counter
from urllib.parse import urlsplit

URL="https://www2.census.gov/programs-surveys/state/data/api_dataset/GOVSSTATEFINTIMESERIES.zip"
MAX_ZIP_BYTES=8_000_000
MAX_UNCOMPRESSED_BYTES=100_000_000
MAX_FILES=30


def download():
    request=urllib.request.Request(URL,headers={
        "User-Agent":"PowerAtlasResearch/1.0 (official publicly indexed Census data only)",
        "Accept":"application/zip,application/octet-stream",
    })
    with urllib.request.urlopen(request,timeout=60) as response:
        final=response.geturl()
        if urlsplit(final).hostname not in ("www2.census.gov","www.census.gov"):
            raise ValueError("Unexpected source redirect outside Census")
        body=response.read(MAX_ZIP_BYTES+1)
        if len(body)>MAX_ZIP_BYTES:
            raise ValueError("Official source exceeds safe compressed size")
        if not body.startswith(b"PK"):
            raise ValueError("Official response is not ZIP magic")
    return body


def probe(body):
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        members=[i for i in z.infolist() if not i.is_dir()]
        if not members or len(members)>MAX_FILES:
            raise ValueError("Unexpected number of archive members")
        if sum(i.file_size for i in members)>MAX_UNCOMPRESSED_BYTES:
            raise ValueError("Unexpected expanded ZIP size")
        out=[]
        for info in members:
            name=info.filename
            if name.startswith("/") or ".." in name.split("/") or "\\" in name:
                raise ValueError("Unsafe archive member")
            item={"filename":name,"bytes":info.file_size,"compressedBytes":info.compress_size}
            if name.lower().endswith((".csv",".txt",".tsv",".json",".xml",".dat")) and info.file_size<MAX_UNCOMPRESSED_BYTES:
                with z.open(info) as f:
                    txt=io.TextIOWrapper(f,encoding="utf-8-sig",errors="replace",newline="")
                    preview=[next(txt,"")[:420] for _ in range(4)]
                    item["first4Lines"]=preview
                    if name.endswith("_FIELDS.txt"):
                        item["fullFieldsText"]=z.read(info).decode("utf-8-sig",errors="replace")
                    if name.lower().endswith((".csv",".tsv")):
                        delimiter="\t" if name.lower().endswith(".tsv") else ","
                        try:
                            header=next(csv.reader([preview[0]],delimiter=delimiter))
                        except Exception:
                            header=[]
                        item["firstRowFields"]=[h[:75] for h in header[:35]]
            out.append(item)
        dat_name="GOVSSTATEFINTIMESERIES.dat"
        if dat_name not in z.namelist():
            raise ValueError("Required official DAT member missing")
        from collections import Counter
        fields=("YEAR","GEOTYPE","ST","GOVTYPE","CATEGORY","AMOUNT_F")
        counts={k:Counter() for k in fields}
        relevant={}
        sample_states=[]
        nrows=0
        with z.open(dat_name) as stream:
            txt=io.TextIOWrapper(stream,encoding="utf-8-sig",errors="strict",newline="")
            reader=csv.DictReader(txt,delimiter="|")
            if not reader.fieldnames or not reader.fieldnames[0].startswith("#GEO_ID"):
                raise ValueError("Unexpected DAT header; do not guess column offsets")
            reader.fieldnames[0]="GEO_ID"
            for row in reader:
                nrows+=1
                if nrows>1_000_000:
                    raise ValueError("Unexpectedly large Census DAT file")
                for k in fields:
                    counts[k][row[k]]+=1
                label=row["AGG_DESC_LABEL"].strip()
                if any(x in label.lower() for x in ("capital", "expenditure", "construction", "assistance", "subsid", "fixed")):
                    code=row["AGG_DESC"].strip()
                    if code not in relevant:
                        relevant[code]={"code":code,"label":label,"item":row["ITEM_CODE"],"itemLabel":row["ITEM_CODE_LABEL"],
                                        "category":row["CATEGORY"],"categoryLabel":row["CATEGORY_LABEL"],"count":0}
                    relevant[code]["count"]+=1
                if row["ST"] not in ("","00") and len(sample_states)<6:
                    sample_states.append({k:row.get(k) for k in ("GEO_ID","GEO_LABEL","GEOTYPE","ST","AGG_DESC","AGG_DESC_LABEL",
                                             "GOVTYPE","ITEM_CODE","ITEM_CODE_LABEL","CATEGORY","YEAR","AMOUNT","AMOUNT_F")})
        profile={
            "totalDataRows":nrows,
            "years":dict(counts["YEAR"].most_common()),
            "geotypes":counts["GEOTYPE"].most_common(12),
            "governmentTypes":counts["GOVTYPE"].most_common(12),
            "categories":counts["CATEGORY"].most_common(20),
            "amountFlags":counts["AMOUNT_F"].most_common(10),
            "uniqueStateCodes":len([k for k in counts["ST"] if k not in ("","00")]),
            "stateSamples":sample_states,
            "spendingRelatedDefinitions":sorted(relevant.values(),key=lambda x:x["code"])[:125],
            "spendingRelatedCodeCount":len(relevant)
        }
        return {"url":URL,"sha256OriginalZip":hashlib.sha256(body).hexdigest(),
                "compressedBytes":len(body),"members":out,"profile":profile,
                "dataPublished":False,"spendingShares":None,"electionCycleEstimates":None}


def main():
    report=probe(download())
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
