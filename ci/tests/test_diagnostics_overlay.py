import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DiagnosticsOverlayTests(unittest.TestCase):
    def test_diagnostics_overlay_base_matches_runtime_postimage(self):
        runtime = json.loads((ROOT / "ci/runtime/overlay.json").read_text(encoding="utf-8"))
        diagnostics = json.loads((ROOT / "ci/diagnostics/overlay.json").read_text(encoding="utf-8"))
        native = runtime["source_files"]["src/video_core/renderer_vulkan/vk_rasterizer_native.cpp"]

        self.assertEqual(diagnostics["renderer_commit"], runtime["renderer_commit"])
        self.assertEqual(diagnostics["base_native_sha256"], native["new_sha256"])


if __name__ == "__main__":
    unittest.main()
