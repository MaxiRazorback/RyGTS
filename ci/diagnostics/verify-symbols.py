"""Verify a PE CodeView identity against its PDB using pinned LLVM, before packaging."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import uuid


def codeview(data):
    if data[:2] != b'MZ':
        raise ValueError('Not a PE binary')
    pe = struct.unpack_from('<I', data, 60)[0]
    if data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')
    optional = pe + 24
    magic = struct.unpack_from('<H', data, optional)[0]
    directory = optional + {0x10b: 96, 0x20b: 112}[magic]
    debug_rva, size = struct.unpack_from('<II', data, directory + 6 * 8)
    sections = optional + struct.unpack_from('<H', data, pe + 20)[0]
    for i in range(struct.unpack_from('<H', data, pe + 6)[0]):
        virtual_size, rva, raw_size, raw = struct.unpack_from('<IIII', data, sections + i * 40 + 8)
        if rva <= debug_rva < rva + max(virtual_size, raw_size):
            start = raw + debug_rva - rva
            break
    else:
        raise ValueError('PE debug directory missing')
    identities = []
    for offset in range(start, start + size, 28):
        kind, count, _, pointer = struct.unpack_from('<IIII', data, offset + 12)
        if kind == 2 and count >= 24 and data[pointer:pointer + 4] == b'RSDS':
            identities.append((str(uuid.UUID(bytes_le=data[pointer + 4:pointer + 20])).lower(),
                               struct.unpack_from('<I', data, pointer + 20)[0]))
    if len(identities) != 1:
        raise ValueError('Exactly one RSDS CodeView record required')
    return identities[0]


def verify(binary, pdb, llvm_bin):
    binary, pdb = Path(binary), Path(pdb)
    identity = codeview(binary.read_bytes())
    report = subprocess.check_output([str(Path(llvm_bin) / 'llvm-pdbutil.exe'), 'dump', '-summary', str(pdb)], text=True)
    guid = re.search(r'(?im)^\s*Guid:\s*\{?([0-9a-f-]{36})\}?', report)
    age = re.search(r'(?im)^\s*Age:\s*(\d+)', report)
    if not guid or not age or (guid[1].lower(), int(age[1])) != identity:
        raise RuntimeError('PDB identity does not match the packaged binary')
    return dict(binary=binary.name, pdb=pdb.name, guid=identity[0], age=identity[1],
                binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                pdb_sha256=hashlib.sha256(pdb.read_bytes()).hexdigest())


if __name__ == '__main__':
    result = verify(*sys.argv[1:4])
    Path(sys.argv[4]).write_text(json.dumps(result, indent=2) + '\n')
