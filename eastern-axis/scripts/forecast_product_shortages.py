#!/usr/bin/env python3
"""Source-dated product shortage pressure scenarios for Eastern Axis.

Forecasts are *conditional screens*, not inventory/stockout estimates or calibrated
shortage probabilities. Prices and broad transit counts cannot establish a stockout.
Never infer product-specific vessel cargo, country of destination, or shortage dates.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, date
import json
from pathlib import Path
import re
from statistics import median
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "public/analysis/physical-early-warning.json"
DEFAULT_OUTPUT = ROOT / "public/analysis/product-shortage-outlook.json"
DEFAULT_INVENTORY = ROOT / "public/analysis/product-inventory-context.json"
PORTWATCH = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
PORTWATCH_HOME = "https://portwatch.imf.org/"
# Commodity names are input proxies, NOT observations of finished-goods inventories.
PRODUCTS = (
    ("fuel", "Transport fuels", "Energy", ("worldbank-brent",), ("hormuz", "suez"), "0–90 days"),
    ("fertilizer", "Agricultural fertilizers", "Agriculture", ("worldbank-urea", "worldbank-dap"), ("hormuz", "suez"), "30–180 days"),
    ("bread", "Wheat-based foods", "Food", ("worldbank-wheat", "fao-cereals"), ("bosporus", "suez"), "30–180 days"),
    ("maize", "Corn and animal feed", "Food", ("worldbank-maize", "fao-cereals"), ("panama", "bosporus"), "30–180 days"),
    ("rice", "Rice-based staples", "Food", ("worldbank-rice", "fao-cereals"), ("malacca", "suez"), "30–180 days"),
    ("cooking-oils", "Cooking oils", "Food", ("worldbank-palm-oil", "fao-oils"), ("malacca", "suez"), "30–180 days"),
    ("meat", "Meat and animal protein", "Food", ("fao-meat", "worldbank-maize"), ("panama", "suez"), "30–180 days"),
    ("dairy", "Dairy products", "Food", ("fao-dairy",), ("suez", "panama"), "30–180 days"),
    ("sugar", "Sugar-containing foods", "Food", ("fao-sugar",), ("suez", "panama"), "30–180 days"),
    ("wiring", "Electrical wiring and equipment", "Industrial", ("worldbank-copper", "worldbank-aluminum"), ("malacca", "suez"), "30–180 days"),
    ("appliances", "Appliances and metal components", "Consumer goods", ("worldbank-copper", "worldbank-aluminum", "worldbank-nickel"), ("malacca", "panama"), "30–180 days"),
    ("batteries", "Battery and energy-storage components", "Industrial", ("worldbank-nickel", "worldbank-copper"), ("malacca", "suez"), "30–180 days"),
    ("semiconductors", "Semiconductors and electronics", "Electronics", (), ("taiwan", "malacca"), "30–180 days"),
    ("medicines", "Essential medicines", "Healthcare", (), ("malacca", "suez"), "30–180 days"),
)
ROUTES = (
    ("hormuz", r"hormuz"),
    ("suez", r"suez"),
    ("malacca", r"malacca"),
    ("panama", r"panama"),
    ("bosporus", r"bospor|bosphor|dardanell"),
    ("taiwan", r"taiwan"),
)
STALE_MONTH_DAYS = 70
STALE_SHIPPING_DAYS = 10


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_period(value: object) -> date | None:
    try:
        raw = str(value or "")
        if re.fullmatch(r"\d{4}-\d{2}", raw):
            raw += "-01"
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def age_days(value: object, today: date) -> int | None:
    parsed = parse_period(value)
    return (today-parsed).days if parsed and parsed <= today else None


def clean_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if result >= 0 and result < 1e13 else None


def commodity_pressure(metric: dict, today: date) -> dict | None:
    if not isinstance(metric, dict) or not str(metric.get("sourceUrl", "")).startswith("https://"):
        return None
    history = []
    for point in metric.get("history", []) if isinstance(metric.get("history"), list) else []:
        if not isinstance(point, dict):
            continue
        period = parse_period(point.get("period"))
        value = clean_number(point.get("value"))
        if period is not None and value is not None and value > 0 and period <= today:
            history.append((period, value))
    history = sorted(dict(history).items())
    period = parse_period(metric.get("period"))
    value = clean_number(metric.get("value"))
    age = age_days(metric.get("period"), today)
    if period is None or value is None or age is None or age > STALE_MONTH_DAYS or len(history) < 12:
        return None
    if history[-1][0] != period or abs(history[-1][1]-value) > max(0.01, value*0.001):
        return None
    recent = [v for _, v in history[-3:]]
    prev = [v for _, v in history[-6:-3]]
    base = median([v for _, v in history[-13:-1]])
    if base <= 0:
        return None
    three_month = (sum(recent)/len(recent)/ (sum(prev)/len(prev))-1)*100 if len(prev)==3 and sum(prev)>0 else 0.0
    annual_median = (value/base-1)*100
    monthly = float(metric.get("changePct", 0)) if isinstance(metric.get("changePct"), (int, float)) else 0
    # A price change is a SCREEN of possible pressure, never proof of scarcity.
    score = min(40,
        (18 if annual_median >= 20 else 9 if annual_median >= 10 else 0)
        + (16 if three_month >= 12 else 8 if three_month >= 6 else 0)
        + (6 if monthly >= 8 else 0))
    return {"id":metric.get("id"),"title":metric.get("label"),"publisher":metric.get("source"),
            "url":metric["sourceUrl"],"period":metric["period"],"value":value,
            "unit":metric.get("unit"),"medianPremiumPct":round(annual_median,1),
            "threeMonthMomentumPct":round(three_month,1),"monthChangePct":round(monthly,1),
            "pressureScore":score,"ageDays":age}


def fetch_portwatch() -> dict:
    """Optional independently dated vessel observations; never fail open on network errors."""
    query = urlencode({"where":"1=1",
                       "outFields":"date,portname,n_total",
                       "orderByFields":"date DESC",
                       "resultRecordCount":"2000","returnGeometry":"false","f":"json"})
    req = Request(PORTWATCH+"?"+query, headers={"Accept":"application/json",
                                              "User-Agent":"EasternAxis/1.0 source-linked research"})
    try:
        with urlopen(req, timeout=18) as response:
            raw = response.read(3_000_001)
        if len(raw) > 3_000_000:
            raise ValueError("Oversized PortWatch payload")
        doc = json.loads(raw)
        if not isinstance(doc, dict) or doc.get("error") or not isinstance(doc.get("features"), list):
            raise ValueError("PortWatch schema not verified")
        return {"status":"observed","features":doc["features"],"sourceUrl":PORTWATCH_HOME}
    except Exception as exc:
        return {"status":"unavailable","features":[],"sourceUrl":PORTWATCH_HOME,
                "detail":type(exc).__name__+" — source request failed; no transit claims published"}


def route_pressure(portwatch: dict, today: date) -> dict:
    features = portwatch.get("features", [])
    if not isinstance(features, list):
        return {}
    grouped: dict[str,dict[date,list[float]]] = {}
    latest = None
    for feature in features:
        attr = feature.get("attributes", {}) if isinstance(feature, dict) else {}
        if not isinstance(attr, dict):
            continue
        day = parse_period(attr.get("date"))
        name = str(attr.get("portname") or "")
        value = clean_number(attr.get("n_total"))
        if day is None or not name or value is None or day > today:
            continue
        latest = max(latest, day) if latest else day
        for route, regex in ROUTES:
            if re.search(regex, name, re.I):
                grouped.setdefault(route, {}).setdefault(day, []).append(value)
                break
    if not latest or (today-latest).days > STALE_SHIPPING_DAYS:
        return {}
    result = {}
    for route, observations in grouped.items():
        recent, prior = [], []
        for day, values in observations.items():
            delta = (latest-day).days
            if 0 <= delta < 7:
                recent.append(sum(values))
            elif 7 <= delta < 14:
                prior.append(sum(values))
        if len(recent) < 5 or len(prior) < 5 or sum(prior) <= 0:
            continue
        pct = (sum(recent)/len(recent)/(sum(prior)/len(prior))-1)*100
        result[route] = {"id":route,"changePct":round(pct,1),"period":latest.isoformat(),
                         "recentDays":len(recent),"baselineDays":len(prior),
                         "publisher":"IMF PortWatch (AIS-derived)","url":PORTWATCH_HOME,
                         "screen":pct <= -15}
    return result


def inventory_signals(inventory: dict | None, today: date) -> tuple[dict, list[dict]]:
    """EIA gasoline is a direct commodity stock; broad Census ratios are context only."""
    if not isinstance(inventory, dict) or inventory.get("schemaVersion") != 1:
        return {}, []
    direct, context = {}, []
    for item in inventory.get("metrics", []) if isinstance(inventory.get("metrics"), list) else []:
        if not isinstance(item, dict): continue
        url = str(item.get("sourceUrl", ""))
        days = age_days(item.get("period"),today)
        if days is None or not url.startswith("https://"): continue
        kind = item.get("kind")
        if kind=="direct-inventory" and item.get("id")=="eia-us-gasoline-stocks" and days<=16:
            week=clean_number(item.get("previous"))
            year=clean_number(item.get("yearAgo"))
            value=clean_number(item.get("value"))
            if not value or not week or not year or item.get("productId")!="fuel":continue
            week_change=round((value/week-1)*100,1)
            annual_change=round((value/year-1)*100,1)
            direct["fuel"]={"kind":"direct-inventory","title":item.get("label"),
              "publisher":item.get("source"),"url":url,"period":item["period"],
              "changePct":week_change,"changeYearPct":annual_change,
              "value":value,"unit":item.get("unit"),"scope":item.get("scope"),
              "stockScreen":week_change<=-3 or annual_change<=-8}
        elif kind=="sector-inventory-ratio" and days<=115:
            value=clean_number(item.get("value"))
            if value is None:continue
            context.append({"kind":"sector-context","title":item.get("label"),
              "publisher":item.get("source"),"url":url,"period":item["period"],
              "value":value,"unit":item.get("unit"),"scope":item.get("scope"),
              "note":"U.S. sector context only; not evidence of product shortages"})
    return direct, context


def forecast(data: dict, portwatch: dict | None = None, *, now: datetime | None = None,
             inventory: dict | None = None) -> dict:
    now = now or utcnow()
    today = now.date()
    if data.get("schemaVersion") != 1 or not isinstance(data.get("metrics"), list):
        raise ValueError("Official measurements are missing or invalid")
    commodities = {}
    for row in data["metrics"]:
        if not isinstance(row, dict):
            continue
        indicator = commodity_pressure(row, today)
        if indicator:
            commodities[str(indicator["id"])] = indicator
    ports = route_pressure(portwatch or {"features":[]}, today)
    inventory_by_product, sector_context = inventory_signals(inventory, today)
    results = []
    for product_id, title, category, commodities_used, corridors, horizon in PRODUCTS:
        inputs = [commodities[k] for k in commodities_used if k in commodities]
        route_rows = [ports[k] for k in corridors if k in ports]
        rising = [m for m in inputs if m["pressureScore"] >= 18]
        strained = [r for r in route_rows if r["screen"]]
        stock = inventory_by_product.get(product_id)
        stock_strain = bool(stock and stock["stockScreen"])
        # Score is transparent triage priority; NOT an estimated shortage probability.
        input_score = max((x["pressureScore"] for x in inputs), default=0)
        transit_score = min(30, len(strained)*15)
        stock_score = 25 if stock_strain else 0
        score = min(100, input_score+transit_score+stock_score)
        coverage = "none" if not inputs and not route_rows and not stock else "partial" if not inputs or not route_rows else "two-channel"
        if stock_strain and (rising or strained):
            status = "cross-source-watch"
        elif stock_strain:
            status = "inventory-watch"
        elif not inputs:
            status = "data-gap" if not strained else "transit-watch"
        elif rising and strained:
            status = "cross-source-watch"
        elif rising:
            status = "input-cost-watch"
        elif strained:
            status = "transit-watch"
        else:
            status = "baseline"
        evidence = ([{"kind":"input-price","title":x["title"],"publisher":x["publisher"],
                      "url":x["url"],"period":x["period"],"changePct":x["monthChangePct"],
                      "baselinePremiumPct":x["medianPremiumPct"],"momentumPct":x["threeMonthMomentumPct"]}
                     for x in inputs]
                    + [{"kind":"corridor-transit","title":x["id"].replace("-"," ").title(),
                        "publisher":x["publisher"],"url":x["url"],"period":x["period"],
                        "changePct":x["changePct"],"recentDays":x["recentDays"],
                        "baselineDays":x["baselineDays"]} for x in route_rows])
        if stock:
            evidence.append({k:v for k,v in stock.items() if k!="stockScreen"})
        signal = " / ".join(filter(None, [
            (str(len(rising))+" rising input-pressure series") if rising else "",
            (str(len(strained))+" strained transit corridors") if strained else "",
            ("Measured EIA gasoline inventory drawdown") if stock_strain else ""
        ])) or "No verified simultaneous price/transit pressure"
        if status == "cross-source-watch":
            interpretation = "Independent pressure indicators warrant investigation; producer-to-retailer availability and deliveries remain unverified."
        elif status == "inventory-watch":
            interpretation = "A measured U.S. fuel inventory decline warrants monitoring; this does not establish retail pump shortages."
        elif status in ("input-cost-watch", "transit-watch"):
            interpretation = "Early input or routing pressure warrants monitoring; no product-level shortage is established."
        elif status == "baseline":
            interpretation = "Available input and transit screens do not establish elevated shortage pressure."
        else:
            interpretation = "Insufficient product-specific evidence for a directional shortage assessment."
        results.append({"id":product_id,"product":title,"category":category,
                        "status":status,"screenScore":score,"scoreType":"uncalibrated-triage-not-probability",
                        "planningWindow":horizon,"horizonType":"planning-scenario-not-predicted-onset",
                        "confidence":"limited","coverage":coverage,"modelReviewed":False,
                        "inventorySeriesAvailable":int(stock is not None),
                        "inventoryStockScreen":stock_strain,
                        "countryScope":"global-input-proxy; destination markets unknown",
                        "confirmedShortage":False,"commandEligible":False,
                        "summary":interpretation,"signal":signal,
                        "inputSeriesAvailable":len(inputs),"inputSeriesExpected":len(commodities_used),
                        "routeSeriesAvailable":len(route_rows),"routeSeriesExpected":len(corridors),
                        "missingEvidence":["Product-specific inventory/stockout observations",
                                           "Orders, demand and manufacturing capacity",
                                           "Verified shipment origin, cargo and destination",
                                           "Importer-level supply dependence"],
                        "evidence":evidence})
    rank = {"cross-source-watch":0,"inventory-watch":1,"input-cost-watch":2,"transit-watch":3,"baseline":4,"data-gap":5}
    results.sort(key=lambda r:(rank.get(r["status"],5),-r["screenScore"],r["id"]))
    return {"schemaVersion":1,"generatedAt":now.isoformat(timespec="seconds").replace("+00:00","Z"),
            "sourceCheckedAt":data.get("checkedAt"),"status":"partial" if not ports else "source-dated",
            "inventoryContext":{"checkedAt":inventory.get("checkedAt") if isinstance(inventory,dict) else None,
                                "directProducts":len(inventory_by_product),
                                "sectorRatios":sector_context,
                                "sources":inventory.get("sources",[]) if isinstance(inventory,dict) else []},
            "analyst":{"mode":"transparent-rules with optional isolated AI review","reviewGate":"A forecast cannot be promoted to Command Center without independently verified product-level inventories and human-approved evidence review",
                       "probabilityCalibration":"unavailable","portwatch":(portwatch or {}).get("status","unavailable")},
            "summary":{"products":len(results),
                       "crossSourceWatch":sum(r["status"]=="cross-source-watch" for r in results),
                       "inputCostWatch":sum(r["status"]=="input-cost-watch" for r in results),
                       "transitWatch":sum(r["status"]=="transit-watch" for r in results),
                       "inventoryWatch":sum(r["inventoryStockScreen"] for r in results),
                       "inventoryFeeds":len(inventory_by_product)+len(sector_context),
                       "dataGaps":sum(r["status"]=="data-gap" for r in results),
                       "commandEligible":0},
            "forecasts":results,
            "limitations":["Proxy commodity prices are not retail product inventories or confirmed shortages.",
                           "PortWatch counts are aggregate AIS vessel estimates, not product-specific shipments or trade partners.",
                           "Forecast windows are planning scenarios, not dated stockout predictions.",
                           "EIA U.S. gasoline stocks are not retail station stocks or foreign-market inventories.",
                           "Census/FRED inventory ratios are sector context, not product-level corroboration.",
                           "No calibrated shortage probabilities, verified stockout data or country-specific product exposure are available.",
                           "Lack of evidence is not evidence of adequate stock."]}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=DEFAULT_INPUT)
    p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    p.add_argument("--portwatch",choices=("fetch","skip"),default="fetch")
    p.add_argument("--inventory",type=Path,default=DEFAULT_INVENTORY)
    args=p.parse_args()
    measurements=json.loads(args.input.read_text(encoding="utf-8"))
    ports=fetch_portwatch() if args.portwatch=="fetch" else {"status":"not-requested","features":[]}
    inventory=json.loads(args.inventory.read_text(encoding="utf-8")) if args.inventory.exists() else None
    report=forecast(measurements, ports,inventory=inventory)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"summary":report["summary"],
                      "portwatch":report["analyst"]["portwatch"]}))


if __name__=="__main__":
    main()
