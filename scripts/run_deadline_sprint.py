"""Deadline-only, no-cost, bounded multi-source collection supervisor.

Record failing sources and their error types; do not delete previously verified
data or mask access controls. The runner stops collecting after October 30, 2026.
"""
from __future__ import annotations
from datetime import datetime, timezone, date
from pathlib import Path
import json
import subprocess
import sys
import os

ROOT=Path(__file__).resolve().parents[1]
HEALTH=ROOT/'data/health/ingestion-status.json'
END=date(2026,10,30)
COLLECTORS=[
    ('justice_cases','scripts/collect_doj.py'),
    ('fec_committee_identity','scripts/collect_fec.py'),
    ('fec_committee_totals','scripts/collect_fec_totals.py'),
    ('fec_intercommittee_payments','scripts/collect_fec_transactions.py'),
    ('lobbying_disclosures','scripts/collect_lda.py'),
    ('census_state_sources','scripts/collect_states.py'),
    ('house_election_results','scripts/collect_house_results.py'),
]

def run():
    today=datetime.now(timezone.utc).date()
    if today>END:
        print('Deadline sprint expired; no collection or data changes.')
        return 0
    report={}
    previous=json.loads(HEALTH.read_text(encoding='utf-8')) if HEALTH.exists() else {}
    past_status=previous.get('sourceStatuses',{}) if previous.get('checkedDateUTC')==today.isoformat() else {}
    restricted_today=not os.environ.get('FEC_API_KEY') and any(
        '429' in str(v.get('error','')) for v in past_status.values())
    for name,script in COLLECTORS:
        if name=='fec_committee_identity' and (ROOT/'data/batches/fec-committees.json').exists() and not os.environ.get('FEC_API_KEY'):
            report[name]={'status':'cached','note':'Existing seven committee IDs retained to conserve free API calls'}
            continue
        if name.startswith('fec_') and restricted_today:
            report[name]={'status':'deferred','note':'DEMO_KEY rate limit encountered today; retry after daily reset, no bypass'}
            continue
        print('Collecting:',name,flush=True)
        try:
            result=subprocess.run([sys.executable,str(ROOT/script)],
                                  cwd=ROOT, text=True, capture_output=True,
                                  timeout=110,check=False)
            if result.returncode==0:
                report[name]={'status':'success'}
                print(name,'succeeded:',result.stdout[-250:].strip(),flush=True)
            else:
                tail=(result.stderr or result.stdout)[-350:].strip()
                report[name]={'status':'blocked','error':tail}
                print(name,'blocked:',tail,flush=True)
        except subprocess.TimeoutExpired:
            report[name]={'status':'blocked','error':'collector exceeded 110s limit'}
    doc={'schema':'power-atlas.ingestion-health.v1',
         'checkedDateUTC':today.isoformat(),
         'policy':'no paid services, no source access bypass, preserve previous data',
         'sourceStatuses':report,
         'unresolvedSources':[name for name,s in report.items() if s['status']!='success']}
    HEALTH.parent.mkdir(parents=True,exist_ok=True)
    body=json.dumps(doc,indent=2,ensure_ascii=False)+'\n'
    if not HEALTH.exists() or HEALTH.read_text(encoding='utf-8')!=body:
        HEALTH.write_text(body,encoding='utf-8')
    return 0

if __name__=='__main__':
    raise SystemExit(run())
