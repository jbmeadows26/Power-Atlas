#!/usr/bin/env python3
"""Fixed two-month Brent benchmark with chronological evaluation and immutable events.
No probability, business price, stockout or causal forecast is produced.
"""
import argparse
import hashlib
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
METHOD = 'brent-3month-mean-h2-v1'
SOURCE = 'https://www.worldbank.org/en/research/commodity-markets'
LIMITATIONS = [
    'Historical evaluation uses the currently retrieved revised series, not archived publication vintages; real-time historical performance is unverified.',
    'Only a short monthly sample is available. Fixed methodology was not tuned on evaluation errors. No claim of beating persistence.',
    'The error range is descriptive historical error dispersion, not a calibrated probability interval; regime shifts can exceed it.',
    'Brent is a global input benchmark, not a supplier quote, delivered fuel price, shortage probability or company cost forecast.',
    'Original publication dates and historical release lags are unavailable in this snapshot; observation month and retrieval time are separate.'
]

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def month_index(period):
    if not isinstance(period,str) or len(period)!=7 or period[4]!='-': raise ValueError('Invalid observation month')
    d=date.fromisoformat(period+'-01')
    return d.year*12+d.month-1

def month_name(index):
    return f'{index//12:04d}-{index%12+1:02d}'

def evaluate(history):
    """Train through origin; evaluate target origin+2, never feed future values."""
    rows=[]
    for origin in range(11,len(history)-2):
        training=history[:origin+1]
        prediction=mean(p['value'] for p in training[-3:])
        actual=history[origin+2]['value']
        baseline=training[-1]['value']
        rows.append({'origin':training[-1]['period'],'target':history[origin+2]['period'],
                     'predicted':prediction,'baseline':baseline,'actual':actual,
                     'absoluteError':abs(actual-prediction),'baselineAbsoluteError':abs(actual-baseline)})
    return rows

def build(snapshot, created, primary=None):
    now=datetime.fromisoformat(created.replace('Z','+00:00'))
    base={'schemaVersion':1,'createdAt':created,'methodologyVersion':METHOD,'target':'World Bank monthly Brent crude oil benchmark',
          'horizonMonths':2,'unit':'$/bbl','limitations':LIMITATIONS,'forecastStatus':'Forecast withheld — insufficient evidence.'}
    try:
        if now.tzinfo is None: raise ValueError('Creation time must be timezone aware')
        retrieved=datetime.fromisoformat(snapshot['checkedAt'].replace('Z','+00:00'))
        if retrieved.tzinfo is None or not 0 <= (now-retrieved).total_seconds() <= 7*86400: raise ValueError('Stale or invalid retrieval')
        metric=next(m for m in snapshot['metrics'] if m['id']=='worldbank-brent')
        if metric['sourceUrl']!=SOURCE or metric['source']!='World Bank Pink Sheet' or metric['unit']!='$/bbl': raise ValueError('Source or units not verified')
        history=metric['history']
        if not isinstance(history,list) or len(history)<36: raise ValueError('At least 36 monthly observations required')
        for i,p in enumerate(history):
            idx=month_index(p['period']);v=p['value']
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0: raise ValueError('Invalid benchmark value')
            if i and idx!=month_index(history[i-1]['period'])+1: raise ValueError('History must be consecutive and unique')
        last=history[-1]
        if last['period']!=metric['period'] or last['value']!=metric['value']: raise ValueError('Current value/history mismatch')
        age=(now.date()-date.fromisoformat(last['period']+'-01')).days
        if not 0 <= age <= 70: raise ValueError('Stale observation')
        target=month_name(month_index(last['period'])+2)
        if month_index(target)<=month_index(now.strftime('%Y-%m')): raise ValueError('Forecast target must be a future calendar month')
        scores=evaluate(history)
        mae=mean(x['absoluteError'] for x in scores);baseline_mae=mean(x['baselineAbsoluteError'] for x in scores)
        prediction=mean(p['value'] for p in history[-3:])
        errors=sorted(x['absoluteError'] for x in scores)
        radius=errors[math.ceil(.8*len(errors))-1]
        source={'publisher':metric['source'],'url':SOURCE,'observationPeriod':last['period'],'retrievedAt':snapshot['checkedAt'],
                'publicationDate':None,'publicationDateLimitation':'Not supplied in collector snapshot','geographicScope':'global','unit':metric['unit']}
        base.update(forecastStatus='Experimental forecast — historically evaluated, prospective performance pending',
                    targetPeriod=target,predicted=prediction,baselinePrediction=last['value'],observationPeriod=last['period'],
                    uncertainty={'method':'80th percentile of historical absolute two-month errors; descriptive, not calibrated','lower':max(0,prediction-radius),'upper':prediction+radius,'radius':radius},
                    evaluation={'observations':len(history),'origins':len(scores),'mae':mae,'persistenceMae':baseline_mae,'beatsPersistence':mae<baseline_mae,'rows':scores},
                    source=source,supportingObservations=history,inputHash=digest(history),
                    drivers=['Last three observed monthly Brent benchmark values'],
                    invalidationConditions=['Missing, stale or revised input history','Structural price regime change','Target month already started before issue'],
                    managementConsideration='For an approved fuel dependency, compare current supplier quotes and contractual pass-through against this public benchmark; do not substitute it for a landed-cost estimate.')
        if primary and primary.get('historyHash')==digest(history):
            base['forecastId']=METHOD+'-'+last['period']+'-'+digest(history)[:12]
            base['primaryVerification']=primary
        else:
            base['forecastStatus']='Forecast withheld — insufficient evidence.'
            base['withheldReason']='Original World Bank workbook has not been independently revalidated for this issue; retained-history evaluation only.'
            for field in ('predicted','baselinePrediction','uncertainty'):
                base.pop(field,None)
    except (KeyError,TypeError,ValueError,StopIteration) as exc:
        base['withheldReason']=str(exc) or 'Required source observation unavailable'
    return base

