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
            if name.lower().endswith((".csv",".txt",".tsv",".json",".xml")) and info.file_size<MAX_UNCOMPRESSED_BYTES:
                with z.open(info) as f:
                    txt=io.TextIOWrapper(f,encoding="utf-8-sig",errors="replace",newline="")
                    preview=[next(txt,"")[:420] for _ in range(4)]
                    item["first4Lines"]=preview
                    if name.lower().endswith((".csv",".tsv")):
                        delimiter="\t" if name.lower().endswith(".tsv") else ","
                        try:
                            header=next(csv.reader([preview[0]],delimiter=delimiter))
                        except Exception:
                            header=[]
                        item["firstRowFields"]=[h[:75] for h in header[:35]]
            out.append(item)
        return {"url":URL,"sha256OriginalZip":hashlib.sha256(body).hexdigest(),
                "compressedBytes":len(body),"members":out,
                "dataPublished":False,"spendingShares":None,"electionCycleEstimates":None}


def main():
    report=probe(download())
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
