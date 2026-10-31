import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'diagnostics'))
from capture_layout import movzx_byte_loads, pdb_procedure_size, pe_image_base


class CaptureLayoutTests(unittest.TestCase):
    def test_decodes_all_modrm_base_registers(self):
        for base in range(8):
            if base == 4:  # RSP/R12 requires a SIB byte.
                continue
            with self.subTest(base=base):
                modrm = 0x80 | base
                code = bytes((0x0F, 0xB6, modrm)) + (0x48).to_bytes(4, 'little', signed=True)
                self.assertEqual(list(movzx_byte_loads(code)), [(0, 7, 0x48)])

    def test_decodes_rex_and_sib_forms(self):
        rex = b'\x49\x0f\xb6\x85\x20\x00\x00\x00'
        sib = b'\x48\x0f\xb6\x84\x24\x38\x00\x00\x00'
        self.assertEqual(list(movzx_byte_loads(rex)), [(0, 8, 0x20)])
        self.assertEqual(list(movzx_byte_loads(sib)), [(0, 9, 0x38)])

    def test_decodes_signed_disp8_and_sib_disp8_forms(self):
        disp8 = b'\x0f\xb6\x41\x50'
        negative = b'\x0f\xb6\x41\xf0'
        sib = b'\x48\x0f\xb6\x44\x24\x50'
        self.assertEqual(list(movzx_byte_loads(disp8)), [(0, 4, 0x50)])
        self.assertEqual(list(movzx_byte_loads(negative)), [(0, 4, -16)])
        self.assertEqual(list(movzx_byte_loads(sib)), [(0, 6, 0x50)])

    def test_decodes_rip_relative_disp32_and_no_displacement(self):
        rip_relative = b'\x0f\xb6\x05\x10\x00\x00\x00'
        no_displacement = b'\x0f\xb6\x01'
        self.assertEqual(list(movzx_byte_loads(rip_relative)), [(0, 7, 0x10)])
        self.assertEqual(list(movzx_byte_loads(no_displacement)), [(0, 3, 0)])

    def test_ignores_register_form_and_decodes_short_displacement(self):
        code = b'\x0f\xb6\xc0\x0f\xb6\x46\x08\x0f\xb6\x81\x40\x00\x00\x00'
        self.assertEqual(list(movzx_byte_loads(code)), [(3, 7, 8), (7, 14, 0x40)])

    def test_counts_repeated_displacements(self):
        code = (b'\x0f\xb6\x86\x50\x00\x00\x00'
                b'\x48\x0f\xb6\x81\x50\x00\x00\x00')
        self.assertEqual([item[2] for item in movzx_byte_loads(code)], [0x50, 0x50])

    def test_reads_pdb_function_code_size_not_record_size(self):
        dump = (
            "12 | S_GPROC32 [size = 44] `?FrameDumpFlip@Rasterizer@Vulkan@@`\n"
            "parent = 0, end = 192, addr = 0001:1000, code size = 7168\n"
            "type = `void ()`, debug start = 4, debug end = 32\n"
        )
        self.assertEqual(pdb_procedure_size(dump, "FrameDumpFlip"), 7168)

    def test_reads_pe32_and_pe32_plus_image_base_from_optional_header(self):
        pe32_plus = bytearray(64)
        pe32_plus[24:26] = (0x20B).to_bytes(2, 'little')
        pe32_plus[48:56] = (0x140000000).to_bytes(8, 'little')
        pe32 = bytearray(64)
        pe32[24:26] = (0x10B).to_bytes(2, 'little')
        pe32[52:56] = (0x400000).to_bytes(4, 'little')
        self.assertEqual(pe_image_base(pe32_plus, 0), 0x140000000)
        self.assertEqual(pe_image_base(pe32, 0), 0x400000)


if __name__ == '__main__':
    unittest.main()
