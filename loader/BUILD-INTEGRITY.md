# Game executable hash verification

The launcher records the complete prepared GTSport.exe SHA-256 in GTSport.exe.sha256 after successful setup. Preparation includes its icon and Windows GUI subsystem. On Play the background preparation thread verifies that record. Matching files start normally; a missing, malformed or mismatched record invokes the normal setup/rebuild routine from the configured game and firmware sources. Source folders must still be available when a rebuild is required.

Conversion writes a staging GTSport.exe first. After conversion and icon/subsystem preparation succeed, generated guest modules and the registry are installed and the staged EXE replaces the previous one. A running/in-use EXE cannot be rebuilt. Setup records the new hash only after finishing. Verification or rebuild failure prevents Play from starting the game and leaves the reason in the setup log. Rebuilds use the complete existing setup routine, including normal file linking and script preparation.

This is a local integrity/build record, not a publisher signature or a defense against somebody who changes both the executable and its record. It does not check every module or detect a converter update by itself.

Validation on 2026-10-25: two independent fresh unwrap/converter/launcher-preparation runs produced identical raw and prepared hashes. Prepared SHA-256 for the tested local 1.69 inputs and converter:
907B853CE14EF93FC4E0C7751D079D5D2CFEE8CF8C3B54475B173D832F3EE490
This is test evidence for those inputs, not a universal hash for all future builds/platforms. The actual updated setup flow and an intentionally modified isolated executable were also tested; the rebuild restored this exact hash. No installed game executable was replaced during the tests.