import importlib.util
from pathlib import Path
import tempfile
import unittest

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
