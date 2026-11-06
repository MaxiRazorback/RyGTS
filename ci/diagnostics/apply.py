"""Apply the diagnostics-only overlay to the independently prepared renderer checkout."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_bytes(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def git_output(source, *arguments):
    return subprocess.check_output(
        ['git', '-c', f'safe.directory={source}', '-C', str(source), *arguments])


def atomic_replace(path, contents):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(contents)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def existing_state(source, actual, root):
    expected_tracked = set()
    expected_untracked = set()
    runtime_manifest_path = source / 'RUNTIME-SOURCE.json'
    if runtime_manifest_path.exists():
        runtime_root = root.parent / 'runtime'
        runtime_spec = json.loads((runtime_root / 'overlay.json').read_text(encoding='utf-8'))
        runtime_patch = runtime_root / 'production-source.patch'
        manifest = json.loads(runtime_manifest_path.read_text(encoding='utf-8'))
        files = manifest.get('source_files', {})
        expected_files = runtime_spec['source_files']
        if (manifest.get('schema') != 2 or manifest.get('renderer_commit') != actual
                or manifest.get('overlay_sha256') != sha256(runtime_patch.read_bytes())
                or set(files) != set(expected_files)):
            raise RuntimeError('Existing runtime overlay manifest does not match renderer or patch')
        patch_files = {line[6:] for line in runtime_patch.read_text(encoding='utf-8').splitlines()
                       if line.startswith('--- a/')}
        if patch_files != set(expected_files):
            raise RuntimeError('Runtime overlay path set changed')
        for relative, expected in expected_files.items():
            entry = files[relative]
            current = source / relative
            current_hash = sha256(normalized_bytes(current))
            if (entry.get('baseline_sha256') != expected['baseline_sha256']
                    or entry.get('overlay_sha256') != expected['new_sha256']
                    or entry.get('overlay_postimage_verified') is not True
                    or entry.get('merged_sha256') != current_hash):
                raise RuntimeError(f'Existing runtime overlay postimage mismatch for {relative}')
            head = git_output(source, 'show', f'HEAD:{relative}').replace(b'\r\n', b'\n')
            if sha256(head) != current_hash:
                expected_tracked.add(relative)
        expected_untracked.add('RUNTIME-SOURCE.json')

    diagnostics_manifest_path = source / 'DIAGNOSTICS-SOURCE.json'
    diagnostics_applied = diagnostics_manifest_path.exists()
    if diagnostics_applied:
        patch = root / 'renderer.patch'
        overlay_json = root / 'overlay.json'
        relative = 'ryty_gpu/RytyGpu.cmake'
        manifest = json.loads(diagnostics_manifest_path.read_text(encoding='utf-8'))
        cmake_hash = sha256(normalized_bytes(source / relative))
        if (manifest.get('schema') != 1 or manifest.get('renderer_commit') != actual
                or manifest.get('patch_sha256') != sha256(patch.read_bytes())
                or manifest.get('overlay_sha256') != sha256(overlay_json.read_bytes())
                or manifest.get('source_files') != {relative: cmake_hash}):
            raise RuntimeError('Existing diagnostics overlay manifest does not match CMake or renderer')
        head_cmake = git_output(source, 'show', f'HEAD:{relative}').replace(b'\r\n', b'\n')
        if sha256(head_cmake) != cmake_hash:
            expected_tracked.add(relative)
        expected_untracked.add('DIAGNOSTICS-SOURCE.json')
    tracked = set(git_output(source, 'diff', '--name-only').decode().splitlines())
    staged = set(git_output(source, 'diff', '--cached', '--name-only').decode().splitlines())
    untracked = set(git_output(source, 'ls-files', '--others', '--exclude-standard').decode().splitlines())
    if staged or tracked != expected_tracked or untracked != expected_untracked:
        raise RuntimeError('Renderer checkout has changes outside validated overlay manifests')
    return expected_tracked, expected_untracked, diagnostics_applied


def apply(destination):
    source = Path(destination).resolve()
    root = Path(__file__).resolve().parent
    spec = json.loads((root / 'overlay.json').read_text(encoding='utf-8'))
    actual = subprocess.check_output(
        ['git', '-c', f'safe.directory={source}', '-C', str(source), 'rev-parse', 'HEAD'],
        text=True).strip()
    expected = os.environ.get('RENDERER_SHA')
    if not expected or actual.lower() != expected.lower():
        raise RuntimeError(f'Diagnostics renderer checkout mismatch: expected {expected or "RENDERER_SHA"}, got {actual}')
    root = Path(__file__).resolve().parent
    expected_tracked, expected_untracked, diagnostics_applied = existing_state(source, actual, root)
    if diagnostics_applied:
        return
    diagnostics_manifest_path = source / 'DIAGNOSTICS-SOURCE.json'
    patch = root / 'renderer.patch'
    relative = 'ryty_gpu/RytyGpu.cmake'
    patch_files = {line[6:] for line in patch.read_text(encoding='utf-8').splitlines()
                   if line.startswith('--- a/')}
    if patch_files != {relative} or spec['files']:
        raise RuntimeError(f'Unexpected diagnostics overlay paths: {sorted(patch_files)}')
    # This overlay edits only CMake. Do not pin an unrelated native renderer file.
    cmake = source / relative
    original_cmake = cmake.read_bytes()
    original_manifest = diagnostics_manifest_path.read_bytes() if diagnostics_manifest_path.exists() else None
    git_prefix = ['git', '-c', f'safe.directory={source}', '-C', str(source)]
    try:
        atomic_replace(cmake, original_cmake.replace(b'\r\n', b'\n'))
        subprocess.run([*git_prefix, 'apply', '--check', '--whitespace=error', str(patch)], check=True)
        subprocess.run([*git_prefix, 'apply', '--whitespace=error', str(patch)], check=True)
        cmake_hash = sha256(normalized_bytes(cmake))
        head_cmake = git_output(source, 'show', f'HEAD:{relative}').replace(b'\r\n', b'\n')
        changed_expected = expected_tracked | ({relative} if sha256(head_cmake) != cmake_hash else set())
        changed = set(subprocess.check_output(
            [*git_prefix, 'diff', '--name-only'], text=True).splitlines())
        if changed != changed_expected:
            raise RuntimeError(f'Unexpected renderer changes after diagnostics overlay: {sorted(changed ^ changed_expected)}')
        manifest = {
            'schema': 1,
            'renderer_commit': actual,
            'patch_sha256': sha256(patch.read_bytes()),
            'overlay_sha256': sha256((root / 'overlay.json').read_bytes()),
            'source_files': {relative: cmake_hash},
        }
        atomic_replace(diagnostics_manifest_path, (json.dumps(manifest, indent=2) + '\n').encode())
        existing_state(source, actual, root)
    except Exception:
        atomic_replace(cmake, original_cmake)
        if original_manifest is None:
            diagnostics_manifest_path.unlink(missing_ok=True)
        else:
            atomic_replace(diagnostics_manifest_path, original_manifest)
        raise


if __name__ == '__main__':
    apply(sys.argv[1])
