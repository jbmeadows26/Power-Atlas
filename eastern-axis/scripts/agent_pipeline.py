#!/usr/bin/env python3
"""Eastern Axis public-source analyst: publish metadata, retain AI drafts privately."""
import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
TOOLS={
 "gpt-researcher":("GPT Researcher","Research drafts require review; no automated model publication."),
 "local-deep-research":("Local Deep Research","Authenticated LDR server and model required."),
 "openosint":("OpenOSINT","Read-only passive MCP domain queries."),
 "openaleph":("OpenAleph","Read-only investigative entity search."),
 "opencti":("OpenCTI","Read-only cyber-intelligence GraphQL API.")
}
def timestamp(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def https(url):
 p=urlparse(str(url or "").strip())
 if p.scheme!="https" or not p.hostname or p.username or p.password or p.fragment: raise ValueError("HTTPS URL required")
 return p.geturl().rstrip("/")
def fetch(url,token="",body=None,scheme="Bearer"):
 https(url)
 headers={"Accept":"application/json","User-Agent":"EasternAxis-Analyst/1.0"}
 if token:headers["Authorization"]=scheme+" "+token
 if body is not None:headers["Content-Type"]="application/json"
 request=Request(url,data=json.dumps(body).encode() if body is not None else None,headers=headers)
 with urlopen(request,timeout=15) as reply:raw=reply.read(2_000_001)
 if len(raw)>2_000_000:raise ValueError("Oversized source response")
 return json.loads(raw)
def short(value,n=200):return re.sub(r"\s+"," ",str(value or "")).strip()[:n]
def digest(doc):
 if not isinstance(doc,dict) or not isinstance(doc.get("records"),list):raise ValueError("Invalid official feed")
 result=[]
 for record in doc["records"][:300]:
  if not isinstance(record,dict):continue
  try:url=https(record.get("url"))
  except ValueError:continue
  title=short(record.get("title"),160)
  if not title:continue
  mentions=record.get("countryMentions")
  mentions=sorted({v for v in mentions if isinstance(v,str) and re.fullmatch("[A-Z]{2}",v)}) if isinstance(mentions,list) else []
  result.append({"id":short(record.get("id"),100) or hashlib.sha256(url.encode()).hexdigest()[:24],
    "title":title,"publisher":short(record.get("publisher"),70) or "Unknown publisher",
    "url":url,"date":short(record.get("published"),40),"detectedAt":short(record.get("changedAt"),40),
    "countries":mentions,"changeType":record.get("changeType") if record.get("changeType") in ("baseline","new-publication","source-revised") else "baseline"})
  if len(result)>=80:break
 return result
def adapter(key,status="not-configured",detail=None):
 name,description=TOOLS[key]
 obj={"id":key,"name":name,"status":status,"detail":short(detail or description)}
 if status in ("ok","error"):obj["checkedAt"]=timestamp()
 return obj
def openaleph():
 origin=os.getenv("EA_OPENALEPH_URL","").strip()
 if not origin:return adapter("openaleph")
 try:
  doc=fetch(https(origin)+"/api/2/entities?"+urlencode({"q":"sanctions","limit":1}),os.getenv("EA_OPENALEPH_TOKEN",""),scheme="ApiKey")
  if not isinstance(doc,dict) or not isinstance(doc.get("results"),list):raise ValueError("Unknown entity response")
  return adapter("openaleph","ok","Entity-search API responded. No entity matches automatically published.")
 except Exception as e:return adapter("openaleph","error",type(e).__name__+": source/API verification failed.")
def opencti():
 origin=os.getenv("EA_OPENCTI_URL","").strip();token=os.getenv("EA_OPENCTI_TOKEN","")
 if not origin or not token:return adapter("opencti")
 try:
  doc=fetch(https(origin)+"/graphql",token,{"query":"query EasternAxisHealth { __typename }"})
  if not isinstance(doc,dict) or doc.get("errors") or not isinstance(doc.get("data"),dict):raise ValueError("Invalid GraphQL result")
  return adapter("opencti","ok","OpenCTI GraphQL authenticated; reports not ingested before review.")
 except Exception as e:return adapter("opencti","error",type(e).__name__+": API/authentication failure.")
async def openosint():
 domain=os.getenv("EA_OPENOSINT_DOMAIN","").strip().lower()
 if not domain:return adapter("openosint")
 if not re.fullmatch("[a-z0-9.-]{4,190}",domain) or "." not in domain:return adapter("openosint","error","Invalid scoped domain")
 try:
  from mcp import ClientSession,StdioServerParameters
  from mcp.client.stdio import stdio_client
  async with stdio_client(StdioServerParameters(command="uvx",args=["--from","openosint","openosint-mcp"])) as (read,write):
   async with ClientSession(read,write) as session:
    await session.initialize()
    capabilities=await session.list_tools()
    if not any(t.name=="search_dns" for t in capabilities.tools):raise RuntimeError("Passive DNS tool missing")
    answer=await session.call_tool("search_dns",{"domain":domain})
    if answer.isError:raise RuntimeError("Passive DNS lookup failed")
  return adapter("openosint","ok","Passive public-domain DNS investigation completed; raw findings withheld for review.")
 except Exception as e:return adapter("openosint","error",type(e).__name__+": MCP lookup failed.")
async def draft(query,folder):
 folder.mkdir(parents=True,exist_ok=True)
 prompt=short(query,450)+"\nUse original attributable sources, uncertainties and competing hypotheses. UNREVIEWED."
 notes=[]
 if os.getenv("OPENAI_API_KEY") and os.getenv("TAVILY_API_KEY"):
  try:
   from gpt_researcher import GPTResearcher
   agent=GPTResearcher(query=prompt,report_type="research_report")
   await agent.conduct_research()
   report=await agent.write_report()
   (folder/"GPT-Researcher-UNREVIEWED.md").write_text(str(report),encoding="utf-8")
   notes.append("GPT Researcher: draft created")
  except Exception as e:notes.append("GPT Researcher failed: "+type(e).__name__)
 else:notes.append("GPT Researcher: credentials not configured")
 if all(os.getenv(k) for k in ("EA_LDR_URL","EA_LDR_USERNAME","EA_LDR_PASSWORD")):
  try:
   from local_deep_research.api.client import LDRClient
   with LDRClient(base_url=https(os.environ["EA_LDR_URL"])) as client:
    if not client.login(os.environ["EA_LDR_USERNAME"],os.environ["EA_LDR_PASSWORD"]):raise RuntimeError("Authentication failed")
    result=await asyncio.to_thread(client.quick_research,prompt,timeout=180)
   (folder/"Local-Deep-Research-UNREVIEWED.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
   notes.append("Local Deep Research: draft created")
  except Exception as e:notes.append("Local Deep Research failed: "+type(e).__name__)
 else:notes.append("Local Deep Research: authenticated model server not configured")
 (folder/"README.txt").write_text("\n".join(notes)+"\nDO NOT PUBLISH UNREVIEWED AI CLAIMS.\n",encoding="utf-8")
async def run(args):
 snapshot={"schemaVersion":1,"generatedAt":timestamp(),"sourceStatus":"error","method":"Attributable original-source metadata only; model drafts require human review.","connectors":[],"records":[]}
 try:
  origin=https((ROOT/"public-api-origin.txt").read_text())
  if not urlparse(origin).hostname.endswith(".neon.tech"):raise ValueError("Verified Neon endpoint required")
  snapshot["records"]=digest(fetch(origin+"/api/source-monitor"))
  snapshot["sourceStatus"]="ok"
 except Exception as e:print("Official source monitor unavailable: "+type(e).__name__)
 snapshot["connectors"]=[
  adapter("gpt-researcher","not-run" if args.research and os.getenv("OPENAI_API_KEY") else "not-configured"),
  adapter("local-deep-research","not-run" if args.research and os.getenv("EA_LDR_URL") else "not-configured"),
  await openosint(),openaleph(),opencti()]
 if args.research:await draft(args.query,Path(args.drafts))
 out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("Source health:",snapshot["sourceStatus"],"Records:",len(snapshot["records"]))
 for item in snapshot["connectors"]:print(item["id"],item["status"])
 if snapshot["sourceStatus"]!="ok":raise SystemExit("Fail closed: no publish without verified primary source data.")
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--output",default=str(ROOT/"public/analysis/manifest.json"))
 p.add_argument("--research",action="store_true")
 p.add_argument("--query",default="Assess new official defense and cyber publications, including conflicting explanations")
 p.add_argument("--drafts",default="agent-drafts")
 asyncio.run(run(p.parse_args()))
if __name__=="__main__":main()
