#!/usr/bin/env python3
"""One-time faithful capture of public Eastern Axis HTML/CSS/JS/JSON for Pages migration."""
import concurrent.futures
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import os

root = pathlib.Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'eastern-axis-migration/static-manifest.json').read_text())
base = manifest['source'].rstrip('/')
target = root / 'eastern-axis-static'
allowed = {'html','css','js','json','svg','txt','xml'}
def get(path):
    safe=pathlib.PurePosixPath(path)
    if safe.is_absolute() or '..' in safe.parts or safe.suffix.lstrip('.').lower() not in allowed:
        raise RuntimeError('Rejected unexpected path: '+path)
    request=urllib.request.Request(base+'/'+urllib.parse.quote(path,safe='/'),headers={'User-Agent':'EasternAxisOwnerMigration/1.0','Accept':'*/*'})
    last=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=25) as response:
                body=response.read(7*1024*1024)
                content_type=response.headers.get('Content-Type','').lower()
                status=response.status
                final=response.url
            if status!=200 or len(body)<5 or len(body)>=7*1024*1024:
                raise RuntimeError(f'Invalid body or HTTP status {status}: {path}')
            suffix=safe.suffix.lower()
            if suffix in ('.js','.css','.json','.svg') and ('text/html' in content_type or body[:200].lstrip().lower().startswith(b'<!doctype html')):
                raise RuntimeError(f'HTML fallback served instead of {suffix}: {path}')
            if urllib.parse.urlparse(final).netloc not in ('eastern-axis-resources-power.vercel.app',):
                raise RuntimeError(f'Unexpected redirect destination: {path}')
            return path,body,content_type
        except Exception as e:
            last=e
            time.sleep(0.5*(attempt+1))
    raise RuntimeError(f'{path}: {last}')
results={}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    future_map={pool.submit(get,path):path for path in manifest['files']}
    for f in concurrent.futures.as_completed(future_map):
        path,body,ctype=f.result()
        results[path]=(body,ctype)
        print(path,len(body),ctype,flush=True)
missing=set(manifest['files'])-set(results)
if missing: raise SystemExit('Missing required public assets: '+str(sorted(missing)))
entries=[]
for path in sorted(results):
    body,ctype=results[path]
    dest=target/path
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(body)
    entries.append({'path':path,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'contentType':ctype})
(target/'_source-manifest.json').write_text(json.dumps({
    'source':base,'sourceDeployment':manifest['capturedFromDeployment'],
    'capturedAtUtc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
    'files':entries},indent=2)+'\n',encoding='utf-8')
print('STATIC_CAPTURE_OK',len(entries),'files',sum(e['bytes'] for e in entries),'bytes',flush=True)
