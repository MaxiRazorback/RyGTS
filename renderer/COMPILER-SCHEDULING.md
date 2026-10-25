# Compiler scheduling

Apply `shadGT-patches/0082-worker-owned-compiler-scheduling.patch` after the existing renderer patches through 0072. Patch 0081 is independent; shader corrections on shader_fixes also apply independently.

Graphics and compute pipeline construction runs on owned worker jobs. Required outputs still wait for completion; compilation is not moved onto the recorder as a fallback. Producers and workers are joined while cache and descriptor dependencies remain alive. Request-specific translation waits match hardware/software stages, runtime specialization and bindings. Required pending builds are promoted ahead of cosmetic queued work, with an atomic claim preventing duplicate compilation.

Translation and pipeline pools share max(1, logical_threads - 2) workers. When there is only one worker it belongs to pipeline construction and translation keeps its required synchronous fallback. Workers can use all available cores at low priority; this is a budget, not exclusive core reservation. Heavy tessellated jobs enter the queue only when fewer than two are running, leaving other workers available for ordinary work. Existing driver heavy-build protection remains.

No bounded startup warm-up policy, history changes, diagnostic probes, event timing hooks or experimental descriptor caches are included.

Validation: 1,024 identical stored pipelines, restored cache fixtures, warm driver cache, ABBA order. Mean compilation elapsed time changed from 2.569 s to 1.988 s (22.6% lower); CPU seconds increased from 8.73 to 12.27. This does not establish cold shader translation or on-track hitch improvement; the user reported unchanged on-track hitches. Queue admission, priority, lifetime, translation matching and worker-budget tests pass against the extracted headers. Syntax checks pass for the extracted pipeline translation unit; the original candidate passed Release and 2,610 local import checks. The later combined build's LLVM OOM remains under investigation; these results do not establish unlimited-session memory stability.

Host tests under renderer/compiler-scheduling-tests compile against the patched shadGT src include directory, using C++20 or newer with assertions enabled (do not define NDEBUG). Run each resulting executable. Tests cover topology counts 0-1024, urgent promotion/duplicate ownership, worker-owned lifetimes, and ordinary work bypassing two active heavy builds.
