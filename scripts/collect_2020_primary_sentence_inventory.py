#!/usr/bin/env python3
"""Build source-linked, copyright-minimizing 2020 campaign TEXT SENTENCE census.

Not a pledge denominator. Every sentence in five selected primary documents
is indexed by position, hash, length and a nonbinding future-tense heuristic.
An independently coded inclusion/exclusion decision is required for EVERY
sentence and compound clause before a complete promise denominator exists.

Only hashes, offsets and official source URLs are persisted; source text is
fetched on demand from its original location and never bulk republished.
"""
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"data/promises"
OUT=P/"primary-2020-sentence-inventory"
MANIFEST=P/"adjudication-2020-template.json"
BASE="https://www.presidency.ucsb.edu"
MAX_PAGE_BYTES=3_000_000
SENTENCE_SPLIT=re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9“\"'])")
FUTURE_SIGNAL=re.compile(
    r"\b(?:we|democrats|republicans|i|our administration|biden|trump)\s+"
    r"(?:will|shall|pledge|promise|commit)\b|\b(?:will|shall|pledge|promise|commitment to)\b",
    re.I
)
CONTENT_SELECTORS=[
    ".field-docs-content",
    ".field--name-field-docs-content",
    ".field--name-body",
    ".document-content",
    ".content .field-docs-content",
    "article",
    "main",
]
MINIMUM_WORDS={
    "party_platform":1000,
    "platform_resolution":40,
    "nomination_acceptance_speech":700,
    "campaign_policy_release":250,
}
def normalized(text):
    return " ".join(unicodedata.normalize("NFKC",text).split())

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def request_doc(url):
    domain=urlsplit(url)
    if domain.scheme!="https" or domain.hostname!="www.presidency.ucsb.edu":
        raise ValueError("Only explicitly reviewed official archive host permitted")
    req=urllib.request.Request(url,headers={
        "Accept":"text/html","User-Agent":"PowerAtlasAcademicEvidenceAudit/1.0 (source-attributed pledge corpus inventory)",
    })
    err=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=35) as response:
                if urlsplit(response.geturl()).hostname!="www.presidency.ucsb.edu":
                    raise ValueError("Archive redirect to unreviewed host")
                raw=response.read(MAX_PAGE_BYTES+1)
            if len(raw)>MAX_PAGE_BYTES:
                raise ValueError("Archived source too large to bound")
            return raw
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            err=e
            if attempt<2:time.sleep(1+attempt)
    raise ValueError("Source not retrievable (do not assume missing sentences): "+url+" "+str(err))

def select_content(html, doc_id, kind):
    soup=BeautifulSoup(html,"html.parser")
    for tag in soup.select("script,style,nav,footer,header,aside"):
        tag.decompose()
    candidates=[]
    for selector in CONTENT_SELECTORS:
        for tag in soup.select(selector):
            paragraphs=[normalized(p.get_text(" ",strip=True)) for p in tag.find_all("p")]
            paragraphs=[p for p in paragraphs if p]
            if not paragraphs:
                paragraphs=[normalized(tag.get_text(" ",strip=True))]
            total=sum(len(p.split()) for p in paragraphs)
            # Fallback <main> can include unrelated UI; prefer specific nested selector
            if total>=MINIMUM_WORDS[kind]:
                candidates.append((selector,total,paragraphs))
        if candidates:
            best=max(candidates,key=lambda item:item[1])
            return best[2],best[0],best[1]
    raise ValueError(f"{doc_id}: no reviewed source-content selector meets minimal document text length")

