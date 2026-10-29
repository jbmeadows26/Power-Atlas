"""Deadline-only, zero-cost, bounded multi-source ingestion supervisor.

Never remove previously persisted source rows after a failed refresh. Report
API success separately from data yield and data persistence. No access bypass.
"""
from __future__ import annotations
from datetime import datetime, timezone, date
from pathlib import Path
import json
import subprocess
import sys
import os
import time

ROOT=Path(__file__).resolve().parents[1]
HEALTH=ROOT/'data/health/ingestion-status.json'
END=date(2026,10,30)
COLLECTORS=[
    ('justice_cases','scripts/collect_doj.py'),
    ('fec_committee_identity','scripts/collect_fec.py'),
    ('fec_committee_totals','scripts/collect_fec_totals.py'),
    ('fec_intercommittee_payments','scripts/collect_fec_transactions.py'),
    ('fec_recipient_aggregates','scripts/collect_fec_recipient_aggregates.py'),
    ('lobbying_disclosures','scripts/collect_lda.py'),
    ('census_state_sources','scripts/collect_states.py'),
    ('house_election_results','scripts/collect_house_results.py'),
    ('house_2024_key_audit','scripts/audit_house_2024.py'),
]
DATA_FILES={
    'justice_cases':'data/batches/doj-auto.json',
    'fec_committee_identity':'data/batches/fec-committees.json',
    'fec_committee_totals':'data/finance/fec-totals.json',
    'fec_intercommittee_payments':'data/finance/fec-disbursements.json',
    'fec_recipient_aggregates':'data/finance/fec-recipient-aggregates.json',
    'lobbying_disclosures':'data/lobbying/lda-filings.json',
    'census_state_sources':'data/geography/states.json',
    'house_election_results':'data/elections/house-districts.json',
    'house_2024_key_audit':'data/health/house-2024-audit.json',
}
SOURCE_ALTERNATIVES={
    'fec_committee_identity':'Existing official FEC candidate-committee bulk crosswalk and committee master index retained; DEMO_KEY quota must reset or a permitted key be configured.',
    'fec_committee_totals':'Official FEC aggregate cycle totals retained from earlier successful queries; no quota circumvention.',
    'fec_intercommittee_payments':'Previously persisted official Schedule B committee-only rows retained; no individual payee data collected.',
    'fec_recipient_aggregates':'Official FEC Schedule B by_recipient_id aggregation avoids individual payee records; existing scoped rows retained.',
    'lobbying_disclosures':'Official Senate LDA issue-text search uses smaller 5/10-row pages after 20-row responses exceeded safety bound; bounded 5xx retry.',
    'house_election_results':'Previously validated MEDSL CC0 election rows retained; Clerk-certified unopposed seat statuses are separate and contain no invented vote totals.',
    'house_2024_key_audit':'Official Census 119th geography compared with 2024 vote rows and Clerk unopposed status-only records.',
}

def persistence(name):
    path=ROOT/DATA_FILES[name]
    if not path.exists():
        return {'persistedRecords':None,'persistenceEvidence':'source file missing'}
    try:
        doc=json.loads(path.read_text(encoding='utf-8'))
        if name=='house_2024_key_audit':
            return {
                'expectedDistrictKeys':doc.get('expectedCensusDistrictKeys'),
                'accountedForDistrictKeys':doc.get('accountedForDistrictKeys'),
                'unresolvedDistrictKeys':doc.get('missingCount'),
                'officialUnopposedStatusOnlyKeys':doc.get('officialUnopposedStatusOnlyKeys')
            }
        records=doc.get('records',doc.get('states'))
        info={'persistedRecords':len(records) if isinstance(records,list) else None}
        if name=='lobbying_disclosures':
            info.update({
                'successfulQueries':doc.get('successfulQueries'),
                'failedQueries':doc.get('failedQueries'),
                'fetchedRowsInBoundedPages':doc.get('fetchedRowsInBoundedPages'),
                'matchedRowsInBoundedPages':doc.get('matchedRowsInBoundedPages'),
                'failedQueryDetails':doc.get('failedQueryDetails',[])
            })
        if name=='house_election_results' and isinstance(records,list):
            info['persisted2024VoteDistrictRows']=sum(x.get('year')==2024 for x in records)
        return info
    except (OSError,ValueError,TypeError) as exc:
        return {'persistedRecords':None,'persistenceEvidence':type(exc).__name__+': '+str(exc)[:120]}

