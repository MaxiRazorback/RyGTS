"""Apply the reviewed, source-pinned production renderer overlay."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_bytes(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def git(source, *arguments):
    subprocess.run(['git', '-c', f'safe.directory={source}', '-C', str(source), *arguments], check=True)


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


def apply(destination):
    source = Path(destination).resolve()
    spec = json.loads((Path(__file__).with_name('overlay.json')).read_text(encoding='utf-8'))
    actual = subprocess.check_output(
        ['git', '-c', f'safe.directory={source}', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()

    files = spec['source_files']
    for relative in files:
        path_part = PurePosixPath(relative)
        if path_part.is_absolute() or '..' in path_part.parts or not path_part.parts:
            raise RuntimeError(f'Invalid overlay path: {relative}')
    validate_files(source, files)
    # git apply expects consistent LF context even when Windows checked out CRLF.
    for relative, expected in files.items():
        if expected['baseline_sha256'] is not None:
            path = source.joinpath(*PurePosixPath(relative).parts)
            path.write_bytes(normalized_bytes(path))

    patch = Path(__file__).with_name('production-source.patch')
    git(source, 'apply', '--check', '--whitespace=error', str(patch))
    git(source, 'apply', '--whitespace=error', str(patch))
    validate_files(source, files, final=True)

    manifest = {
        'schema': 1,
        'renderer_commit': actual,
        'overlay_sha256': sha256(patch.read_bytes()),
        'source_files': files,
    }
    (source / 'RUNTIME-SOURCE.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: apply.py <prepared-renderer-checkout>')
    apply(sys.argv[1])
