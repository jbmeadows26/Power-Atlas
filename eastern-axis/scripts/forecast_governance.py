"""Prospective, fixed review gate. Never edits or selectively removes issued events."""
from datetime import datetime
from statistics import mean
POLICY={'version':'brent-prospective-review-v1','registeredAt':'2026-11-27T22:01:34+00:00','minimumDistinctTargets':12,'minimumBaselineImprovement':0.10,'automaticPromotion':False}

def assess(entries):
    issued={e['forecastId']:e for e in entries if e.get('kind')=='issued'}
    targets={}
    for event in entries:
        if event.get('kind')!='outcome' or event.get('forecastId') not in issued: continue
        issue=issued[event['forecastId']]; forecast=issue['forecast']
        # Only forecasts issued after registration, before their target month,
        # count. Repeated forecasts for a target cannot inflate sample size.
        if forecast.get('methodologyVersion')!='brent-3month-mean-h2-v1': continue
        stamp=issue['recordedAt'];target=forecast['targetPeriod']
        if datetime.fromisoformat(stamp.replace('Z','+00:00'))<datetime.fromisoformat(POLICY['registeredAt']) or stamp[:7]>=target: continue
        if target not in targets or stamp<targets[target][0]:targets[target]=(stamp,event)
    rows=[v[1] for _,v in sorted(targets.items())]
    mae=mean(e['absoluteError'] for e in rows) if rows else None
    baseline=mean(e['baselineAbsoluteError'] for e in rows) if rows else None
    improvement=(baseline-mae)/baseline if baseline is not None and baseline>0 else None
    enough=len(rows)>=POLICY['minimumDistinctTargets'];better=improvement is not None and improvement>=POLICY['minimumBaselineImprovement']
    return {'policy':POLICY,'status':'Experimental — not decision-grade','prospectiveTargets':len(rows),'prospectiveMAE':mae,'persistenceMAE':baseline,'baselineImprovement':improvement,'eligibleForIndependentReview':enough and better,'limitations':['At least 12 distinct prospective monthly targets and 10% lower MAE than persistence are required for independent review; these are fixed before qualifying outcomes.','No automatic promotion: release-lag, uncertainty and source-vintage validation plus documented independent methodological review remain required.','Past failed forecasts and historical baseline underperformance remain in the ledger.']}
