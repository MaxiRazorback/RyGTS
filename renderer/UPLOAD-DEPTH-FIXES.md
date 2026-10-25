# Immutable region uploads and depth-only compilation dependencies

Apply `shadGT-patches/0083-native-immutable-region-uploads-and-depth-bakes.patch` after the existing renderer patches through 0072. It is independent of the performance_fixes patches.

Native partial-region uploads now copy the compared CPU bytes into timeline-owned staging storage before recording a GPU copy. The GPU therefore reads the exact snapshot used to identify changed ranges, even if the guest rewrites the source before submission. GPU-only/unreadable pages continue to copy from their imported GPU backing. Existing allocation and completion lifetime rules retain the staging storage.

The depth-output predicate treats valid depth-writing draws with color output disabled as depth-only even when stale color attachments remain bound. Those required draws retain pipeline and translation waits, preserving one-time shadow bakes while ordinary cosmetic draws remain asynchronous.

Validation: the original Release candidate passed 2,610 local import checks, and the user confirmed correct first-load distant shadows and menu rendering with a separate fresh cache. Extracted patches pass application checks both independently and combined with performance_fixes, in either category order. Affected translation-unit syntax checks pass. No probe shaders, trace code, binaries, speculative color-corruption claim or startup warm-up changes are included.