def index_source(src,raw):
    decoded=raw.decode("utf-8",errors="strict")
    pars,selector,total=select_content(decoded,src["id"],src["type"])
    entries=[]
    for pindex,p in enumerate(pars,1):
        fragments=[normalized(s) for s in SENTENCE_SPLIT.split(p) if normalized(s)]
        for sindex,s in enumerate(fragments,1):
            entries.append({
                "id":src["id"]+f"-P{pindex:04d}-S{sindex:03d}",
                "paragraphIndex":pindex,"sentenceIndex":sindex,
                "sentenceSHA256":sha(s),
                "sourceCharLength":len(s),
                "sourceWordCount":len(s.split()),
                "provisionalFutureTenseCue":bool(FUTURE_SIGNAL.search(s)),
                "verifiedAtomicPledge":None,
                "independentReviewerCount":0,
                "pledgeInclusionStatus":"not_reviewed",
                "humanAdjudicationRequired":True,
            })
    if len(entries)<10:raise ValueError("Incomplete sentence extraction")
    return {
      "schema":"power-atlas.primary-source-sentence-index.v1",
      "publicationStatus":"machine_indexed_primary_text_no_pledge_denominator",
      "sourceId":src["id"],"sourceType":src["type"],"campaignSide":src["side"],
      "sourceURL":src["url"],"sourceDate":src["date"],
      "originalHtmlSHA256":hashlib.sha256(raw).hexdigest(),
      "selectedSelector":selector,"sourceWordsExtracted":total,
      "sourceParagraphCount":len(pars),"indexedSentenceCount":len(entries),
      "heuristicFutureTenseCues":sum(x["provisionalFutureTenseCue"] for x in entries),
      "reviewedPledgeSentences":0,"verifiedAtomicPledges":None,
      "rights":"Only positional metadata and SHA256s persisted; original text remains on archive publisher's site.",
      "warning":"Completeness applies only to this version of one selected document's extracted sentences. Future-tense cues are NOT verified campaign pledges. No comprehensive campaign source inventory and no independent adjudication.",
      "sentences":entries,
    }

def build():
    # Use current authoritative source-manifest builder in branch CI. The
    # persisted JSON manifest can still reflect the previous version until
    # main-branch publication catches up.
    from scripts.prepare_pledge_adjudication import make as make_manifest
    d=make_manifest()
    sources=d.get("knownPrimaryDocuments",[])
    if len(sources)!=6 or d["sourceCollectionRule"]["fullDenominatorFrozen"] is not False:
        raise ValueError("Unexpected campaign source scope; fresh manual review necessary")
    if len({s["id"] for s in sources})!=6:
        raise ValueError("Duplicate campaign source documents")
    documents=[]
    for src in sources:
        raw=request_doc(src["url"])
        obj=index_source(src,raw)
        documents.append(obj)
        print(src["id"],obj["sourceParagraphCount"],obj["indexedSentenceCount"],
              obj["heuristicFutureTenseCues"],obj["selectedSelector"],flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    for d in documents:
        path=OUT/(d["sourceId"]+".json")
        b=json.dumps(d,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
        if not path.exists() or path.read_text(encoding="utf-8")!=b:
            path.write_text(b,encoding="utf-8")
    return {
      "schema":"power-atlas.campaign-source-sentence-index-summary.v1",
      "asOf":"2026-10-30",
      "status":"selected_primary_documents_machine_indexed_only_no_exhaustive_pledge_denominator",
      "documentsRequested":len(documents),"documentsIndexed":len(documents),
      "sourceScopeComplete":False,
      "independentlyAdjudicatedPledgeDenominator":None,
      "independentlyAdjudicatedPledges":0,
      "sourceSentenceTotal":sum(d["indexedSentenceCount"] for d in documents),
      "futureTenseCueTotal":sum(d["heuristicFutureTenseCues"] for d in documents),
      "documents":[{
        "id":d["sourceId"],"date":d["sourceDate"],"url":d["sourceURL"],
        "originalHtmlSHA256":d["originalHtmlSHA256"],
        "sourceWordCount":d["sourceWordsExtracted"],
        "paragraphCount":d["sourceParagraphCount"],
        "sentenceCount":d["indexedSentenceCount"],
        "futureCueCount":d["heuristicFutureTenseCues"],
        "path":f"data/promises/primary-2020-sentence-inventory/{d['sourceId']}.json"
      } for d in documents],
      "warning":"No full promise denominator: only six selected originals (including a historical 2016 platform reaffirmed in 2020), with heuristic candidate tags and zero independent human inclusion decisions. Do not infer a fulfillment percentage."
    }

def main():
    summary=build()
    target=OUT/"index.json"
    result=json.dumps(summary,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if not target.exists() or target.read_text(encoding="utf-8")!=result:
        target.write_text(result,encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
