import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location('registry_ci', Path(__file__).parents[1] / 'github-registry/registry_ci.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)
SHA = 'a' * 40


class Response(io.BytesIO):
    status = 201


class RegistryTests(unittest.TestCase):
    def test_commit_validation(self):
        self.assertEqual(ci.version(SHA), 'development-' + SHA)
        for invalid in ('main', '../x', 'a' * 39, 'A' * 40):
            with self.assertRaises(ValueError):
                ci.version(invalid)

    def resolve(self, marker, force='false'):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'output'
            responses = [Response(json.dumps({'commit': {'id': SHA}}).encode()), marker]
            with patch.dict(os.environ, {'GITHUB_OUTPUT': str(output), 'FORCE_BUILD': force}), patch.object(ci.urllib.request, 'urlopen', side_effect=responses):
                ci.resolve()
            return output.read_text()

    def test_new_commit_builds(self):
        missing = urllib.error.HTTPError('https://gitlab.com', 404, 'not found', {}, None)
        self.assertIn('needed=true', self.resolve(missing))

    def test_completed_commit_skips(self):
        self.assertIn('needed=false', self.resolve(Response(json.dumps({'commit': SHA}).encode())))

    def test_force_rebuild(self):
        self.assertIn('needed=true', self.resolve(Response(json.dumps({'commit': SHA}).encode()), 'true'))

    def test_server_error_does_not_start_build(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.resolve(urllib.error.HTTPError('https://gitlab.com', 503, 'unavailable', {}, None))

    def test_publication_verifies_and_uploads_marker_last(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            folder = Path('source/dist'); folder.mkdir(parents=True)
            name = f'RyGT-development-{SHA[:8]}.zip'
            payload = b'test package'
            (folder / name).write_bytes(payload)
            (folder / (name + '.sha256')).write_text(hashlib.sha256(payload).hexdigest() + '  ' + name + '\n')
            uploads = {}; order = []
            def api(request, **kwargs):
                if isinstance(request, str):
                    return Response(uploads[request])
                self.assertEqual(request.headers.get('Deploy-token'), 'unit-test-only')
                uploads[request.full_url] = request.data.read()
                order.append(request.full_url)
                return Response(b'{}')
            env = {'SOURCE_SHA': SHA, 'GITHUB_REPOSITORY': 'test/repo', 'GITHUB_RUN_ID': '1',
                   'GITLAB_PACKAGE_TOKEN': 'unit-test-only', 'GITHUB_STEP_SUMMARY': str(Path(temp)/'summary')}
            with patch.dict(os.environ, env), patch.object(ci.urllib.request, 'urlopen', side_effect=api):
                ci.publish()
            self.assertTrue(order[-1].endswith('/CI-BUILD.json'))
            self.assertEqual(json.loads(uploads[order[-1]])['commit'], SHA)
            self.assertEqual(len(order), 3)


if __name__ == '__main__':
    unittest.main()
