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

    def resolve(self, markers, force='false'):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'output'
            responses = [Response(json.dumps({'commit': {'id': SHA}}).encode()), *markers]
            with patch.dict(os.environ, {'GITHUB_OUTPUT': str(output), 'FORCE_BUILD': force}), patch.object(ci.urllib.request, 'urlopen', side_effect=responses):
                ci.resolve()
            return output.read_text()

    def test_new_commit_builds(self):
        missing = urllib.error.HTTPError('https://gitlab.com', 404, 'not found', {}, None)
        self.assertIn('needed=true', self.resolve([missing, missing]))

    def markers(self):
        return [Response(json.dumps({'commit': SHA, 'channel': channel}).encode()) for channel in ci.CHANNELS]

    def test_incomplete_debug_channel_rebuilds(self):
        missing = urllib.error.HTTPError('https://gitlab.com', 404, 'not found', {}, None)
        self.assertIn('needed=true', self.resolve([self.markers()[0], missing]))

    def test_completed_commit_skips(self):
        self.assertIn('needed=false', self.resolve(self.markers()))

    def test_force_rebuild(self):
        self.assertIn('needed=true', self.resolve(self.markers(), 'true'))

    def test_server_error_does_not_start_build(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.resolve([urllib.error.HTTPError('https://gitlab.com', 503, 'unavailable', {}, None)])

    def prepare_packages(self, folder):
        variants = []
        for channel in ci.CHANNELS:
            name = f'RyGT-{channel}-{SHA[:8]}.zip'
            payload = ('test package ' + channel).encode()
            digest = hashlib.sha256(payload).hexdigest()
            (folder / name).write_bytes(payload)
            (folder / (name + '.sha256')).write_text(digest + '  ' + name + '\n')
            variants.append(dict(channel=channel, archive=name, sha256=digest))
        (folder / 'CI-PACKAGES.json').write_text(json.dumps(dict(schema=2, commit=SHA, variants=variants)))

    def test_publication_verifies_and_uploads_marker_last(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            folder = Path('source/dist'); folder.mkdir(parents=True)
            self.prepare_packages(folder)
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
            self.assertTrue(all(url.endswith('/CI-BUILD.json') for url in order[-2:]))
            self.assertTrue(all(not url.endswith('/CI-BUILD.json') for url in order[:-2]))
            for channel, url in zip(ci.CHANNELS, order[-2:]):
                self.assertEqual(json.loads(uploads[url])['commit'], SHA)
                self.assertEqual(json.loads(uploads[url])['channel'], channel)
                self.assertIn('/generic/' + channel + '/', url)
            self.assertEqual(len(order), 6)

    def test_bad_debug_checksum_prevents_all_uploads(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            folder = Path('source/dist'); folder.mkdir(parents=True)
            self.prepare_packages(folder)
            (folder / f'RyGT-debug-ci-{SHA[:8]}.zip').write_bytes(b'corrupt')
            with patch.dict(os.environ, {'SOURCE_SHA': SHA}), patch.object(ci.urllib.request, 'urlopen') as api:
                with self.assertRaisesRegex(RuntimeError, 'checksum'):
                    ci.publish()
                api.assert_not_called()

    def test_bad_remote_readback_prevents_completion_markers(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            folder = Path('source/dist'); folder.mkdir(parents=True)
            self.prepare_packages(folder)
            order = []
            def api(request, **kwargs):
                if isinstance(request, str): return Response(b'corrupt')
                order.append(request.full_url)
                return Response(b'{}')
            env = {'SOURCE_SHA': SHA, 'GITHUB_REPOSITORY': 'test/repo', 'GITHUB_RUN_ID': '1',
                   'GITLAB_PACKAGE_TOKEN': 'unit-test-only'}
            with patch.dict(os.environ, env), patch.object(ci.urllib.request, 'urlopen', side_effect=api):
                with self.assertRaisesRegex(RuntimeError, 'Uploaded package checksum'):
                    ci.publish()
            self.assertEqual(len(order), 1)
            self.assertFalse(any(url.endswith('/CI-BUILD.json') for url in order))


if __name__ == '__main__':
    unittest.main()
