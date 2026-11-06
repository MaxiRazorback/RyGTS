import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

apply_path = Path(__file__).parents[1] / 'runtime/apply.py'
spec = importlib.util.spec_from_file_location('runtime_overlay_apply', apply_path)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
validate_files = overlay.validate_files
prepare_three_way = overlay.prepare_three_way
write_transaction = overlay.write_transaction


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


class RuntimeOverlayTests(unittest.TestCase):
    def test_manifest_guards_exactly_the_patched_files(self):
        root = Path(__file__).resolve().parents[2]
        patch = (root / 'ci/runtime/production-source.patch').read_text(encoding='utf-8')
        manifest = json.loads((root / 'ci/runtime/overlay.json').read_text(encoding='utf-8'))
        patch_files = {line[6:] for line in patch.splitlines() if line.startswith('--- a/')}
        self.assertEqual(patch_files, set(manifest['source_files']))

    def test_amd_pipeline_policy_keeps_force_whole_perf_control(self):
        root = Path(__file__).resolve().parents[2]
        patch = (root / 'ci/runtime/production-source.patch').read_text(encoding='utf-8')
        self.assertIn(
            '+              tessellated && (Common::PerfFeatureEnabled(80) || '
            '!Mr14SharedTessellationEnabled(false)))',
            patch,
        )

    def test_checks_baseline_and_postimage_hashes_with_windows_newlines(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'src' / 'sample.cpp'
            target.parent.mkdir()
            baseline = b'int value = 1;\n'
            final = b'int value = 2;\n'
            target.write_bytes(baseline.replace(b'\n', b'\r\n'))
            files = {
                'src/sample.cpp': {
                    'baseline_sha256': hashlib.sha256(baseline).hexdigest(),
                    'new_sha256': hashlib.sha256(final).hexdigest(),
                },
                'src/new.h': {
                    'baseline_sha256': None,
                    'new_sha256': hashlib.sha256(b'#pragma once\n').hexdigest(),
                },
            }
            validate_files(root, files)
            self.assertRaises(RuntimeError, validate_files, root, files, final=True)
            target.write_bytes(final.replace(b'\n', b'\r\n'))
            (root / 'src' / 'new.h').write_bytes(b'#pragma once\r\n')
            validate_files(root, files, final=True)

    def test_rejects_unexpected_baseline_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'file.cpp'
            target.write_text('changed\n')
            files = {'file.cpp': {'baseline_sha256': '0' * 64, 'new_sha256': '1' * 64}}
            with self.assertRaisesRegex(RuntimeError, 'baseline mismatch'):
                validate_files(root, files)

    def test_three_way_merge_preserves_independent_renderer_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'renderer'
            source.mkdir()
            git(source, 'init', '-q')
            git(source, 'config', 'user.email', 'overlay-test@example.invalid')
            git(source, 'config', 'user.name', 'Overlay test')
            target = source / 'src/sample.cpp'
            target.parent.mkdir()
            baseline = b'first = 1;\ncontext;\nsecond = 1;\ntail;\n'
            postimage = b'first = 2;\ncontext;\nsecond = 1;\ntail;\n'
            target.write_bytes(baseline)
            git(source, 'add', 'src/sample.cpp')
            git(source, 'commit', '-q', '-m', 'base')
            base_commit = git(source, 'rev-parse', 'HEAD')
            target.write_bytes(b'first = 1;\ncontext;\nsecond = 3;\ntail;\n')
            git(source, 'commit', '-qam', 'upstream change')
            patch = root / 'overlay.patch'
            patch.write_bytes((
                '--- a/src/sample.cpp\n+++ b/src/sample.cpp\n'
                '@@ -1,4 +1,4 @@\n-first = 1;\n+first = 2;\n context;\n second = 1;\n tail;\n'
            ).encode())
            files = {'src/sample.cpp': {
                'baseline_sha256': hashlib.sha256(baseline).hexdigest(),
                'new_sha256': hashlib.sha256(postimage).hexdigest(),
            }}
            original, current, merged, verified = prepare_three_way(
                source, base_commit, patch, files, root / 'scratch')
            self.assertEqual(current['src/sample.cpp'], b'first = 1;\ncontext;\nsecond = 3;\ntail;\n')
            self.assertEqual(merged['src/sample.cpp'], b'first = 2;\ncontext;\nsecond = 3;\ntail;\n')
            self.assertEqual(verified['src/sample.cpp'], postimage)
            self.assertEqual(original['src/sample.cpp'], target.read_bytes())
            self.assertEqual(target.read_bytes(), current['src/sample.cpp'])

    def test_three_way_merge_conflict_leaves_all_files_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'renderer'
            source.mkdir()
            git(source, 'init', '-q')
            git(source, 'config', 'user.email', 'overlay-test@example.invalid')
            git(source, 'config', 'user.name', 'Overlay test')
            base_a = b'value = 1;\n'
            base_b = b'flag = 1;\n'
            (source / 'a.cpp').write_bytes(base_a)
            (source / 'b.cpp').write_bytes(base_b)
            git(source, 'add', '.')
            git(source, 'commit', '-q', '-m', 'base')
            base_commit = git(source, 'rev-parse', 'HEAD')
            (source / 'a.cpp').write_bytes(b'value = 3;\n')
            (source / 'b.cpp').write_bytes(b'flag = 2;\n')
            git(source, 'commit', '-qam', 'upstream change')
            patch = root / 'overlay.patch'
            patch.write_bytes((
                '--- a/a.cpp\n+++ b/a.cpp\n@@ -1 +1 @@\n-value = 1;\n+value = 2;\n'
                '--- a/b.cpp\n+++ b/b.cpp\n@@ -1 +1 @@\n-flag = 1;\n+flag = 3;\n'
            ).encode())
            files = {
                'a.cpp': {'baseline_sha256': hashlib.sha256(base_a).hexdigest(),
                          'new_sha256': hashlib.sha256(b'value = 2;\n').hexdigest()},
                'b.cpp': {'baseline_sha256': hashlib.sha256(base_b).hexdigest(),
                          'new_sha256': hashlib.sha256(b'flag = 3;\n').hexdigest()},
            }
            before = {'a.cpp': (source / 'a.cpp').read_bytes(),
                      'b.cpp': (source / 'b.cpp').read_bytes()}
            with self.assertRaisesRegex(RuntimeError, 'conflicted'):
                prepare_three_way(source, base_commit, patch, files, root / 'scratch')
            self.assertEqual({name: (source / name).read_bytes() for name in before}, before)

    def test_three_way_merge_accepts_already_applied_overlay(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'renderer'
            source.mkdir()
            git(source, 'init', '-q')
            git(source, 'config', 'user.email', 'overlay-test@example.invalid')
            git(source, 'config', 'user.name', 'Overlay test')
            baseline = b'value = 1;\n'
            postimage = b'value = 2;\n'
            target = source / 'value.cpp'
            target.write_bytes(baseline)
            git(source, 'add', 'value.cpp')
            git(source, 'commit', '-q', '-m', 'base')
            base_commit = git(source, 'rev-parse', 'HEAD')
            target.write_bytes(postimage)
            git(source, 'commit', '-qam', 'upstream includes overlay')
            patch = root / 'overlay.patch'
            patch.write_bytes((
                '--- a/value.cpp\n+++ b/value.cpp\n@@ -1 +1 @@\n-value = 1;\n+value = 2;\n'
            ).encode())
            files = {'value.cpp': {
                'baseline_sha256': hashlib.sha256(baseline).hexdigest(),
                'new_sha256': hashlib.sha256(postimage).hexdigest(),
            }}
            _, current, merged, _ = prepare_three_way(source, base_commit, patch, files, root / 'scratch')
            self.assertEqual(merged['value.cpp'], current['value.cpp'])

    def test_three_way_merge_rejects_bad_base_hash_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'renderer'
            source.mkdir()
            git(source, 'init', '-q')
            git(source, 'config', 'user.email', 'overlay-test@example.invalid')
            git(source, 'config', 'user.name', 'Overlay test')
            target = source / 'value.cpp'
            target.write_bytes(b'value = 1;\n')
            git(source, 'add', 'value.cpp')
            git(source, 'commit', '-q', '-m', 'base')
            base_commit = git(source, 'rev-parse', 'HEAD')
            patch = root / 'overlay.patch'
            patch.write_bytes((
                '--- a/value.cpp\n+++ b/value.cpp\n@@ -1 +1 @@\n-value = 1;\n+value = 2;\n'
            ).encode())
            bad_hash = {'value.cpp': {'baseline_sha256': '0' * 64, 'new_sha256': '1' * 64}}
            with self.assertRaisesRegex(RuntimeError, 'baseline object mismatch'):
                prepare_three_way(source, base_commit, patch, bad_hash, root / 'bad-hash')
            bad_postimage = {'value.cpp': {
                'baseline_sha256': hashlib.sha256(b'value = 1;\n').hexdigest(),
                'new_sha256': '1' * 64,
            }}
            with self.assertRaisesRegex(RuntimeError, 'postimage object mismatch'):
                prepare_three_way(source, base_commit, patch, bad_postimage, root / 'bad-postimage')
            traversal = {'../value.cpp': {'baseline_sha256': '0' * 64, 'new_sha256': '1' * 64}}
            with self.assertRaisesRegex(RuntimeError, 'Invalid overlay path'):
                prepare_three_way(source, base_commit, patch, traversal, root / 'traversal')
            with self.assertRaisesRegex(RuntimeError, 'Missing overlay baseline object'):
                prepare_three_way(source, '1' * 40, patch,
                                  {'value.cpp': {
                                      'baseline_sha256': hashlib.sha256(b'value = 1;\n').hexdigest(),
                                      'new_sha256': hashlib.sha256(b'value = 2;\n').hexdigest(),
                                  }}, root / 'missing-base')

    def test_write_transaction_rolls_back_mid_write_and_postcheck_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'renderer'
            source.mkdir()
            first = source / 'first.cpp'
            second = source / 'second.cpp'
            manifest = source / 'RUNTIME-SOURCE.json'
            original = {'first.cpp': b'first\r\n', 'second.cpp': b'second\r\n'}
            first.write_bytes(original['first.cpp'])
            second.write_bytes(original['second.cpp'])
            manifest.write_bytes(b'old manifest\r\n')
            merged = {'first.cpp': b'new first\n', 'second.cpp': b'new second\n'}
            original_manifest = manifest.read_bytes()
            real_replace = overlay.os.replace
            calls = 0

            def fail_second_replace(source_path, target_path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected replace failure')
                real_replace(source_path, target_path)

            with patch.object(overlay.os, 'replace', side_effect=fail_second_replace):
                with self.assertRaisesRegex(OSError, 'injected replace failure'):
                    write_transaction(source, original, merged, manifest, b'new manifest', lambda: None)
            self.assertEqual(first.read_bytes(), original['first.cpp'])
            self.assertEqual(second.read_bytes(), original['second.cpp'])
            self.assertEqual(manifest.read_bytes(), original_manifest)

            with self.assertRaisesRegex(RuntimeError, 'postcheck failed'):
                write_transaction(source, original, merged, manifest, b'new manifest',
                                  lambda: (_ for _ in ()).throw(RuntimeError('postcheck failed')))
            self.assertEqual(first.read_bytes(), original['first.cpp'])
            self.assertEqual(second.read_bytes(), original['second.cpp'])
            self.assertEqual(manifest.read_bytes(), original_manifest)


if __name__ == '__main__':
    unittest.main()
