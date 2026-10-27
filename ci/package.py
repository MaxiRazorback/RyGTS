"""Assemble redistributable Windows package from same-pipeline build artifacts."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import urllib.request
import zipfile

BASE_URL = ('https://gitlab.com/api/v4/projects/rygt-team%2FRyGT/packages/generic/'
            'gt-sport-prerelease/gt-sport-2026-10-25/'
            'GTSport-Ryty-shadGT-2026-10-25-prerelease%2Ezip')
BASE_SHA = '563349eb82d091d16a7d6864dca437d17a6dd3aee6f994d256399bf29aae7702'
BASE_FOLDER = 'GTSport-Ryty-shadGT-2026-10-25-prerelease'
FORBIDDEN = {'.self', '.elf', '.sprx', '.pkg', '.vol', '.adc', '.log', '.pdb'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_artifact(folder, filename, commit):
    actual_commit = (folder / 'RYGT-COMMIT.txt').read_text(encoding='utf-8-sig').strip()
    if actual_commit != commit:
        raise RuntimeError(f'Artifact revision mismatch: {folder}')
    entries = {}
    for line in (folder / 'SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
        digest, name = line.split('  ', 1)
        if Path(name).name != name or not re.fullmatch('[0-9a-fA-F]{64}', digest):
            raise RuntimeError('Invalid artifact manifest entry')
        if sha(folder / name) != digest.lower():
            raise RuntimeError(f'Artifact checksum mismatch: {name}')
        entries[name] = digest
    if filename not in entries:
        raise RuntimeError(f'Missing artifact checksum: {filename}')
    if (folder / filename).read_bytes()[:2] != b'MZ':
        raise RuntimeError(f'Expected Windows PE artifact: {filename}')
    return folder / filename


def package():
    commit = os.environ['CI_COMMIT_SHA']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise RuntimeError('Invalid source revision')
    launcher = verify_artifact(Path('artifacts/launcher'), 'RyGT.exe', commit)
    renderer = verify_artifact(Path('artifacts/renderer'), 'libSceVideoOut.prx', commit)
    base = Path(os.environ.get('RYGT_PACKAGE_BASE', '.ci-runtime-base.zip'))
    if not base.exists():
        headers = {}
        if os.environ.get('CI_JOB_TOKEN'):
            headers['JOB-TOKEN'] = os.environ['CI_JOB_TOKEN']
        with urllib.request.urlopen(urllib.request.Request(BASE_URL, headers=headers)) as response:
            with base.open('wb') as output:
                shutil.copyfileobj(response, output)
    if sha(base) != BASE_SHA:
        raise RuntimeError('Pinned runtime archive checksum mismatch')
    name = 'RyGT-development-' + commit[:8]
    destination = Path('dist')
    stage = destination / name
    stage.mkdir(parents=True, exist_ok=False)
    copied = set()
    with zipfile.ZipFile(base) as archive:
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in entry.filename
                    or not path.parts or path.parts[0] != BASE_FOLDER):
                raise RuntimeError('Unsafe runtime archive path')
            if entry.is_dir():
                continue
            relative = PurePosixPath(*path.parts[1:])
            lowered = relative.as_posix().lower()
            if (relative.suffix.lower() in FORBIDDEN or lowered == 'gtsport.exe'
                    or any(p.lower() in {'app0', 'sys', 'shaders', 'logs', 'saves', '_sd', 'convert'}
                           for p in relative.parts)
                    or (relative.parts[0].lower() == 'user' and
                        lowered != 'user/custom_configs/cusa03220.json')
                    or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise RuntimeError(f'Forbidden runtime package content: {relative}')
            if lowered in {'build_info.txt', 'sha256sums.txt', 'readme.txt', 'rygt.exe',
                           'libs/libscevideoout.prx'}:
                continue
            if lowered in copied:
                raise RuntimeError('Duplicate package path')
            copied.add(lowered)
            target = stage / relative.as_posix()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(entry))
    shutil.copy2(Path(__file__).resolve().parent.parent / 'LICENSE', stage / 'LICENSE')
    shutil.copy2(launcher, stage / 'RyGT.exe')
    shutil.copy2(renderer, stage / 'libs/libSceVideoOut.prx')
    required = ['converter/ryty.exe', 'tools/adcpatch/adcpatch.exe',
                'libs/libSceBluetoothHid.prx', 'amd_fidelityfx_vk.dll',
                'amd_fidelityfx_vk-LICENSE.txt', 'launcher/background.png',
                'user/custom_configs/CUSA03220.json']
    for item in required:
        if not (stage / item).is_file():
            raise RuntimeError(f'Incomplete runtime package: {item}')
    (stage / 'README.txt').write_text(
        'RyGT development CI package\n\n'
        'Run RyGT.exe to set up your own decrypted GT Sport CUSA03220 v1.69 dump.\n'
        'Game executable/data, firmware, saves, caches and NVIDIA SDK DLLs are excluded.\n'
        'Supply required firmware modules and optional NVIDIA upscaler files yourself.\n'
        'Launcher and libSceVideoOut are built from this pipeline revision.\n'
        'Other runtime libraries and Windows conversion helpers are retained from the\n'
        'checksummed October 25 prerelease; they are not rebuilt by this pipeline.\n'
        'This is a development artifact, not an automatically published release.\n'
        'See BUILD_INFO.txt, SHA256SUMS.txt and LINUX.txt.\n', encoding='utf-8')
    provenance = {
        'commit': commit, 'pipeline': os.environ.get('CI_PIPELINE_URL'),
        'runtime_base_url': BASE_URL, 'runtime_base_sha256': BASE_SHA,
        'rebuilt': ['RyGT.exe', 'libs/libSceVideoOut.prx'],
        'retained': 'All other redistributable runtime files from pinned prerelease',
        'renderer_source': Path('artifacts/renderer/CI-SOURCE.txt').read_text(encoding='utf-8-sig'),
    }
    (stage / 'BUILD_INFO.txt').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    manifest = {f.relative_to(stage).as_posix(): sha(f)
                for f in sorted(stage.rglob('*')) if f.is_file()}
    (stage / 'SHA256SUMS.txt').write_text(
        ''.join(f'{digest}  {filename}\n' for filename, digest in manifest.items()), encoding='utf-8')
    result = destination / (name + '.zip')
    with zipfile.ZipFile(result, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(stage.rglob('*')):
            if file.is_file():
                archive.write(file, file.relative_to(destination).as_posix())
    with zipfile.ZipFile(result) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity failure')
        for filename, digest in manifest.items():
            if hashlib.sha256(archive.read(name + '/' + filename)).hexdigest() != digest:
                raise RuntimeError('Packaged file checksum mismatch')
    (destination / (result.name + '.sha256')).write_text(
        sha(result) + '  ' + result.name + '\n', encoding='utf-8')
    print(f'Packaged and verified {len(manifest) + 1} files: {result}')


if __name__ == '__main__':
    package()