def run():
    today=datetime.now(timezone.utc).date()
    if today>END:
        print('Deadline sprint expired; no collection or data changes.')
        return 0
    previous=json.loads(HEALTH.read_text(encoding='utf-8')) if HEALTH.exists() else {}
    past=previous.get('sourceStatuses',{}) if previous.get('checkedDateUTC')==today.isoformat() else {}
    restricted_today=not os.environ.get('FEC_API_KEY') and any(
        name.startswith('fec_') and '429' in str(status.get('error',''))
        for name,status in past.items())
    restricted_lda_today='429' in str(past.get('lobbying_disclosures',{}).get('error',''))
    report={}
    for name,script in COLLECTORS:
        if name=='fec_committee_identity' and (ROOT/'data/batches/fec-committees.json').exists() and not os.environ.get('FEC_API_KEY'):
            report[name]={'status':'cached','note':'Retained previously indexed official committee identities to conserve DEMO_KEY requests',**persistence(name)}
            continue
        if name=='fec_recipient_aggregates' and (ROOT/DATA_FILES[name]).exists() and not os.environ.get('FEC_API_KEY'):
            info=persistence(name)
            if info.get('persistedRecords',0)>0:
                report[name]={'status':'cached_verified',
                              'note':'Previously collected bounded official FEC recipient-ID aggregates retained to conserve DEMO_KEY quota',
                              **info}
                continue
        if name.startswith('fec_') and restricted_today:
            report[name]={'status':'deferred','note':'DEMO_KEY HTTP 429 observed earlier today; wait for permitted quota reset',**persistence(name)}
            continue
        if name=='lobbying_disclosures' and restricted_lda_today:
            info=persistence(name)
            scoped_complete=(info.get('successfulQueries')==6 and info.get('failedQueries')==0
                             and info.get('persistedRecords',0)>0)
            report[name]={
                'status':'cached_verified' if scoped_complete else 'deferred',
                'note':('All six bounded Senate issue/year queries previously succeeded; preserve indexed filings without repeat calls'
                        if scoped_complete else 'Senate LDA HTTP 429 observed earlier today; wait for permitted quota reset'),
                **info
            }
            continue
        print('Collecting:',name,flush=True)
        result=None
        attempts=0
        for attempt in range(2):
            attempts+=1
            try:
                result=subprocess.run([sys.executable,str(ROOT/script)],
                                      cwd=ROOT,text=True,capture_output=True,
                                      timeout=110,check=False)
                if result.returncode==0:
                    break
                tail=(result.stderr or result.stdout)[-500:].strip()
                transient=any(token in tail for token in (
                    'HTTP 500','HTTP 502','HTTP 503','HTTP 504',
                    'TimeoutError','timed out','ConnectionResetError','URLError'))
                if not transient or attempt:
                    break
                print(name,'temporary failure, one bounded retry:',tail[-180:],flush=True)
                time.sleep(2)
            except subprocess.TimeoutExpired:
                result=None
                if attempt:
                    break
                print(name,'timed out; one bounded retry',flush=True)
                time.sleep(2)
        data=persistence(name)
        if result is not None and result.returncode==0:
            status='success'
            if name=='lobbying_disclosures' and data.get('failedQueries',0):
                status='partial'
            if data.get('persistedRecords')==0:
                status='partial_empty'
            if name=='house_2024_key_audit' and data.get('unresolvedDistrictKeys'):
                status='partial'
            report[name]={'status':status,'attempts':attempts,**data}
            print(name,status,'persisted:',data,flush=True)
        else:
            error=((result.stderr or result.stdout)[-500:].strip()
                   if result is not None else 'collector exceeded 110s timeout twice')
            report[name]={
                'status':'blocked','attempts':attempts,'error':error,
                'workaroundOrPreservation':SOURCE_ALTERNATIVES.get(
                    name,'Prior validated source file preserved; retry transient faults only.'),
                **data
            }
            if name.startswith('fec_') and '429' in error and not os.environ.get('FEC_API_KEY'):
                restricted_today=True
            print(name,'blocked:',error[-300:],flush=True)
    doc={
        'schema':'power-atlas.ingestion-health.v2',
        'checkedDateUTC':today.isoformat(),
        'policy':'zero paid services; no rate, license, access, or auth bypass; preserve prior data',
        'sourceStatuses':report,
        'unresolvedSources':[name for name,status in report.items() if status['status'] not in ('success','cached_verified')],
        'statusMeaning':'success means collector completed; persistedRecords/expectedDistrictKeys describe actual local source yield, not nationwide completeness'
    }
    HEALTH.parent.mkdir(parents=True,exist_ok=True)
    body=json.dumps(doc,indent=2,ensure_ascii=False)+'\n'
    if not HEALTH.exists() or HEALTH.read_text(encoding='utf-8')!=body:
        HEALTH.write_text(body,encoding='utf-8')
    return 0

if __name__=='__main__':
    raise SystemExit(run())
