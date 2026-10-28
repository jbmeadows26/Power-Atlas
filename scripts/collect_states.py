"""Official Census state FIPS index using free keyless Census reference text.
The Census data API now requires an API key; do not bypass that access
control. Use its separately published static geography reference file.
Do not download or commit full shapefiles.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/geography/states.json'
STATE_SOURCE='https://www2.census.gov/geo/docs/reference/state.txt'
GEOMETRY_BASE='https://www2.census.gov/geo/tiger/TIGER2025/CD/'

def collect():
    request=Request(STATE_SOURCE,headers={
        'User-Agent':'PowerAtlasPublicResearch/1.0',
        'Accept':'text/plain'})
    with urlopen(request,timeout=25) as response:
        if response.status!=200:
            raise RuntimeError('Census reference HTTP error')
        text=response.read(30001)
        if len(text)>30000:
            raise RuntimeError('Unexpected Census reference size')
    lines=text.decode('utf-8-sig').splitlines()
    if not lines or lines[0].strip()!='STATE|STUSAB|STATE_NAME|STATENS':
        raise RuntimeError('Unexpected official Census reference headers')
    parsed={}
    for line in lines[1:]:
        columns=line.split('|')
        if len(columns)!=4:
            continue
        fips,abbrev,name,ansi=columns
        if not re.fullmatch(r'[0-9]{2}',fips) or not re.fullmatch(r'[A-Z]{2}',abbrev):
            continue
        # 50 states + DC + Puerto Rico; retain other territories in source registry only.
        if fips in ('60','66','69','74','78'):
            continue
        parsed[fips]={
            'fips':fips,'name':name,'postal':abbrev,
            'stateSource':STATE_SOURCE,
            'districtMapSource':GEOMETRY_BASE+f'tl_2025_{fips}_cd119.zip',
            'congress':'119','geometryStatus':'linked_not_downloaded',
            'sourceAuthority':'US_Census_Bureau',
            'stateCodeStatus':'verified_official_census_keyless_reference'
        }
    if len(parsed)!=52:
        raise RuntimeError(f'Expected 52 states/equivalents; found {len(parsed)}')
    data={'schema':'power-atlas.states.v1',
          'note':'Official keyless Census geography index; no district polygons or election scores downloaded',
          'states':sorted(parsed.values(),key=lambda x:x['fips'])}
    content=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=content:
        OUT.write_text(content,encoding='utf-8')
    print('Validated free official Census state FIPS index:',len(parsed))

if __name__=='__main__':
    collect()
