# Streaming upload and recorder fixes - 2026-10-29

Renderer revision: `5e8d5cf7c8877176dc7d6eef7559f9f193ac6070` (`rygt-team/ShadGT`, `ryty-gpu`). These changes are enabled by normal renderer behavior and do not require diagnostic masks. The existing CI configuration builds Discord RPC with `ENABLE_DISCORD_RPC=ON`.

Large CPU-origin textures now remain dirty until used, including when old backing is unmapped. A drained batch processes each image once: duplicate admissions cannot consume a CPU write arriving during its first snapshot. That write remains dirty and is uploaded at the next actual use. GPU-written data keeps the ordered GPU-source path. The deterministic old-behavior GPU test fails; the corrected snapshot and next-use test passes.

The renderer also retains frozen CPU-only snapshots, local texture upload reuse, gap-only GPU-region initialization, bounded asynchronous geometry preparation, mapping-aware readability reuse, imported-view retirement, background diagnostics, parallel shader-store reading and bounded gameplay compilation. Descriptor host updates are combined per draw while preserving write records and original per-set bind/push order. Translator/cache formats remain compatible.

Validation: both new CMake tests pass (100,000 queue cases and 10,240 descriptor plans), the standalone NVIDIA descriptor test verifies 1,024 outputs, the full NVIDIA image/lifetime suite passes, and all 2,766 package imports resolve. The installed candidate binary is SHA-256 `9d56aee262dbe37d2b6f9bf2fc5d9c8ce14e91ae93b7e500af6809ecfb218049`; publication adds only standalone test registration/source and documentation to its rendering sources.

Two moving-scene 30-second captures logged four >=100 ms frames before duplicate-drain correction and one afterward (100 ms). The largest observed GPU-list span fell from 41.478 to 18.008 ms; the previous 18-copy/402.7 MB texture storm was not present in the latter sample. These intervals differ in streaming work and are not a deterministic benchmark. Remaining long frames and sustained 16.6 ms performance are unresolved; AMD runtime compatibility has not been retested in this session.
