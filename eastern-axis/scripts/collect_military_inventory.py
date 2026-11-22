#!/usr/bin/env python3
"""Enrich military inventory with dated historical WDI observations."""
import json, math, os, pathlib, tempfile, urllib.request
from datetime import datetime, timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"public"/"analysis"/"military-inventory.json"
SERIES={
 "MS.MIL.TOTL.P1":("Personnel","Armed forces personnel (historical)","people","IISS via World Bank WDI"),
 "MS.MIL.XPND.CD":("Spending","Annual military expenditure (current US$)","USD","SIPRI via World Bank WDI")
}
def fetch_json(url):
 request=urllib.request.Request(url,headers={"User-Agent":"EasternAxisOSINT/1.0","Accept":"application/json"})
 with urllib.request.urlopen(request,timeout=25) as response:
  blob=response.read(12_000_001)
 if len(blob)>12_000_000: raise ValueError("Response exceeded size cap")
 return json.loads(blob)

def country_map(rows):
 if not isinstance(rows,list) or len(rows)!=2 or not isinstance(rows[1],list): raise ValueError("Bad country response")
 return {row["id"]:row["iso2Code"] for row in rows[1] if isinstance(row,dict) and len(str(row.get("iso2Code","")))==2 and row.get("region",{}).get("id")!="NA"}

def latest_observations(rows,countries,series):
 if not isinstance(rows,list) or len(rows)!=2 or not isinstance(rows[1],list): raise ValueError("Bad series response")
 result={}
 for item in rows[1]:
  if not isinstance(item,dict): continue
  iso2=countries.get(item.get("countryiso3code"))
  year=str(item.get("date",""))
  value=item.get("value")
  if not iso2 or not year.isdigit() or int(year)<2015 or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0: continue
  if series=="MS.MIL.TOTL.P1" and value!=int(value): continue
  if iso2 not in result or int(year)>int(result[iso2]["date"]): result[iso2]=item
 return result

def make_entries(series,observations):
 category,name,unit,publisher=SERIES[series]
 records=[]
 for code,item in sorted(observations.items()):
  year=int(item["date"]); amount=float(item["value"])
  if category=="Personnel":
   amount=int(amount); qty=format(amount,","); status="historical-active-personnel"
   detail=f"Historical {year} estimate of active-duty personnel; excludes reserves and is NOT a current 2026 force count."
  else:
   qty="$"+(f"{amount/1e9:,.2f}B" if amount>=1e9 else f"{amount/1e6:,.1f}M")
   status="annual-spending"
   detail=f"Nominal military spending in {year}. This is not a count of equipment or procurement orders."
  records.append({
   "id":"wdi-"+series.replace(".","-")+"-"+code,"code":code,"category":category,
   "name":name,"quantity":qty,"value":amount,"unit":unit,"published":str(year),
   "publisher":publisher,"url":"https://data.worldbank.org/indicator/"+series+"?locations="+code,
   "basis":"Historic WDI/IISS estimate" if category=="Personnel" else "SIPRI/WDI annual observation",
   "detail":detail,"status":status,"estimate":category=="Personnel","observationYear":year
  })
 return records

def main():
 data=json.loads(OUT.read_text(encoding="utf-8"))
 data["assets"]=[item for item in data["assets"] if not item["id"].startswith("wdi-")]
 health={}
 try: countries=country_map(fetch_json("https://api.worldbank.org/v2/country?format=json&per_page=400"))
 except Exception as exc:
  countries={}
  health["countryCrosswalk"]={"state":"unavailable","error":str(exc)[:130]}
 for series in SERIES:
  try:
   if not countries: raise RuntimeError("Country crosswalk unavailable")
   url="https://api.worldbank.org/v2/country/all/indicator/"+series+"?format=json&date=2015:2026&per_page=5000"
   records=latest_observations(fetch_json(url),countries,series)
   if len(records)<25: raise ValueError("Unexpectedly few countries: "+str(len(records)))
   data["assets"].extend(make_entries(series,records))
   health[series]={"state":"ok","countries":len(records)}
  except Exception as exc:
   health[series]={"state":"unavailable","error":str(exc)[:130]}
 data["generatedAt"]=datetime.now(timezone.utc).date().isoformat()
 data["collectionHealth"]={"worldBank":health,"note":"WDI active personnel is historical; spending is not equipment."}
 ids=set()
 for item in data["assets"]:
  assert item["id"] not in ids and len(item["code"])==2
  assert item["url"].startswith("https://") and item["published"]
  assert isinstance(item["value"],(int,float)) and math.isfinite(item["value"]) and item["value"]>=0
  ids.add(item["id"])
 with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=OUT.parent,delete=False) as temp:
  json.dump(data,temp,indent=2,ensure_ascii=False)
  temp.write("\n")
  tmp=temp.name
 os.replace(tmp,OUT)
 print("Military inventory: "+str(len(ids))+" dated estimates; World Bank health: "+str(health))

if __name__=="__main__":main()
