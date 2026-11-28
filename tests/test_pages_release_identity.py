import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('identity', Path(__file__).resolve().parents[1] / 'scripts/pages_release_identity.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReleaseIdentityTests(unittest.TestCase):
    def manifest(self):
        return {'schemaVersion': 1, 'commit': 'a' * 40, 'files': {name: 'b' * 64 for name in ('business-intelligence/index.html', 'business-intelligence/app.mjs', 'private-workspace/vault-core.mjs')}}

    def test_wrong_release_fails(self):
        with self.assertRaises(ValueError):
            m.validate(self.manifest(), 'c' * 40)

    def test_path_injection_fails(self):
        for path in ('../secret', 'business-intelligence/../../secret', 'business-intelligence/file?private=yes', '/business-intelligence/app.mjs'):
            data = self.manifest()
            data['files'][path] = 'b' * 64
            with self.assertRaises(ValueError):
                m.validate(data)

    def test_missing_asset_fails(self):
        data = self.manifest()
        del data['files']['business-intelligence/app.mjs']
        with self.assertRaises(ValueError):
            m.validate(data)

    def test_build_hashes_actual_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder)
            for name in self.manifest()['files']:
                file = site / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b'public source')
            result = m.build(site, 'a' * 40)
            self.assertEqual(set(result['files'].values()), {m.digest(b'public source')})
            self.assertTrue((site / m.MANIFEST).exists())

    def test_published_asset_corruption_fails(self):
        data = self.manifest()
        data['files'] = {name: m.digest(b'public source') for name in data['files']}
        responses = [json.dumps(data).encode(), b'tampered asset']
        with patch.object(m, 'fetch', side_effect=responses), patch.object(m.subprocess, 'check_output', return_value=b'public source'):
            with self.assertRaisesRegex(ValueError, 'Published asset mismatch'):
                m.verify('https://example.test', 'a' * 40)

    def test_manifest_cannot_redefine_repository_source(self):
        data = self.manifest()
        with patch.object(m, 'fetch', return_value=json.dumps(data).encode()), patch.object(m.subprocess, 'check_output', return_value=b'actual repository source'):
            with self.assertRaisesRegex(ValueError, 'Manifest disagrees'):
                m.verify('https://example.test')

    def test_build_includes_control_registry_and_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder)
            for name in list(self.manifest()['files']) + ['development-control/acceptance.json', 'development-control/evidence/release.json']:
                file = site / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes((Path(__file__).resolve().parents[1] / 'site/development-control/acceptance.json').read_bytes() if name == 'development-control/acceptance.json' else b'{}')
            manifest = m.build(site, 'a' * 40)
            self.assertIn('development-control/acceptance.json', manifest['files'])
            self.assertIn('development-control/evidence/release.json', manifest['files'])
            self.assertEqual(manifest['acceptanceContext']['deployedCommit'], 'a' * 40)

    def test_acceptance_context_carries_only_mechanically_unchanged_scopes(self):
        registry = {'schema': 'eastern-axis.acceptance.v2', 'evidence': [
            {'id': 'unchanged', 'commit': 'a' * 40, 'releaseScope': {'policy': 'unchanged-assets', 'paths': ['site/business-intelligence/app.mjs']}},
            {'id': 'changed', 'commit': 'b' * 40, 'releaseScope': {'policy': 'unchanged-assets', 'paths': ['site/business-intelligence/engine.mjs']}},
        ]}
        completed = [m.subprocess.CompletedProcess([], 0), m.subprocess.CompletedProcess([], 1)]
        with patch.object(m.subprocess, 'run', side_effect=completed):
            context = m.acceptance_context(registry, 'c' * 40)
        self.assertEqual(context['carryForwardEvidence'], ['unchanged'])

    def test_manifest_treats_missing_context_as_legacy_and_rejects_forgery(self):
        data = self.manifest()
        data['files']['development-control/acceptance.json'] = 'b' * 64
        self.assertNotIn('acceptanceContext', m.validate(data))
        data['acceptanceContext'] = {
            'schema': m.CONTEXT_SCHEMA,
            'status': 'Verified',
            'deployedCommit': data['commit'],
            'source': 'content-addressed-pages-release-identity',
            'artifact': m.MANIFEST,
            'carryForwardEvidence': ['duplicate', 'duplicate'],
        }
        with self.assertRaisesRegex(ValueError, 'carry-forward'):
            m.validate(data)

    def test_acceptance_context_rejects_unsafe_or_self_referential_scope(self):
        for path in ('../secret', '/site/business-intelligence/app.mjs', 'site/development-control/acceptance.json'):
            registry = {'schema': 'eastern-axis.acceptance.v2', 'evidence': [{'id': 'unsafe', 'commit': 'a' * 40, 'stage': 'production', 'releaseScope': {'policy': 'unchanged-assets', 'paths': [path]}}]}
            with self.assertRaisesRegex(ValueError, 'scope|carry itself'):
                m.acceptance_context(registry, 'b' * 40)
