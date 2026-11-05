"""Parse a specifically obtained official IRS Form 990 Schedule I XML filing.

This importer does NOT mine Schedule B private donor lists or infer political
donors. Schedule I is an outbound grant ledger; a grant is not a PAC
contribution. Only recipient entries with their own public organization EIN
are retained. No postal addresses, officers, phone, or individuals retained.

Usage (once an independently verified official XML is supplied):
 python -m scripts.parse_irs_schedule_i --file /path/to/IRS_filing.xml \
    --archive-url https://apps.irs.gov/pub/epostcard/990/xml/2025/2025_TEOS_XML_01A.zip \
    --member 202540123456789.xml
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/finance/irs-schedule-i-grants-v1.json"
EIN=re.compile(r"^\d{9}$")
IRS_SOURCE=re.compile(r"^/pub/epostcard/990/xml/20\d{2}/20\d{2}_TEOS_XML_[A-Za-z0-9]+\.zip$")
MEMBER=re.compile(r"^[A-Za-z0-9_-]{5,80}\.xml$")
MAX_BYTES=8_000_000

def local(tag):
    return tag.rsplit("}",1)[-1] if "}" in tag else tag

def descend_text(elem, names):
    if elem is None:return ""
    for item in elem.iter():
        if local(item.tag) in names and item.text and item.text.strip():
            return item.text.strip()
    return ""

def business_name(elem):
    if elem is None:return ""
    for item in elem.iter():
        if local(item.tag) in {"RecipientBusinessName","BusinessName","BusinessNameControlTxt"}:
            return descend_text(item,{"BusinessNameLine1Txt","BusinessNameLine1","BusinessNameControlTxt"})
    return ""

def parse_xml(blob:bytes,archive_url:str,member:str):
    if len(blob)>MAX_BYTES or b"<!DOCTYPE" in blob.upper() or b"<!ENTITY" in blob.upper():
        raise ValueError("Unsafe or oversized IRS XML")
    u=urlsplit(archive_url)
    if u.scheme!="https" or u.hostname!="apps.irs.gov" or not IRS_SOURCE.fullmatch(u.path):
        raise ValueError("Official IRS Form 990 archive URL required")
    if not MEMBER.fullmatch(member):
        raise ValueError("Invalid IRS archive XML member identifier")
    root=ET.fromstring(blob)
    if local(root.tag)!="Return":
        raise ValueError("Expected IRS Form 990 Return XML root")
    headers=[e for e in root if local(e.tag)=="ReturnHeader"]
    if len(headers)!=1:raise ValueError("IRS ReturnHeader missing")
    header=headers[0]
    filer=next((x for x in header.iter() if local(x.tag)=="Filer"),None)
    filer_ein=descend_text(filer,{"EIN"})
    if not EIN.fullmatch(filer_ein):raise ValueError("Filer EIN must be explicit")
    yr=descend_text(header,{"TaxYr","TaxYear"})
    if not re.fullmatch(r"20\d{2}",yr):raise ValueError("IRS tax-year missing")
    filer_name=business_name(filer)
    if not filer_name:raise ValueError("IRS filer legal business name missing")
    schedule=[x for x in root.iter() if local(x.tag)=="IRS990ScheduleI"]
    if not schedule:
        return []
    result=[]
    accepted_groups={"RecipientTable","RecipientInfo","RecipientDetails",
                     "GrantsOtherAsstToOrgInUSGrp","GrantsOtherAsstToOrgInUS",
                     "GrantsOtherAsstToOrgOutsideUSGrp"}
    for sch in schedule:
        for sequence,entry in enumerate(e for e in sch.iter() if local(e.tag) in accepted_groups):
            rec_ein=descend_text(entry,{"RecipientEIN","EINOfRecipient","RecipientEINNumber",
                                           "RecipientEINNum","EIN"})
            rec_name=business_name(entry)
            if not (EIN.fullmatch(rec_ein or "") and rec_name and rec_ein!=filer_ein):
                continue
            cash=descend_text(entry,{"CashGrantAmt","CashGrantAmount",
                                          "CashGrantGivenAmt"})
            try:
                total=Decimal(cash)
                if not total.is_finite() or total<=0 or total>Decimal("1000000000000"):
                    continue
            except (InvalidOperation,ValueError):
                continue
            key="|".join([member,filer_ein,rec_ein,yr,format(total,"f"),str(sequence)])
            result.append({"id":"irs-grant-"+hashlib.sha256(key.encode()).hexdigest()[:20],
                           "from":"irs-ein:"+filer_ein,"to":"irs-ein:"+rec_ein,
                           "fromName":filer_name[:160],"toName":rec_name[:160],
                           "taxYear":int(yr),"amountUSD":float(total),
                           "evidenceType":"irs_schedule_i_outbound_grant_not_campaign_contribution",
                           "source":archive_url,"archiveMember":member,
                           "reviewStatus":"official_irs_xml_unverified_political_purpose"})
    return sorted(result,key=lambda e:e["id"])

def write_records(records):
    if not records:raise ValueError("No qualifying organization-to-organization Schedule I grants; do not publish an empty refresh")
    previous=json.loads(OUT.read_text()) if OUT.exists() else {"records":[]}
    combined={r["id"]:r for r in previous.get("records",[])}
    for r in records:combined[r["id"]]=r
    result={"schema":"power-atlas.irs-schedule-i-grants.v1",
            "dataStatus":"source_attributed_xml_outbound_grants_not_political_contributions",
            "sourceLandingPage":"https://www.irs.gov/charities-non-profits/form-990-series-downloads",
            "originalDonorIdentitiesExtracted":False,
            "validatedCampaignFundingEdges":0,
            "limitations":["Schedule I is public outbound nonprofit grants; not recipient PAC receipts or a complete financial flow.",
                           "Most 501(c)(4)/(c)(6) donor identities cannot be recovered from publicly available Form 990.",
                           "Organization EIN identity is reported by the filer and requires independent confirmation for any cross-dataset join.",
                           "Only verified, targeted official e-filing XML files are processed; no national completeness claimed."],
            "records":sorted(combined.values(),key=lambda x:x["id"])}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--file",required=True,type=Path)
    p.add_argument("--archive-url",required=True)
    p.add_argument("--member",required=True)
    args=p.parse_args()
    if args.file.stat().st_size>MAX_BYTES:raise ValueError("IRS XML exceeds size bound")
    records=parse_xml(args.file.read_bytes(),args.archive_url,args.member)
    print(json.dumps({"newSourceGrants":len(records),
                      "totalPublishedGrants":len(write_records(records)["records"])}))
if __name__=="__main__":main()
