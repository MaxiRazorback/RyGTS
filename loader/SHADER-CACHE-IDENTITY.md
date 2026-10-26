# Shader cache identity

Launcher source: loader/ShaderCacheIdentity.cs, called after portable-cache migration and before shader-pack preparation during Setup and Play. SHA-256 fingerprints cover the generated GTSport.exe and libs/libSceVideoOut.prx. The stamp is shaders/cache-identity.sha256. Hashes are compatibility fingerprints, not signatures or trusted provenance.

Missing or changed identity removes managed CUSA cache directories (plain/direct-sets), archive caches, else-scope markers and the shader-pack stamp. Existing .outdated directories are removed even when identity matches. Unrelated files are retained. No old shader directory is renamed or preserved. Cache is rebuilt/prepared on demand; this does not compile every unseen game shader before launch.

Cleanup requires the game closed, refuses reparse points, validates every selected tree before deletion, and publishes its identity only after successful cleanup. Missing binaries or cleanup failures abort the launch. Every renderer binary change currently invalidates the cache conservatively, even if its shader compiler is unchanged. Directly launching GTSport.exe bypasses launcher identity validation.

Renderer cache_storage.cpp also deletes version-incompatible stores instead of renaming them to .outdated. Failure stops cache opening. Existing renderer store-version policies remain in effect.

Tests passed in temporary fixture folders: missing stamp invalidation, matching stamp reuse, executable change, renderer change, old-backup removal, unrelated-file retention and missing-binary failure before deletion. Launcher compiled with existing CS1690 UI warning. No live game cache was deleted or migrated during development/testing. Candidate launcher is in this directory; installation/runtime validation remains separate.
