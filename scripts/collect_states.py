"""Compact national Census state index; geometry is linked, never downloaded."""
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/geography/states.json'
URL = 'https://api.census.gov/data/2020/dec/pl?' + urlencode({'get':'NAME','for':'state:*'})
GEOMETRY_BASE = 'https://www2.census.gov/geo/tiger/TIGER2025/CD/'

def collect():
    req = Request(URL, headers={'User-Agent':'PowerAtlas/1.0 (public geography index)'})
    with urlopen(req, timeout=25) as res:
        if res.status != 200:
            raise RuntimeError('Census HTTP error')
        raw = res.read(75001)
        if len(raw)>75000:
            raise ValueError('Census state response unexpectedly large')
    rows = json.loads(raw)
    if not rows or rows[0] != ['NAME','state']:
        raise ValueError('Unexpected Census state schema')
    states = {}
    for name, fips in rows[1:]:
        if not re.fullmatch(r'[0-9]{2}',fips) or not isinstance(name,str):
            raise ValueError('Invalid Census state row')
        states[fips] = {
            'fips':fips, 'name':name,
            'stateSource':URL,
            'districtMapSource': GEOMETRY_BASE + f'tl_2025_{fips}_cd119.zip',
            'congress':'119',
            'geometryStatus':'linked_not_downloaded',
            'sourceAuthority':'US_Census_Bureau'
        }
    if not 50 <= len(states) <= 56:
        raise RuntimeError('Unexpected number of Census state equivalents')
    content = json.dumps({'schema':'power-atlas.states.v1',
                          'note':'Source references only; no district polygons or election metrics ingested',
                          'states':sorted(states.values(),key=lambda x:x['fips'])},
                         ensure_ascii=False,indent=2)+'\n'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8') != content:
        OUT.write_text(content,encoding='utf-8')
    print('Census state/equivalent references:',len(states),'bytes:',len(content.encode()))
if __name__=='__main__':
    collect()
