"""Exercise both archives and redistribution boundaries without network/builds."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('package', ROOT / 'ci/package.py')
pkg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)
SHA = 'a' * 40
GUID = uuid.UUID('01234567-89ab-cdef-0123-456789abcdef')


def pe():
    data = bytearray(1024)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<H', data, 134, 1)
    struct.pack_into('<H', data, 148, 240)
    struct.pack_into('<H', data, 152, 0x20b)
    struct.pack_into('<II', data, 152 + 112 + 48, 0x1000, 28)
    struct.pack_into('<IIII', data, 392 + 8, 512, 0x1000, 512, 512)
    struct.pack_into('<IIII', data, 512 + 12, 2, 24, 0x1040, 576)
    data[576:600] = b'RSDS' + GUID.bytes_le + struct.pack('<I', 1)
    data[650:650+len(b'DISCORD-RPC: compiled in; 1440140585595047977')] = b'DISCORD-RPC: compiled in; 1440140585595047977'
    return bytes(data)


class PackageTests(unittest.TestCase):
    def fixture(self):
        base = Path('base.zip')
        with zipfile.ZipFile(base, 'w') as z:
            for name in ('converter/ryty.exe', 'tools/adcpatch/adcpatch.exe',
                         'libs/libSceBluetoothHid.prx', 'amd_fidelityfx_vk.dll',
                         'amd_fidelityfx_vk-LICENSE.txt', 'launcher/background.png'):
                z.writestr(pkg.BASE_FOLDER + '/' + name, b'fixture')
            z.writestr(pkg.BASE_FOLDER + '/user/custom_configs/CUSA03220.json',
                       json.dumps({'GPU': {'precompile_shaders': False},
                                   'Vulkan': {'pipeline_cache_enabled': False}}))
        pin = json.loads((ROOT / 'renderer/source.json').read_text())
        for flavor, _, suffix in pkg.VARIANTS:
            for target, binary in (('launcher', 'RyGTS.exe'), ('renderer', 'libSceVideoOut.prx')):
                folder = Path('artifacts/' + target + suffix)
                folder.mkdir(parents=True)
                (folder / binary).write_bytes(pe())
                (folder / 'RYGT-COMMIT.txt').write_text(SHA)
                (folder / 'BUILD-PROFILE.json').write_text(json.dumps(dict(
                    schema=1, flavor=flavor, commit=SHA, optimized=True,
                    full_symbols=bool(suffix))))
                if target == 'renderer':
                    (folder / 'CI-SOURCE.txt').write_text(pin['repository'] + '\n' + pin['commit'] + '\n')
                    runtime_spec = json.loads((ROOT / 'ci/runtime/overlay.json').read_text())
                    runtime_patch = ROOT / 'ci/runtime/production-source.patch'
                    (folder / 'RUNTIME-SOURCE.json').write_text(json.dumps(dict(
                        schema=1, renderer_commit=pin['commit'],
                        overlay_sha256=pkg.sha(runtime_patch), source_files=runtime_spec['source_files'])))
                if suffix:
                    pdb = folder / (Path(binary).stem + '.pdb')
                    pdb.write_bytes(b'Microsoft C/C++ MSF 7.00 fixture')
                    (folder / 'SYMBOLS.json').write_text(json.dumps(dict(
                        binary=binary, pdb=pdb.name, guid=str(GUID), age=1,
                        binary_sha256=pkg.sha(folder / binary), pdb_sha256=pkg.sha(pdb))))
                    if target == 'renderer':
                        (folder / 'frame-capture-layouts.json').write_text(json.dumps({pkg.sha(folder / binary).upper(): {}}))
                        (folder / 'DIAGNOSTICS-SOURCE.json').write_text('{}')
                self.rehash(folder)
        return base

    def rehash(self, folder):
        (folder / 'SHA256SUMS.txt').write_text(''.join(
            pkg.sha(f) + '  ' + f.name + '\n' for f in sorted(folder.iterdir())
            if f.name != 'SHA256SUMS.txt'))

    def test_separate_archives_symbols_defaults_and_provenance(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            base = self.fixture()
            with patch.dict(os.environ, {'CI_COMMIT_SHA': SHA, 'RYGT_PACKAGE_BASE': str(base)}), patch.object(pkg, 'BASE_SHA', pkg.sha(base)):
                pkg.package()
            manifest = json.loads(Path('dist/CI-PACKAGES.json').read_text())
            self.assertEqual([v['channel'] for v in manifest['variants']], ['ci', 'debug-ci'])
            for variant in manifest['variants']:
                archive = Path('dist') / variant['archive']
                self.assertEqual(pkg.sha(archive), variant['sha256'])
                prefix = archive.stem + '/'
                with zipfile.ZipFile(archive) as z:
                    names = {n.removeprefix(prefix) for n in z.namelist()}
                    pdbs = {n for n in names if n.endswith('.pdb')}
                    self.assertEqual(pdbs, {'RyGTS.pdb', 'libs/libSceVideoOut.pdb'} if variant['channel'] == 'debug-ci' else set())
                    self.assertEqual('tools/diagnostics/Start-Capture.cmd' in names, bool(pdbs))
                    config = json.loads(z.read(prefix + 'user/custom_configs/CUSA03220.json'))
                    self.assertTrue(config['GPU']['precompile_shaders'])
                    self.assertTrue(config['Vulkan']['pipeline_cache_enabled'])
                    info = json.loads(z.read(prefix + 'BUILD_INFO.txt'))
                    self.assertEqual(info['commit'], SHA)
                    self.assertEqual(info['channel'], variant['channel'])
                    self.assertEqual(info['rebuilt'], ['RyGTS.exe', 'libs/libSceVideoOut.prx'])
                    self.assertEqual(info['runtime_overlay']['renderer_commit'],
                                     json.loads((ROOT / 'renderer/source.json').read_text())['commit'])
                    for line in z.read(prefix + 'SHA256SUMS.txt').decode().splitlines():
                        digest, name = line.split('  ', 1)
                        import hashlib
                        self.assertEqual(hashlib.sha256(z.read(prefix + name)).hexdigest(), digest)

    def test_missing_or_wrong_symbols_and_source_revision_rejected(self):
        for mutation in ('identity', 'missing', 'commit'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
                self.fixture()
                folder = Path('artifacts/renderer-diagnostics')
                if mutation == 'identity':
                    symbols = folder / 'SYMBOLS.json'
                    value = json.loads(symbols.read_text()); value['age'] = 2
                    symbols.write_text(json.dumps(value))
                elif mutation == 'missing':
                    (folder / 'libSceVideoOut.pdb').unlink()
                else:
                    (folder / 'RYGT-COMMIT.txt').write_text('b' * 40)
                if mutation != 'missing': self.rehash(folder)
                with self.assertRaises((RuntimeError, FileNotFoundError)):
                    pkg.verify_bundle(folder, 'libSceVideoOut.prx', SHA, 'Diagnostics')

    def test_runtime_overlay_provenance_must_match_pinned_patch(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            base = self.fixture()
            folder = Path('artifacts/renderer')
            overlay_path = folder / 'RUNTIME-SOURCE.json'
            overlay = json.loads(overlay_path.read_text())
            overlay['overlay_sha256'] = '0' * 64
            overlay_path.write_text(json.dumps(overlay))
            self.rehash(folder)
            with patch.dict(os.environ, {'CI_COMMIT_SHA': SHA, 'RYGT_PACKAGE_BASE': str(base)}), \
                    patch.object(pkg, 'BASE_SHA', pkg.sha(base)), \
                    self.assertRaisesRegex(RuntimeError, 'Production renderer overlay provenance mismatch'):
                pkg.package()

    def test_forbidden_runtime_content(self):
        bad = ('module.sprx', 'symbols.pdb', 'GTSport.exe', 'shaders/x.bin', 'saves/x.dat',
               'sys/module.bin', 'user/private.json', 'nvngx_dlss.dll', 'sl.interposer.dll',
               '../outside', 'x:stream', 'x\\outside')
        for name in bad:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
                with zipfile.ZipFile('base.zip', 'w') as z:
                    entry = zipfile.ZipInfo()
                    # Windows ZipInfo construction normalizes backslashes; retain
                    # the raw hostile spelling to exercise the extraction guard.
                    entry.filename = pkg.BASE_FOLDER + '/' + name
                    z.writestr(entry, b'excluded')
                with self.assertRaises(RuntimeError):
                    pkg.extract_runtime(Path('base.zip'), Path('stage'))

    def test_duplicate_and_symlink_rejected(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
                with zipfile.ZipFile('base.zip', 'w') as z:
                    entry = zipfile.ZipInfo(pkg.BASE_FOLDER + '/safe.txt')
                    if symlink: entry.external_attr = 0o120777 << 16
                    z.writestr(entry, b'fixture')
                    if not symlink: z.writestr(pkg.BASE_FOLDER + '/SAFE.txt', b'duplicate')
                with self.assertRaises(RuntimeError):
                    pkg.extract_runtime(Path('base.zip'), Path('stage'))


if __name__ == '__main__':
    unittest.main()
