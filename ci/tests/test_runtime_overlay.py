import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

apply_path = Path(__file__).parents[1] / 'runtime/apply.py'
spec = importlib.util.spec_from_file_location('runtime_overlay_apply', apply_path)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
validate_files = overlay.validate_files


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


if __name__ == '__main__':
    unittest.main()
