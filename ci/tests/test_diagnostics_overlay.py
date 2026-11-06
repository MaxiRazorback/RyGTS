import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DiagnosticsOverlayTests(unittest.TestCase):
    def test_diagnostics_overlay_base_matches_exact_renderer(self):
        runtime = json.loads((ROOT / "ci/runtime/overlay.json").read_text(encoding="utf-8"))
        diagnostics = json.loads((ROOT / "ci/diagnostics/overlay.json").read_text(encoding="utf-8"))

        self.assertEqual(diagnostics["renderer_commit"], runtime["renderer_commit"])
        self.assertEqual(runtime["renderer_commit"], "449a00493940f7c3cc030fd2c166b54c7118b532")
        self.assertEqual(
            diagnostics["base_native_sha256"],
            "6c84e2b94b3c57d24f9b5e881a5fb2032083aab6bbf42a767ac82a6956ce366c",
        )
        self.assertEqual(diagnostics["files"], [])


if __name__ == "__main__":
    unittest.main()
