"""Locate known civic/political nonprofit EIN filings in the *official IRS* 2025 index.

The output is an allowlisted organization filing CATALOG, not a financial
flow or tax-exempt status determination. Schedule B donor identities are not
collected. Only the 2025 IRS public CSV index is streamed; no other entity
records are retained.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/finance/irs-focused-filing-inventory-2025.json"
INDEX="https://apps.irs.gov/pub/epostcard/990/xml/2025/index_2025.csv"
# EINs independently verified against ProPublica's source-linked 990 profiles.
ORGANIZATIONS={
 "264486735":{"name":"Sixteen Thirty Fund","nonprofitType":"501c4","verificationURL":"https://projects.propublica.org/nonprofits/organizations/264486735"},
 "202303252":{"name":"The Concord Fund","nonprofitType":"501c4","verificationURL":"https://projects.propublica.org/nonprofits/organizations/202303252"},
}
COLUMN_SET={"EIN","RETURN_TYPE","OBJECT_ID","XML_BATCH_ID","TAX_PERIOD","SUB_DATE","TAXPAYER_NAME"}
MAX_INDEX_BYTES=175_000_000
MAX_ROWS=1_500_000
BATCH=re.compile(r"^2025_TEOS_XML_\d{2}[A-Z](?:\.zip)?$",re.I)
OBJECT=re.compile(r"^20\d{16}$")

def clean_ein(value):
    s=re.sub("[^0-9]","",str(value or ""))
    return s.zfill(9) if 1<=len(s)<=9 else ""

def parse_index(rows, columns):
    if not COLUMN_SET.issubset(set(columns)):
        raise ValueError("IRS index required EIN/object/batch columns missing")
    targets={}
    stats={"rowsScanned":0,"officialIndex2025":True}
    for row in rows:
        stats["rowsScanned"]+=1
        if stats["rowsScanned"]>MAX_ROWS:
            raise ValueError("Unexpectedly large IRS index")
        ein=clean_ein(row.get("EIN"))
        if ein not in ORGANIZATIONS or row.get("RETURN_TYPE")!="990":
            continue
        oid=(row.get("OBJECT_ID") or "").strip()
        batch=(row.get("XML_BATCH_ID") or "").strip()
        if not OBJECT.fullmatch(oid) or not BATCH.fullmatch(batch):
            raise ValueError("Selected filing has unsupported IRS object/batch locator")
        archive=batch if batch.lower().endswith(".zip") else batch+".zip"
        tax_period=(row.get("TAX_PERIOD") or "").strip()
        sub_date=(row.get("SUB_DATE") or "").strip()
        if not re.fullmatch(r"(?:\\d{6}|\\d{4}-\\d{2}|\\d{8})",tax_period):
            raise ValueError("Selected IRS filing tax-period format unsupported")
        # Official index returns SUB_DATE in either M/D/YYYY, YYYY-MM-DD
        # or YYYYMMDD notation, depending on release.
        from datetime import datetime
        parsed=None
        for fmt in ("%Y-%m-%d","%m/%d/%Y","%Y%m%d","%Y/%m/%d"):
            try:
                parsed=datetime.strptime(sub_date,fmt).date().isoformat()
                break
            except ValueError:continue
        if parsed is None:
            raise ValueError("Selected IRS filing submission-date format unsupported")
        sub_date=parsed
        item={"filingId":oid,"ein":ein,"organizationName":ORGANIZATIONS[ein]["name"],
              "taxExemptClassificationFromIndependentProfile":ORGANIZATIONS[ein]["nonprofitType"],
              "profileSource":ORGANIZATIONS[ein]["verificationURL"],
              "taxPeriod":tax_period,"submitted":sub_date,
              "returnType":"990",
              "archiveURL":"https://apps.irs.gov/pub/epostcard/990/xml/2025/"+archive,
              "archiveMember":oid+"_public.xml",
              "reviewStatus":"official_irs_index_entry_nonprofit_profile_independently_identified"}
        targets[oid]=item
    return sorted(targets.values(),key=lambda r:(r["ein"],r["submitted"],r["filingId"])),stats

def collect():
    req=urllib.request.Request(INDEX,headers={
        "User-Agent":"PowerAtlasPublicInterestResearch/1.4 nonprofit filing metadata only",
        "Accept":"text/csv"})
    with urllib.request.urlopen(req,timeout=90) as r:
        u=urlsplit(r.geturl())
        if u.scheme!="https" or u.hostname!="apps.irs.gov":
            raise ValueError("IRS index unexpectedly redirected")
        # Bound raw bytes and avoid saving index (which contains other taxpayers).
        raw=r.read(MAX_INDEX_BYTES+1)
    if len(raw)>MAX_INDEX_BYTES:
        raise ValueError("IRS index exceeds no-cost ingestion budget")
    import io
    decoded=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(decoded,newline=""))
    reader.fieldnames=[x.strip().upper() for x in (reader.fieldnames or [])]
    records,stats=parse_index(reader,reader.fieldnames)
    if stats["rowsScanned"]<10000:
        raise ValueError("IRS index unexpectedly incomplete")
    if not records:
        raise ValueError("Target nonprofit EINs not present in the 2025 official index")
    stats["selectedFilings"]=len(records)
    stats["selectedEINs"]=len({r["ein"] for r in records})
    result={"schema":"power-atlas.irs.verified-ein-filing-inventory.2025.v1",
            "sourceURL":INDEX,
            "downloadSHA256":hashlib.sha256(raw).hexdigest(),
            "scope":"2025 IRS-processed Form 990 filings for two source-verified civic 501(c)(4) EINs only",
            "status":"IRS filing inventory only; grant totals and cross-jurisdiction payments not yet extracted",
            "donorsIdentified":0,"campaignFundingTransfersEstablished":0,
            "selection":stats,
            "limitations":["Selected Form 990 filers are not all U.S. political nonprofits.",
                           "IRS filing year 2025 is not the same as the organization's tax year.",
                           "Filing an IRS Form 990 or having a tax-exempt classification is not evidence of wrongdoing.",
                           "A Schedule I grant does not prove the original donor or any political expenditure.",
                           "An IRS batch archive/member locator is independently auditable; extracting grants remains a separate step."],
            "records":records}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result
if __name__=="__main__":
    j=collect();print(json.dumps(j["selection"],indent=2))
