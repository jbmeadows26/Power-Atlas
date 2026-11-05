"""Bounded live IRS Schedule I grant pilot from verified official 2025 e-file ZIPs.

Downloads only IRS ZIP batches named by the pre-reviewed EIN index. Public
outbound organization grants with explicit recipient EINs are retained.
No Schedule B or private donors; no inference that grants fund PAC activity.
"""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from scripts import parse_irs_schedule_i as parser

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"data/finance/irs-focused-filing-inventory-2025.json"
ALLOWED_EINS={"264486735"}  # initial pilot: Sixteen Thirty Fund only
MAX_ARCHIVE_BYTES=750_000_000
MAX_XML_BYTES=parser.MAX_BYTES
MAX_TOTAL_GRANTS=2500

def check_filing(row):
    if row.get("ein") not in ALLOWED_EINS:
        raise ValueError("IRS pilot limited to source-verified EIN")
    url=row.get("archiveURL","")
    member=row.get("archiveMember","")
    u=urlsplit(url)
    if u.hostname!="apps.irs.gov" or u.scheme!="https" or not parser.IRS_SOURCE.fullmatch(u.path):
        raise ValueError("IRS archive URL must match official indexed source")
    if not parser.MEMBER.fullmatch(member) or row.get("filingId","")+"_public.xml"!=member:
        raise ValueError("Selected IRS archive member must match indexed filing ID")
    if row.get("returnType")!="990" or row.get("reviewStatus")!="official_irs_index_entry_nonprofit_profile_independently_identified":
        raise ValueError("Selected IRS filing not verified")
    return url,member

def download(url, path):
    req=urllib.request.Request(url,headers={
        "Accept":"application/zip",
        "User-Agent":"PowerAtlasResearch/1.5 public IRS Form990 Schedule I EIN-only civic grants"
    })
    size=0
    digest=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=120) as response, path.open("wb") as dest:
        u=urlsplit(response.geturl())
        host=(u.hostname or "").lower()
        allowed=(u.scheme=="https" and
                 (host in {"apps.irs.gov","www.irs.gov","s3.amazonaws.com"}
                  or host.endswith(".amazonaws.com") or host.endswith(".cloudfront.net")))
        if not allowed:
            raise ValueError("IRS official archive redirected to unexpected host")
        while True:
            part=response.read(1024*1024)
            if not part:
                break
            size+=len(part)
            if size>MAX_ARCHIVE_BYTES:
                raise ValueError("IRS batch ZIP exceeds free-run bound")
            digest.update(part)
            dest.write(part)
    if not zipfile.is_zipfile(path):
        raise ValueError("Official IRS batch response was not a ZIP")
    return {"archiveSHA256":digest.hexdigest(),"archiveBytes":size}

def read_target_xml(path,member):
    with zipfile.ZipFile(path) as z:
        names=[v for v in z.infolist() if not v.is_dir() and v.filename.split("/")[-1]==member]
        if len(names)!=1:
            raise ValueError("Indexed IRS XML filing missing or duplicated in official batch")
        info=names[0]
        if info.file_size>MAX_XML_BYTES:
            raise ValueError("Target IRS return exceeds safe XML size")
        with z.open(info) as f:
            blob=f.read(MAX_XML_BYTES+1)
        if len(blob)>MAX_XML_BYTES:
            raise ValueError("Target IRS return read exceeds safe XML size")
        return blob

def collect():
    index=json.loads(INDEX.read_text(encoding="utf-8"))
    if index.get("schema")!="power-atlas.irs.verified-ein-filing-inventory.2025.v1":
        raise ValueError("Source-verified EIN index unavailable")
    filings=[r for r in index.get("records",[]) if r.get("ein") in ALLOWED_EINS]
    if len(filings)!=1:
        raise ValueError("Expected exactly one official 2025 Sixteen Thirty Fund filing")
    row=filings[0]
    url,member=check_filing(row)
    with tempfile.TemporaryDirectory(prefix="poweratlas-irs-") as temp:
        zip_path=Path(temp)/"irs-target-batch.zip"
        archive_meta=download(url,zip_path)
        xml=read_target_xml(zip_path,member)
    if hashlib.sha256(xml).hexdigest()==hashlib.sha256(b"").hexdigest():
        raise ValueError("IRS return unexpectedly blank")
    grants=parser.parse_xml(xml,url,member)
    grants=[g for g in grants if g["from"]=="irs-ein:"+row["ein"]]
    if not 1<=len(grants)<=MAX_TOTAL_GRANTS:
        raise ValueError("IRS EIN-identified Schedule I grants unavailable / unusually numerous")
    xml_sha=hashlib.sha256(xml).hexdigest()
    for grant in grants:
        grant["sourceArchiveSHA256"]=archive_meta["archiveSHA256"]
        grant["sourceFilingXMLSHA256"]=xml_sha
        grant["officialIRSObjectID"]=row["filingId"]
    result=parser.write_records(grants)
    print(json.dumps({
        "filedByEIN":row["ein"],"taxPeriod":row["taxPeriod"],"qualifyingEINGrants":len(grants),
        "archiveBytes":archive_meta["archiveBytes"],"archiveSHA256":archive_meta["archiveSHA256"],
        "sourceLink":url,"publishedRecords":len(result["records"]),
        "campaignFundingTransfersEstablished":result["validatedCampaignFundingEdges"]
    },indent=2))
    return result

if __name__=="__main__":
    collect()
