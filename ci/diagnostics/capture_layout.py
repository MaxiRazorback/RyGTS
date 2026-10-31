"""Small x64 instruction decoder for byte-load offsets used by frame capture."""
import re
import struct


def movzx_byte_loads(code):
    """Yield (instruction_start, instruction_end, displacement) for MOVZX r32/m8 forms."""
    legacy_prefixes = {0x2E, 0x36, 0x3E, 0x26, 0x64, 0x65, 0x66, 0x67, 0xF0, 0xF2, 0xF3}
    i = 0
    while i < len(code):
        start = i
        while i < len(code) and (code[i] in legacy_prefixes or 0x40 <= code[i] <= 0x4F):
            i += 1
        if code[i:i + 2] != b"\x0f\xb6" or i + 3 > len(code):
            i = start + 1
            continue

        modrm = code[i + 2]
        mod = modrm >> 6
        rm = modrm & 7
        if mod == 0b11:  # Register source, not a memory byte load.
            i = start + 1
            continue

        sib = rm == 4
        displacement_at = i + 3 + int(sib)
        sib_base = code[i + 3] & 7 if sib and i + 3 < len(code) else None
        if mod == 0:
            # [RIP+disp32] or SIB with no base carries a displacement despite mod=00.
            displacement_size = 4 if rm == 5 or (sib and sib_base == 5) else 0
        elif mod == 1:
            displacement_size = 1
        else:  # mod == 2
            displacement_size = 4
        end = displacement_at + displacement_size
        if end > len(code):
            i = start + 1
            continue
        if displacement_size == 1:
            displacement = struct.unpack_from("<b", code, displacement_at)[0]
        elif displacement_size == 4:
            displacement = struct.unpack_from("<i", code, displacement_at)[0]
        else:
            displacement = 0
        yield start, end, displacement
        i = max(end, start + 1)


def pdb_procedure_size(dump, name):
    """Read the CodeView procedure code size for a named PDB symbol."""
    lines = dump.splitlines()
    sizes = []
    for i, line in enumerate(lines):
        if name in line:
            match = re.search(r"code size\s*=\s*(\d+)", "\n".join(lines[i:i + 3]))
            if match:
                sizes.append(int(match.group(1)))
    return max(sizes, default=0)


def pe_image_base(pe, pe_offset):
    """Read ImageBase using its offset within the PE optional header."""
    optional = pe_offset + 24
    magic = struct.unpack_from("<H", pe, optional)[0]
    if magic == 0x20B:
        return struct.unpack_from("<Q", pe, optional + 24)[0]
    if magic == 0x10B:
        return struct.unpack_from("<I", pe, optional + 28)[0]
    raise ValueError(f"unsupported PE optional-header magic: {magic:#x}")
