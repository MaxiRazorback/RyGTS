"""Small x64 instruction decoder for byte-load offsets used by frame capture."""
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
        if modrm >> 6 != 0b10:  # Require a 32-bit displacement.
            i = start + 1
            continue
        displacement_at = i + 3
        if modrm & 7 == 4:  # SIB follows the ModRM byte.
            displacement_at += 1
        end = displacement_at + 4
        if end > len(code):
            i = start + 1
            continue
        displacement = struct.unpack_from("<i", code, displacement_at)[0]
        yield start, end, displacement
        i = end
