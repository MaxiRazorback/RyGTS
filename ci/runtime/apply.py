"""Apply the reviewed, source-pinned production renderer overlay."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_bytes(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def atomic_replace(path, contents):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(contents)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_transaction(source, original_bytes, merged, manifest_path, manifest_bytes, validate):
    """Restore exact pre-write bytes on apply or validation failure; persistent disk failure may block rollback."""
    original_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
    replaced = []
    try:
        for relative, contents in merged.items():
            path = source.joinpath(*PurePosixPath(relative).parts)
            atomic_replace(path, contents)
            replaced.append(path)
        atomic_replace(manifest_path, manifest_bytes)
        validate()
    except Exception:
        for path in reversed(replaced):
            relative = path.relative_to(source).as_posix()
            atomic_replace(path, original_bytes[relative])
        if original_manifest is None:
            manifest_path.unlink(missing_ok=True)
        else:
            atomic_replace(manifest_path, original_manifest)
        raise


def git(source, *arguments):
    subprocess.run(['git', '-c', f'safe.directory={source}', '-C', str(source), *arguments], check=True)


def git_output(source, *arguments):
    return subprocess.check_output(
        ['git', '-c', f'safe.directory={source}', '-C', str(source), *arguments])


def validate_files(source, files, *, final=False):
    for relative, expected in files.items():
        path = source.joinpath(*PurePosixPath(relative).parts)
        if path.resolve().is_relative_to(source.resolve()) is False:
            raise RuntimeError(f'Overlay path escapes renderer checkout: {relative}')
        wanted = expected['new_sha256' if final else 'baseline_sha256']
        actual = sha256(normalized_bytes(path)) if path.is_file() else None
        if actual != wanted:
            state = 'postimage' if final else 'baseline'
            raise RuntimeError(f'Renderer {state} mismatch for {relative}: expected {wanted}, got {actual}')


def source_state(source, actual, runtime_files, runtime_patch):
    """Accept only clean source or the exact manifest-backed counterpart overlay."""
    root = Path(__file__).resolve().parents[1]
    expected_tracked = set()
    expected_untracked = set()
    runtime_manifest_path = source / 'RUNTIME-SOURCE.json'
    if runtime_manifest_path.exists():
        manifest = json.loads(runtime_manifest_path.read_text(encoding='utf-8'))
        if (manifest.get('schema') != 2 or manifest.get('renderer_commit') != actual
                or manifest.get('overlay_sha256') != sha256(runtime_patch.read_bytes())):
            raise RuntimeError('Existing runtime overlay manifest does not match this renderer and patch')
        entries = manifest.get('source_files', {})
        if set(entries) != set(runtime_files):
            raise RuntimeError('Existing runtime overlay manifest file list mismatch')
        for relative, expected in runtime_files.items():
            entry = entries[relative]
            path = source.joinpath(*PurePosixPath(relative).parts)
            if (entry.get('baseline_sha256') != expected['baseline_sha256']
                    or entry.get('overlay_sha256') != expected['new_sha256']
                    or entry.get('overlay_postimage_verified') is not True
                    or entry.get('merged_sha256') != sha256(normalized_bytes(path))):
                raise RuntimeError(f'Existing runtime overlay postimage mismatch for {relative}')
            head = git_output(source, 'show', f'HEAD:{relative}').replace(b'\r\n', b'\n')
            if sha256(head) != sha256(normalized_bytes(path)):
                expected_tracked.add(relative)
        expected_untracked.add('RUNTIME-SOURCE.json')

    diagnostics_manifest_path = source / 'DIAGNOSTICS-SOURCE.json'
    if diagnostics_manifest_path.exists():
        diagnostics_root = root / 'diagnostics'
        diagnostics_patch = diagnostics_root / 'renderer.patch'
        diagnostics_manifest = json.loads(diagnostics_manifest_path.read_text(encoding='utf-8'))
        relative = 'ryty_gpu/RytyGpu.cmake'
        cmake = source / relative
        cmake_hash = sha256(normalized_bytes(cmake))
        if (diagnostics_manifest.get('renderer_commit') != actual
                or diagnostics_manifest.get('patch_sha256') != sha256(diagnostics_patch.read_bytes())
                or diagnostics_manifest.get('overlay_sha256') != sha256((diagnostics_root / 'overlay.json').read_bytes())
                or diagnostics_manifest.get('source_files') != {relative: cmake_hash}):
            raise RuntimeError('Existing diagnostics overlay manifest does not match CMake or renderer')
        patch_files = {line[6:] for line in diagnostics_patch.read_text(encoding='utf-8').splitlines()
                       if line.startswith('--- a/')}
        if patch_files != {relative}:
            raise RuntimeError('Diagnostics overlay path set changed')
        head = git_output(source, 'show', f'HEAD:{relative}').replace(b'\r\n', b'\n')
        if sha256(head) != cmake_hash:
            expected_tracked.add(relative)
        expected_untracked.add('DIAGNOSTICS-SOURCE.json')

    tracked = set(git_output(source, 'diff', '--name-only').decode().splitlines())
    staged = set(git_output(source, 'diff', '--cached', '--name-only').decode().splitlines())
    untracked = set(git_output(source, 'ls-files', '--others', '--exclude-standard').decode().splitlines())
    if staged or tracked != expected_tracked or untracked != expected_untracked:
        raise RuntimeError('Renderer checkout has changes outside validated overlay manifests')
    return runtime_manifest_path.exists(), tracked


def git_hash_object(source, contents, *, write=False):
    arguments = ['hash-object']
    if write:
        arguments.append('-w')
    arguments.append('--stdin')
    return subprocess.check_output(
        ['git', '-c', f'safe.directory={source}', '-C', str(source), *arguments],
        input=contents).decode().strip()


def prepare_three_way(source, base_commit, patch, files, temp_root):
    for relative in files:
        path_part = PurePosixPath(relative)
        if path_part.is_absolute() or '..' in path_part.parts or not path_part.parts:
            raise RuntimeError(f'Invalid overlay path: {relative}')
    patch_files = {line[6:].strip() for line in patch.read_text(encoding='utf-8').splitlines()
                   if line.startswith('--- a/')}
    if patch_files != set(files):
        raise RuntimeError('Overlay patch files do not match the guarded source files')

    base_root = temp_root / 'overlay-base'
    base_root.mkdir(parents=True)
    base_blobs = {}
    for relative, expected in files.items():
        path_part = PurePosixPath(relative)
        target = source.joinpath(*path_part.parts)
        if not target.resolve().is_relative_to(source.resolve()):
            raise RuntimeError(f'Overlay path escapes renderer checkout: {relative}')
        try:
            baseline = git_output(source, 'show', f'{base_commit}:{relative}').replace(b'\r\n', b'\n')
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f'Missing overlay baseline object for {relative}') from error
        if sha256(baseline) != expected['baseline_sha256']:
            raise RuntimeError(f'Overlay baseline object mismatch for {relative}')
        baseline_path = base_root.joinpath(*path_part.parts)
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(baseline)
        base_blobs[relative] = (baseline, git_hash_object(source, baseline))

    subprocess.run(['git', 'apply', '--check', '--whitespace=error', str(patch)],
                   cwd=base_root, check=True)
    subprocess.run(['git', 'apply', '--whitespace=error', str(patch)],
                   cwd=base_root, check=True)

    # Add full Git blob IDs to the reviewed patch so `git apply --3way` can use
    # the exact baseline and independently verified postimage objects.
    canonical_lines = []
    postimages = {}
    for line in patch.read_text(encoding='utf-8').splitlines(keepends=True):
        if line.startswith('--- a/'):
            relative = line[6:].strip()
            postimage = base_root.joinpath(*PurePosixPath(relative).parts).read_bytes().replace(b'\r\n', b'\n')
            if sha256(postimage) != files[relative]['new_sha256']:
                raise RuntimeError(f'Overlay postimage object mismatch for {relative}')
            postimages[relative] = postimage
            new_blob = git_hash_object(source, postimage, write=True)
            old_blob = base_blobs[relative][1]
            canonical_lines.extend((f'diff --git a/{relative} b/{relative}\n',
                                    f'index {old_blob}..{new_blob} 100644\n'))
        canonical_lines.append(line)
    canonical_patch = temp_root / 'canonical.patch'
    canonical_patch.write_text(''.join(canonical_lines), encoding='utf-8', newline='\n')

    original_bytes = {relative: source.joinpath(*PurePosixPath(relative).parts).read_bytes()
                      for relative in files}
    current = {relative: contents.replace(b'\r\n', b'\n')
               for relative, contents in original_bytes.items()}
    index = temp_root / 'overlay.index'
    env = os.environ.copy()
    env['GIT_INDEX_FILE'] = str(index)

    def indexed_git(*arguments, check=True):
        return subprocess.run(
            ['git', '-c', f'safe.directory={source}', '-C', str(source), *arguments],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

    indexed_git('read-tree', 'HEAD')
    applied = indexed_git('apply', '--cached', '--3way', '--whitespace=error',
                          str(canonical_patch), check=False)
    unmerged = indexed_git('ls-files', '-u').stdout
    if applied.returncode or unmerged:
        details = applied.stderr.decode(errors='replace').strip()
        raise RuntimeError(f'Overlay three-way merge conflicted; renderer checkout left unchanged: {details}')

    changed = set(indexed_git('diff', '--cached', '--name-only', 'HEAD').stdout.decode().splitlines())
    if not changed.issubset(set(files)):
        raise RuntimeError(f'Unexpected staged overlay paths: {sorted(changed - set(files))}')
    merged = {}
    for relative in files:
        blob = indexed_git('show', f':{relative}')
        if blob.returncode:
            raise RuntimeError(f'Missing merged stage-0 blob for {relative}')
        merged[relative] = blob.stdout
    return original_bytes, current, merged, postimages


def apply(destination):
    source = Path(destination).resolve()
    spec = json.loads((Path(__file__).with_name('overlay.json')).read_text(encoding='utf-8'))
    actual = git_output(source, 'rev-parse', 'HEAD').decode().strip()
    expected = os.environ.get('RENDERER_SHA')
    if not expected or actual.lower() != expected.lower():
        raise RuntimeError(f'Renderer checkout mismatch: expected {expected or "RENDERER_SHA"}, got {actual}')

    files = spec['source_files']
    for relative in files:
        path_part = PurePosixPath(relative)
        if path_part.is_absolute() or '..' in path_part.parts or not path_part.parts:
            raise RuntimeError(f'Invalid overlay path: {relative}')
    patch = Path(__file__).with_name('production-source.patch')
    base_commit = spec['renderer_commit']
    # Keep the overlay's reviewed base blob and postimage hashes authoritative while
    # replaying it over later renderer commits. Only a validated diagnostics overlay
    # may already be present before this overlay starts.
    already_applied, initial_tracked = source_state(source, actual, files, patch)
    if already_applied:
        return
    git(source, 'fetch', '--depth=1', 'origin', base_commit)
    if actual != base_commit:
        git(source, 'fetch', '--deepen=256', 'origin', actual)
        try:
            git(source, 'merge-base', '--is-ancestor', base_commit, actual)
        except subprocess.CalledProcessError as error:
            shallow = git_output(source, 'rev-parse', '--is-shallow-repository').decode().strip() == 'true'
            if not shallow:
                raise RuntimeError('Renderer commit is not descended from the reviewed overlay base') from error
            git(source, 'fetch', '--unshallow', 'origin', actual)
            try:
                git(source, 'merge-base', '--is-ancestor', base_commit, actual)
            except subprocess.CalledProcessError as unshallow_error:
                raise RuntimeError('Renderer commit is not descended from the reviewed overlay base') from unshallow_error
    with tempfile.TemporaryDirectory() as temp:
        original_bytes, current, merged, postimages = prepare_three_way(
            source, base_commit, patch, files, Path(temp))
    for relative, contents in current.items():
        if normalized_bytes(source.joinpath(*PurePosixPath(relative).parts)) != contents:
            raise RuntimeError(f'Renderer changed during overlay preflight: {relative}')
    changed_expected = {relative for relative, contents in merged.items()
                        if contents != current[relative]}

    manifest = {
        'schema': 2,
        'renderer_commit': actual,
        'overlay_sha256': sha256(patch.read_bytes()),
        'source_files': {relative: {
            'baseline_sha256': files[relative]['baseline_sha256'],
            'overlay_sha256': files[relative]['new_sha256'],
            'merged_sha256': sha256(contents),
            'overlay_postimage_verified': sha256(postimages[relative]) == files[relative]['new_sha256'],
        } for relative, contents in merged.items()},
    }
    manifest_path = source / 'RUNTIME-SOURCE.json'

    def verify_transaction():
        changed = set(git_output(source, 'diff', '--name-only').decode().splitlines())
        if changed != initial_tracked | changed_expected:
            raise RuntimeError(f'Unexpected renderer changes after overlay: {sorted(changed ^ (initial_tracked | changed_expected))}')
        for relative, contents in merged.items():
            path = source.joinpath(*PurePosixPath(relative).parts)
            if normalized_bytes(path) != contents:
                raise RuntimeError(f'Overlay merged postimage mismatch for {relative}')
        source_state(source, actual, files, patch)

    write_transaction(source, original_bytes, merged, manifest_path,
                      (json.dumps(manifest, indent=2) + '\n').encode(), verify_transaction)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: apply.py <prepared-renderer-checkout>')
    apply(sys.argv[1])
