import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'diagnostics'))
from capture_layout import movzx_byte_loads


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

    def test_ignores_register_and_short_displacement_forms(self):
        code = b'\x0f\xb6\xc0\x0f\xb6\x46\x08\x0f\xb6\x81\x40\x00\x00\x00'
        self.assertEqual(list(movzx_byte_loads(code)), [(7, 14, 0x40)])

    def test_counts_repeated_displacements(self):
        code = (b'\x0f\xb6\x86\x50\x00\x00\x00'
                b'\x48\x0f\xb6\x81\x50\x00\x00\x00')
        self.assertEqual([item[2] for item in movzx_byte_loads(code)], [0x50, 0x50])


if __name__ == '__main__':
    unittest.main()
