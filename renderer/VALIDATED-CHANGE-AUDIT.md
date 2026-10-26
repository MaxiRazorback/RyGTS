# Validated investigation changes audited for development

October26,2026 source publication audit. This covers the locally recorded AMD/resolution/performance investigation; uncommitted source alone is not validation.

| Change | Development status |
| --- | --- |
| Queued fetch-input lifetime crash correction | df6617a |
| Three fragment buffer-descriptor improvements | c5aba4c, opt-in |
| Game/renderer SHA-256 cache identity and obsolete-cache cleanup | c2a4efd |
| Bounded zero-copy compute prefix for d0af5a54 | 9aaea69, opt-in |
| Fixed960x540 scene /1920x1080 output | Newly published patch0088; opt-in |
| Scene-resolution composition with normal-resolution HUD | Newly published patch0089; opt-in quality/performance option |

The resolution helper and documentation accompany0088/0089. The generalized launcher preset experiment remains unverified and is excluded. Main branch is unchanged.

Rejected/no demonstrated benefit and excluded: generic SPIR-V cleanup, full-range compute descriptor fallback (Preparing slowdown and heavy gathers), material descriptor fallback, broader compute-prefix eligibility, and cached composition access-mode specialization. Diagnostic profiler/readback tools, pointer traces, crash evidence, game binaries and shader caches are not part of these source changes.

Earlier warm-up learning/reuse tests passed, but a later memory/crash investigation remains unresolved; those observations do not justify publishing that mixed local experiment as validated here. Other dirty launcher/source edits require their own review and recorded verification; they are not swept into these commits.
