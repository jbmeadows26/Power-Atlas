"""Simplified 119th congressional district geometry from US Census Bureau.

The federal 2025 1:20m cartographic shapefile is public domain/CC0.
Retain only quantized exterior/interior polygon points + GEOID, state FIPS
and district identifier. Do not store the original shapefile archive.
"""
from __future__ import annotations
from io import BytesIO
import json
from pathlib import Path
from urllib.request import Request, urlopen
import zipfile
import shapefile

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/geography/districts-119.geojson'
SOURCE='https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_cd119_20m.zip'
LANDING='https://www.census.gov/geographies/mapping-files/2025/geo/carto-boundary-file.html'
MAX_REMOTE_BYTES=1_500_000
MAX_OUTPUT_BYTES=3_000_000

def compact_geometry(obj):
    # Census simplified polygons; quantization is for map display, not GIS analysis.
    typ=obj.get('type')
    if typ not in ('Polygon','MultiPolygon'):
        raise RuntimeError('Unexpected Census shape type: '+str(typ))
    def round_coordinates(value):
        if isinstance(value,(list,tuple)) and len(value)>=2 and all(isinstance(x,(int,float)) for x in value[:2]):
            return [round(float(value[0]),3),round(float(value[1]),3)]
        if isinstance(value,(list,tuple)):
            return [round_coordinates(x) for x in value]
        raise RuntimeError('Invalid Census coordinate encoding')
    return {'type':typ,'coordinates':round_coordinates(obj['coordinates'])}

def collect():
    request=Request(SOURCE,headers={'User-Agent':'PowerAtlasResearch/1.0 (public Census cartographic data)'})
    with urlopen(request,timeout=30) as response:
        if response.status!=200:
            raise RuntimeError('Official Census geometry returned non-200 response')
        blob=response.read(MAX_REMOTE_BYTES+1)
        if len(blob)>MAX_REMOTE_BYTES:
            raise RuntimeError('Unexpectedly large federal Census geometry file')
    archive=zipfile.ZipFile(BytesIO(blob))
    def entry(ext):
        candidates=[name for name in archive.namelist() if name.lower().endswith(ext)]
        if len(candidates)!=1:
            raise RuntimeError('Expected one .'+ext+' file in archive')
        return BytesIO(archive.read(candidates[0]))
    reader=shapefile.Reader(shp=entry('.shp'),shx=entry('.shx'),dbf=entry('.dbf'))
    headers=[f[0] for f in reader.fields[1:]]
    if not {'GEOID','STATEFP','CD119FP'}.issubset(set(headers)):
        raise RuntimeError('Congressional district metadata columns are missing: '+str(headers))
    features=[]
    seen=set()
    for obj in reader.iterShapeRecords():
        fields=dict(zip(headers,obj.record))
        geoid=str(fields.get('GEOID') or '')
        state=str(fields.get('STATEFP') or '')
        district=str(fields.get('CD119FP') or '')
        if not geoid or not state or not district or geoid in seen:
            raise RuntimeError('Duplicate or incomplete district identity')
        seen.add(geoid)
        features.append({
            'type':'Feature','id':geoid,
            'properties':{'GEOID':geoid,'STATEFP':state,'CD119FP':district},
            'geometry':compact_geometry(obj.shape.__geo_interface__)
        })
    if not 435<=len(features)<=465:
        raise RuntimeError(f'Unexpected Census 119th district count: {len(features)}')
    doc={
        'type':'FeatureCollection',
        'source':SOURCE,
        'catalog':LANDING,
        'edition':'Census 2025 cartographic 119th Congressional Districts 1:20m',
        'license':'CC0-1.0',
        'reviewStatus':'public_cartographic_generalized_map_only',
        'limitations':'Generalized display polygons, not district legal boundary or partisan bias score; source reflects boundaries used for 119th Congress.',
        'features':sorted(features,key=lambda f:f['id'])
    }
    content=json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(content.encode('utf-8'))>MAX_OUTPUT_BYTES:
        raise RuntimeError('Quantized map exceeds small storage target: '+str(len(content.encode())))
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if not DEST.exists() or DEST.read_text(encoding='utf-8')!=content:
        DEST.write_text(content,encoding='utf-8')
    print('Official Census district geometries:',len(features),'bytes:',len(content.encode()))

if __name__=='__main__':
    collect()
