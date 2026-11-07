# Shader cache persistence

The launcher preserves shader caches across game executable, renderer binary and GPU identity changes. This applies to both Release and Diagnostics builds. Setup and Play no longer hash those identities to purge managed CUSA directories, shader archives, else-scope markers or the shader-pack stamp.

Existing `shaders/cache-identity.sha256` files are ignored and left in place. The launcher no longer removes `.outdated` directories through this identity check. No user cache files need to be deleted or migrated for this change.

Portable-cache migration, shader-pack preparation and the game-closed guard remain. A changed shader pack can still prepare new program entries from the user's game files. Executable integrity checks and rebuild records remain separate and are not removed.

This removes the launcher's binary/GPU identity purge, not the renderer's cache-format/version policies or the driver's own pipeline-cache compatibility handling.

The removed `ShaderCacheIdentity` helper and its obsolete deletion tests are no longer part of the launcher source/build. Live shader caches are not touched by the source change or launcher compilation.