def append_events(path, report, snapshot):
    """Never rewrite a past issue or outcome. Hash chain detects mutation/reordering."""
    entries=[json.loads(line) for line in path.read_text().splitlines() if line] if path.exists() else []
    previous=None
    for item in entries:
        if item.get('previousHash')!=previous or item.get('eventHash')!=digest({k:v for k,v in item.items() if k!='eventHash'}): raise ValueError('Invalid accountability chain')
        previous=item['eventHash']
    additions=[]
    def add(event):
        nonlocal previous
        event['previousHash']=previous;event['eventHash']=digest(event);previous=event['eventHash'];additions.append(event)
    # Only validated current input may resolve previously issued targets.
    if 'forecastId' in report:
        points={p['period']:p['value'] for p in report['supportingObservations']}
        resolved={e['forecastId'] for e in entries if e['kind']=='outcome'}
        for e in entries:
            if e['kind']=='issued' and e['forecastId'] not in resolved and e['forecast']['targetPeriod'] in points:
                actual=points[e['forecast']['targetPeriod']]
                add({'kind':'outcome','forecastId':e['forecastId'],'recordedAt':report['createdAt'],'observed':actual,
                     'source':report['source'],'absoluteError':abs(actual-e['forecast']['predicted']),
                     'baselineAbsoluteError':abs(actual-e['forecast']['baselinePrediction'])})
        if not any(e.get('forecastId')==report['forecastId'] and e['kind']=='issued' for e in entries):
            add({'kind':'issued','forecastId':report['forecastId'],'forecast':report,'recordedAt':report['createdAt']})
    if additions:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a') as f:
            for item in additions: f.write(json.dumps(item,sort_keys=True,allow_nan=False)+'\n')
    return len(additions)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=ROOT/'eastern-axis/public/analysis/physical-early-warning.json');parser.add_argument('--output',type=Path,default=ROOT/'site/business-intelligence/data/brent-forecast.json');parser.add_argument('--ledger',type=Path,default=ROOT/'eastern-axis/public/analysis/brent-forecast-ledger.jsonl');args=parser.parse_args()
    snapshot=json.loads(args.input.read_text());primary=None
    try:
        from urllib.request import urlopen,Request
        from collect_early_warning import PINK_SHEET_URL,read_pink_sheet
        with urlopen(Request(PINK_SHEET_URL,headers={'User-Agent':'EasternAxis research; public benchmark verification'}),timeout=30) as response:
            raw=response.read(10_000_001)
        if len(raw)>10_000_000: raise ValueError('Oversized original workbook')
        metric=next(m for m in read_pink_sheet(raw) if m['id']=='worldbank-brent')
        primary={'url':PINK_SHEET_URL,'sha256':hashlib.sha256(raw).hexdigest(),'historyHash':digest(metric['history']),'retrievedAt':datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        print('Original source verification unavailable:',type(exc).__name__)
    report=build(snapshot,datetime.now(timezone.utc).isoformat(),primary);append_events(args.ledger,report,snapshot)
    if 'forecastId' in report and args.ledger.exists():
        issued=[json.loads(line) for line in args.ledger.read_text().splitlines() if line]
        report=next(e['forecast'] for e in issued if e['kind']=='issued' and e['forecastId']==report['forecastId'])
    from forecast_governance import assess
    events=[json.loads(line) for line in args.ledger.read_text().splitlines() if line] if args.ledger.exists() else []
    report={**report,'governance':assess(events)}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(report['forecastStatus'])
