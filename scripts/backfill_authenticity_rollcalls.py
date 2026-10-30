"""Safely retry only missing official House 2025 roll-call XML records.

The 127/150 partial archive rejects some XML due explicit completeness gates.
This diagnostic preserves typed causes, never fills missing roll calls with
zeros, and only merges newly parsed source records that pass Bioguide checks.
"""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,time
from urllib.error import HTTPError,URLError
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_authenticity_rollcalls import fetch

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/research/political-authenticity/house-rollcalls-2025.json'
AUDIT=ROOT/'data/health/house-roll-2025-backfill.json'
MAX_PER_RUN=23

def collect():
    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    rows={r['rollCall']:r for r in data['records']}
    missing=[n for n in range(1,151) if n not in rows]
    results=[]
    for number in missing[:MAX_PER_RUN]:
        try:
            value=fetch(2025,number,seconds=12)
            if value:
                rows[number]=value
                results.append({'roll':number,'status':'official_XML_parsed','memberVotes':value['memberVotes']})
            else:
                results.append({'roll':number,'status':'source_404_no_imputed_vote'})
        except (HTTPError,URLError,TimeoutError,ValueError) as exc:
            results.append({'roll':number,'status':'rejected_or_unavailable',
                            'errorType':type(exc).__name__,
                            'cause':str(exc)[:180]})
            if isinstance(exc,HTTPError) and exc.code in (401,403,429):
                break
        time.sleep(0.14)
    data['records']=sorted(rows.values(),key=lambda row:row['rollCall'])
    data['retrieved']=len(rows)
    data['missingRollNumbers']=[n for n in range(1,151) if n not in rows]
    data['coverageStatus']='complete_window' if len(rows)==150 else 'partial_window'
    data['status']='official_source_partial_vote_archive' if len(rows)!=150 else 'official_source_complete_bounded_window'
    data['completionNote']='Rejected or unavailable roll calls have no inferred votes; see backfill diagnostics and official source XML.'
    contents=json.dumps(data,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n'
    if not SOURCE.exists() or SOURCE.read_text(encoding='utf-8')!=contents:
        SOURCE.write_text(contents,encoding='utf-8')
    audit={'schema':'power-atlas.official-house-roll-backfill.v1',
           'asOfUTC':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'target':150,'persistedOfficialRollCalls':len(rows),
           'stillMissing':data['missingRollNumbers'],
           'attempts':results,
           'interpretation':'Strict XML parsing rejection is distinct from a nonexistent vote and cannot be set to zero.'}
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    AUDIT.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Verified official House rolls:',len(rows),'of 150','backfill attempts:',len(results))
if __name__=='__main__':
    collect()
