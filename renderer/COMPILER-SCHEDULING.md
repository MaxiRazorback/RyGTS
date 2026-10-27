# Compiler scheduling

The renderer source is maintained as commits in ShadGT ryty-gpu and pinned by renderer/source.json. CI no longer applies a separate patch series.

Graphics and compute pipeline construction runs on owned worker jobs. Required outputs still wait for completion; compilation is not moved onto the recorder as a fallback. Producers and workers are joined while cache and descriptor dependencies remain alive. Request-specific translation waits match hardware/software stages, runtime specialization and bindings. Required pending builds are promoted ahead of cosmetic queued work, with an atomic claim preventing duplicate compilation.

Translation and pipeline pools share max(1, logical_threads - 2) workers. When there is only one worker it belongs to pipeline construction and translation keeps its required synchronous fallback. Workers can use all available cores at low priority; this is a budget, not exclusive core reservation. Heavy tessellated jobs are admitted one at a time, leaving other workers available for ordinary work. Queue admission and the final driver-call gate share the same limit. Two simultaneous tessellated builds exhausted process commit inside the NVIDIA compiler during a race-to-results transition; serial admission reduces their overlapping memory demand without changing shader generation.

No bounded startup warm-up policy, history changes, diagnostic probes, event timing hooks or experimental descriptor caches are included.

Validation: 1,024 identical stored pipelines, restored cache fixtures, warm driver cache, ABBA order. Mean compilation elapsed time changed from 2.569 s to 1.988 s (22.6% lower); CPU seconds increased from 8.73 to 12.27. This does not establish cold shader translation or on-track hitch improvement; the user reported unchanged on-track hitches. Queue admission, priority, lifetime, translation matching and worker-budget tests pass against the extracted headers. Syntax checks pass for the extracted pipeline translation unit; the original candidate passed Release and 2,610 local import checks. The later combined build's LLVM OOM remains under investigation; these results do not establish unlimited-session memory stability.

Host tests under renderer/compiler-scheduling-tests compile against the patched shadGT src include directory, using C++20 or newer with assertions enabled (do not define NDEBUG). Run each resulting executable. Tests cover topology counts 0-1024, urgent promotion/duplicate ownership, worker-owned lifetimes, and ordinary work bypassing blocked heavy builds, including urgent and boosted-background admission.

Crash-candidate validation: the combined renderer passed the Release build, all 2,893 import checks and the image self-test. The user reported sustained runtime stability and approved this candidate on October 27, 2026. This reduces concurrent compilation memory demand; it does not impose a bound on the memory needed by a single driver compilation.
