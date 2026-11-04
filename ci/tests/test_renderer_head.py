"""Renderer policy resolves once and keeps explicit commit pins authoritative."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('prepare_renderer', ROOT / 'ci/prepare-renderer.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
SHA = 'a' * 40
OTHER = 'b' * 40

class RendererPolicyTests(unittest.TestCase):
    def prepare(self, policy, env, expected=SHA):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'renderer').mkdir(); (root/'ci').mkdir()
            (root/'renderer/source.json').write_text(json.dumps({'repository':'https://example.invalid/renderer.git', 'branch':'main', 'commit':policy}))
            output = root/'checkout'
            def run(*args):
                if args[1] == 'init': output.mkdir()
            def check(args, **kwargs):
                if 'ls-remote' in args: return SHA + '\trefs/heads/main\n'
                return expected + '\n'
            with mock.patch.object(module, '__file__', str(root/'ci/prepare-renderer.py')), mock.patch.object(module, 'run', side_effect=run) as commands, mock.patch.object(module.subprocess, 'check_output', side_effect=check) as calls, mock.patch.dict(os.environ, env, clear=True):
                module.prepare(output)
                self.assertEqual((output/'CI-SOURCE.txt').read_text().splitlines()[-1], expected)
                self.assertIn(expected, [arg for call in commands.call_args_list for arg in call.args])
                return calls.call_args_list

    def test_head_resolves_once_or_uses_controller(self):
        calls=self.prepare('HEAD', {})
        self.assertEqual(sum('ls-remote' in call.args[0] for call in calls), 1)
        calls=self.prepare('HEAD', {'RENDERER_SHA': SHA})
        self.assertFalse(any('ls-remote' in call.args[0] for call in calls))

    def test_explicit_pin_and_invalid_overrides(self):
        self.prepare(SHA, {})
        self.prepare(SHA, {'RENDERER_SHA': SHA})
        with self.assertRaises(SystemExit): self.prepare(SHA, {'RENDERER_SHA': OTHER})
        with self.assertRaises(SystemExit): self.prepare('HEAD', {'RENDERER_SHA': 'bad'})
        with self.assertRaises(SystemExit): self.prepare('bad', {})
        with self.assertRaises(SystemExit): self.prepare('HEAD', {'RENDERER_SHA': SHA}, OTHER)

if __name__ == '__main__': unittest.main()
