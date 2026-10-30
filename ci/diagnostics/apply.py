"""Apply the diagnostics-only overlay to the independently prepared renderer checkout."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def apply(destination):
    source = Path(destination).resolve()
    root = Path(__file__).resolve().parent
    spec = json.loads((root / 'overlay.json').read_text())
    actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != spec['renderer_commit']:
        raise RuntimeError('Rebase and validate the diagnostics overlay when changing the renderer pin')
    native = source / 'src/video_core/renderer_vulkan/vk_rasterizer_native.cpp'
    # Git on Windows may check out CRLF; patch identity is defined over LF source.
    if hashlib.sha256(native.read_text().encode()).hexdigest() != spec['base_native_sha256']:
        raise RuntimeError('Diagnostics overlay source mismatch')
    for relative in ('src/video_core/renderer_vulkan/vk_rasterizer_native.cpp', 'ryty_gpu/RytyGpu.cmake'):
        file = source / relative
        file.write_bytes(file.read_bytes().replace(b'\r\n', b'\n'))
    patch = root / 'renderer.patch'
    subprocess.run(['git', '-C', str(source), 'apply', '--check', '--whitespace=error', str(patch)], check=True)
    subprocess.run(['git', '-C', str(source), 'apply', '--whitespace=error', str(patch)], check=True)
    for name in spec['files']:
        if Path(name).name != name:
            raise RuntimeError('Invalid overlay file path')
        target = native.parent / name
        if target.exists():
            raise RuntimeError(f'Overlay would overwrite an existing header: {name}')
        shutil.copy2(root / name, target)
    payloads = [patch, root / 'overlay.json', *(root / name for name in spec['files'])]
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in payloads}
    (source / 'DIAGNOSTICS-SOURCE.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    apply(sys.argv[1])
