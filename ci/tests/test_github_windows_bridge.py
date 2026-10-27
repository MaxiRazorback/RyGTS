import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
import urllib.request
import zipfile

MODULE = Path(__file__).resolve().parents[1] / 'github_windows_bridge.py'
spec = importlib.util.spec_from_file_location('bridge', MODULE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class ArtifactTests(unittest.TestCase):
    expected = dict(gitlab_commit='a' * 40, workflow_commit='b' * 40,
                    request_id='1-2-' + 'c' * 32, github_run_id='123')

    def bundle(self, metadata=None, extra=None, corrupt=False):
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, 'w') as archive:
            archive.writestr('GITHUB-BUILD.json', json.dumps(metadata or self.expected))
            for folder, filename in [('launcher', 'RyGT.exe'), ('renderer', 'libSceVideoOut.prx')]:
                binary = b'MZ-build-output'
                archive.writestr(f'{folder}/{filename}', binary + (b'tampered' if corrupt else b''))
                archive.writestr(f'{folder}/RYGT-COMMIT.txt', self.expected['gitlab_commit'])
                archive.writestr(f'{folder}/SHA256SUMS.txt', hashlib.sha256(binary).hexdigest() + '  ' + filename)
            if extra is not None:
                archive.writestr(extra, b'bad')
        memory.seek(0)
        return memory

    def test_matching_outputs_are_extracted(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge.unpack(self.bundle(), directory, self.expected)
            self.assertEqual((Path(directory)/'launcher/RyGT.exe').read_bytes(), b'MZ-build-output')

    def test_wrong_source_or_run_never_extracts(self):
        for key in self.expected:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                metadata = dict(self.expected, **{key: 'wrong'})
                with self.assertRaises(RuntimeError):
                    bridge.unpack(self.bundle(metadata=metadata), directory, self.expected)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_tampered_binary_never_extracts(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                bridge.unpack(self.bundle(corrupt=True), directory, self.expected)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_traversal_and_unexpected_paths_are_rejected(self):
        for path in ['../escape', '/escape', r'launcher\..\escape', 'C:/escape', 'other/file']:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(RuntimeError):
                    bridge.unpack(self.bundle(extra=path), directory, self.expected)

    def test_symlink_is_rejected(self):
        entry = zipfile.ZipInfo('launcher/link')
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                bridge.unpack(self.bundle(extra=entry), directory, self.expected)


class RedirectTests(unittest.TestCase):
    def test_signed_download_redirect_does_not_receive_token(self):
        request = urllib.request.Request('https://api.github.com/artifact', headers={'Authorization': 'Bearer test-only'})
        redirected = bridge.SafeRedirect().redirect_request(request, None, 302, 'Found', {}, 'https://blob.example/artifact')
        self.assertFalse(redirected.has_header('Authorization'))

    def test_plain_http_download_is_rejected(self):
        request = urllib.request.Request('https://api.github.com/artifact')
        with self.assertRaises(RuntimeError):
            bridge.SafeRedirect().redirect_request(request, None, 302, 'Found', {}, 'http://blob.example/artifact')


if __name__ == '__main__':
    unittest.main()
