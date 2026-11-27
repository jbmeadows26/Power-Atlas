"""Build and verify a public, content-addressed Pages release manifest.

Only public frontend files are inventoried. Verification checks bytes, not merely
HTTP success, and never records private inputs or response contents.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'release-identity.json'
PREFIXES = ('business-intelligence', 'private-workspace', 'personal-intelligence')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(manifest, expected=None):
    if manifest.get('schemaVersion') != 1 or not re.fullmatch(r'[0-9a-f]{40}', manifest.get('commit', '')):
        raise ValueError('Invalid release identity')
    if expected and manifest['commit'] != expected:
        raise ValueError('Production commit does not match expected release')
    files = manifest.get('files', {})
    for required in ('business-intelligence/index.html', 'business-intelligence/app.mjs', 'private-workspace/vault-core.mjs'):
        if required not in files:
            raise ValueError('Required release asset missing')
    for name, sha in files.items():
        if not isinstance(name, str) or '..' in name.split('/') or name.startswith('/') or name.split('/')[0] not in PREFIXES or not re.fullmatch(r'[a-zA-Z0-9_./-]+', name):
            raise ValueError('Unsafe asset path')
        if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
            raise ValueError('Invalid asset digest')
    return manifest


def build(site, commit):
    files = {}
    for prefix in PREFIXES:
        for file in sorted((site / prefix).rglob('*')):
            # AI weights are independently pinned by their own asset manifest.
            if file.is_file() and file.suffix in ('.html', '.mjs', '.css', '.json') and 'adaptive-assets' not in file.parts:
                files[file.relative_to(site).as_posix()] = digest(file.read_bytes())
    result = validate({'schemaVersion': 1, 'commit': commit, 'files': files})
    (site / MANIFEST).write_text(json.dumps(result, indent=2) + '\n')
    return result


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'Eastern-Axis-release-verifier/1'}), timeout=30) as response:
        return response.read()


def verify(origin, expected=None):
    manifest = validate(json.loads(fetch(origin.rstrip('/') + '/' + MANIFEST)), expected)
    # Pin key source assets to the declared commit, including scheduled checks.
    for name in ('business-intelligence/index.html', 'business-intelligence/app.mjs', 'private-workspace/vault-core.mjs'):
        original = subprocess.check_output(['git', 'show', manifest['commit'] + ':site/' + name], cwd=ROOT)
        if digest(original) != manifest['files'][name]:
            raise ValueError('Manifest disagrees with repository source: ' + name)
    for name, sha in manifest['files'].items():
        if digest(fetch(origin.rstrip('/') + '/' + name + '?release=' + manifest['commit'])) != sha:
            raise ValueError('Published asset mismatch: ' + name)
    return {'status': 'Verified', 'commit': manifest['commit'], 'verifiedAssets': len(manifest['files']), 'scope': 'Public release identity and asset integrity only; not workflow or commercial acceptance'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('build', 'verify'))
    parser.add_argument('--site', type=Path, default=ROOT / 'site')
    parser.add_argument('--commit')
    parser.add_argument('--origin', default='https://jbmeadows26.github.io/Power-Atlas')
    args = parser.parse_args()
    if args.mode == 'build':
        sha = args.commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        result = build(args.site, sha)
        print(json.dumps({'commit': result['commit'], 'assets': len(result['files'])}))
    else:
        print(json.dumps(verify(args.origin, args.commit)))
