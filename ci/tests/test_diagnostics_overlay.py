import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
apply_path = ROOT / "ci/diagnostics/apply.py"
spec = importlib.util.spec_from_file_location("diagnostics_overlay_apply", apply_path)
diagnostics_apply = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics_apply)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


class DiagnosticsOverlayTests(unittest.TestCase):
    def test_diagnostics_overlay_guards_only_the_file_it_patches(self):
        diagnostics = json.loads((ROOT / "ci/diagnostics/overlay.json").read_text(encoding="utf-8"))
        self.assertEqual(diagnostics["files"], [])
        patch = (ROOT / "ci/diagnostics/renderer.patch").read_text(encoding="utf-8")
        patch_files = {line[6:] for line in patch.splitlines() if line.startswith("--- a/")}
        self.assertEqual(patch_files, {"ryty_gpu/RytyGpu.cmake"})
        apply = (ROOT / "ci/diagnostics/apply.py").read_text(encoding="utf-8")
        self.assertIn("RENDERER_SHA", apply)
        self.assertNotIn("base_native_sha256", apply)

    def test_rejected_patch_restores_cmake_crlf_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "renderer"
            source.mkdir()
            git(source, "init", "-q")
            git(source, "config", "user.email", "overlay-test@example.invalid")
            git(source, "config", "user.name", "Overlay test")
            cmake = source / "ryty_gpu/RytyGpu.cmake"
            cmake.parent.mkdir()
            original = b"cmake_minimum_required(VERSION 3.16)\r\n# unpatched\r\n"
            cmake.write_bytes(original)
            git(source, "add", "ryty_gpu/RytyGpu.cmake")
            git(source, "commit", "-q", "-m", "renderer")
            head = git(source, "rev-parse", "HEAD")
            self.assertEqual(cmake.read_bytes(), original)
            with patch.dict(os.environ, {"RENDERER_SHA": head}):
                with self.assertRaises(subprocess.CalledProcessError):
                    diagnostics_apply.apply(source)
            self.assertEqual(cmake.read_bytes(), original)
            self.assertFalse((source / "DIAGNOSTICS-SOURCE.json").exists())


if __name__ == "__main__":
    unittest.main()
