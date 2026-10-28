"""Bounded, deterministic DOJ Section 2 index discovery. No AI, raw page retention, or paid APIs."""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError
from pathlib import Path
import json
import re
import hashlib

SOURCE = 'https://www.justice.gov/crt/cases-raising-claims-under-section-2-voting-rights-act-0'
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data' / 'batches' / 'doj-auto.json'
STATE_NAMES = {
    'TX': 'Texas', 'GA': 'Georgia', 'TN': 'Tennessee', 'PA': 'Pennsylvania',
    'LA': 'Louisiana', 'MI': 'Michigan', 'NC': 'North Carolina', 'FL': 'Florida',
    'OH': 'Ohio', 'NJ': 'New Jersey', 'NY': 'New York', 'SC': 'South Carolina',
    'SD': 'South Dakota',
}

class Blocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.level = 0
        self.parts = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'h2', 'h3', 'h4', 'li'):
            if self.level == 0:
                self.parts = []
            self.level += 1
    def handle_endtag(self, tag):
        if tag in ('p', 'h2', 'h3', 'h4', 'li') and self.level:
            self.level -= 1
            if not self.level:
                self.blocks.append(' '.join(''.join(self.parts).split()))
                self.parts = []
    def handle_data(self, data):
        if self.level:
            self.parts.append(data)

def collect():
    req = Request(SOURCE, headers={'User-Agent': 'PowerAtlasPublicResearch/1.0 (source indexing only)'})
    with urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError('DOJ returned non-200 response')
        page = response.read(650001)
        if len(page) > 650000:
            raise RuntimeError('DOJ page exceeds bounded maximum; no changes written')
        content_type = response.headers.get('Content-Type','')
        if 'html' not in content_type:
            raise RuntimeError('Unexpected content type')
    parser = Blocks()
    parser.feed(page.decode('utf-8', errors='replace'))
    found = {}
    pattern = re.compile(r'^(United States v\.\s+.{3,115}?)\s*\(([^)]*?\b(?:19|20)\d{2})\)')
    for block in parser.blocks:
        match = pattern.search(block)
        if not match:
            continue
        title, court_year = match.groups()
        year_match = re.search(r'((?:19|20)\d{2})',court_year)
        if not year_match:
            continue
        year = int(year_match.group(1))
        if year < 2000:
            continue
        state_code = re.search(r',\s*([A-Z]{2})$', title)
        state = STATE_NAMES.get(state_code.group(1), '') if state_code else ''
        canonical = re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')[:85]
        key = 'doj-index-'+hashlib.sha256((canonical+'-'+str(year)).encode()).hexdigest()[:14]
        found[key] = {
            'id': key,
            'title': title[:130],
            'state': state,
            'date': str(year),
            'source': SOURCE,
            'status': 'official_source_indexed_unreviewed',
            'claimScope': 'DOJ Section 2 case index listing; filing outcome not verified'
        }
    if not 4 <= len(found) <= 100:
        raise RuntimeError('Unexpected DOJ extraction count: '+str(len(found))+'; previous data kept')
    data = {'batch':'doj-auto-v1','records':sorted(found.values(),key=lambda x:x['id'])}
    proposed = json.dumps(data,indent=2,ensure_ascii=False)+'\n'
    previous = DEST.read_text(encoding='utf-8') if DEST.exists() else None
    if proposed != previous:
        DEST.parent.mkdir(parents=True,exist_ok=True)
        DEST.write_text(proposed,encoding='utf-8')
    print('DOJ index entries:',len(found),'changed:',proposed!=previous,'bytes:',len(proposed.encode()))
if __name__ == '__main__':
    collect()
