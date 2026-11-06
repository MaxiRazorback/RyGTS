"""Execute the build script's real compile-database checks without a renderer build."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which('pwsh') or shutil.which('powershell')


@unittest.skipUnless(POWERSHELL, 'PowerShell required (available on Windows CI)')
class CompileFlagsTests(unittest.TestCase):
    def entry(self, filename, target='ryty_gpu', flags='/DNDEBUG', output=True,
              separator='/', quoted=False):
        obj = f'CMakeFiles/{target}.dir/src/{filename}.obj'.replace('/', separator)
        command = f'clang-cl {flags} /Fo' + (f'"{obj}"' if quoted else obj) + f' -c C:/renderer/src/{filename}'
        result = dict(file=f'C:/renderer/src/{filename}', command=command)
        if output:
            result['output'] = obj
        return result

    def check(self, entries, flavor, success=True, error=None):
        build = (ROOT / 'ci/build-windows.ps1').read_text(encoding='utf-8')
        checks = build.split("    Invoke-Checked 'cmake' $cmakeArgs\n", 1)[1].split('    $probeSource =', 1)[0]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)
            database = source / 'Build/ci/compile_commands.json'
            database.parent.mkdir(parents=True)
            database.write_text(json.dumps(entries), encoding='utf-8')
            script = source / 'verify.ps1'
            script.write_text("param([string]$source, [string]$Flavor)\n$ErrorActionPreference = 'Stop'\nSet-StrictMode -Version Latest\n" + checks, encoding='utf-8')
            result = subprocess.run([POWERSHELL, '-NoProfile', '-File', str(script), str(source), flavor], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        if error:
            self.assertIn(error, result.stdout + result.stderr)

    def test_release_selects_renderer_not_emulator(self):
        self.check([self.entry('vk_rasterizer.cpp', 'shadps4', '/UNDEBUG'),
                    self.entry('vk_rasterizer.cpp')], 'Release')

    def test_diagnostics_selects_renderer_c_and_cpp_not_emulator(self):
        flags = '/O2 /Ob2 /Zi /UNDEBUG'
        self.check([self.entry('vk_rasterizer.cpp', 'shadps4'),
                    self.entry('vk_rasterizer.cpp', flags=flags),
                    self.entry('native_xxh512.c', flags=flags)], 'Diagnostics')

    def test_windows_paths_and_command_only_databases(self):
        for output in (True, False):
            for separator in ('/', '\\'):
                with self.subTest(output=output, separator=separator):
                    self.check([self.entry('vk_rasterizer.cpp', 'shadps4', '/UNDEBUG', output, separator, True),
                                self.entry('vk_rasterizer.cpp', output=output, separator=separator, quoted=True)], 'Release')

    def test_missing_and_duplicate_renderer_entries_fail(self):
        for entries in ([self.entry('vk_rasterizer.cpp', 'shadps4')],
                        [self.entry('vk_rasterizer.cpp')] * 2):
            with self.subTest(entries=entries):
                self.check(entries, 'Release', False, 'Expected one Release rasterizer')

    def test_wrong_renderer_flags_fail_despite_valid_emulator_flags(self):
        self.check([self.entry('vk_rasterizer.cpp', 'shadps4'),
                    self.entry('vk_rasterizer.cpp', flags='/UNDEBUG')], 'Release', False, 'must retain NDEBUG')
        self.check([self.entry('vk_rasterizer.cpp', flags='/DNDEBUG /UNDEBUG')], 'Release', False, 'must retain NDEBUG')

    def test_diagnostics_rejects_missing_c_entry_and_ndebug(self):
        flags = '/O2 /Ob2 /Zi /UNDEBUG'
        self.check([self.entry('vk_rasterizer.cpp', flags=flags)], 'Diagnostics', False, 'Expected one diagnostics compile command')
        self.check([self.entry('vk_rasterizer.cpp', flags=flags),
                    self.entry('native_xxh512.c', flags=flags + ' /DNDEBUG')], 'Diagnostics', False, 'without NDEBUG')

    def test_include_path_is_not_target_evidence(self):
        entry = self.entry('vk_rasterizer.cpp', 'shadps4', output=False)
        entry['command'] += ' -ICMakeFiles/ryty_gpu.dir/include'
        self.check([entry], 'Release', False, 'Expected one Release rasterizer')


if __name__ == '__main__':
    unittest.main()
