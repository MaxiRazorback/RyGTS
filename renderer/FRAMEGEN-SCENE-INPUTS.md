# Frame generation scene inputs

Patch 0093 snapshots actual R32 scene depth, motion vectors, jitter and render dimensions per presentation Frame. Ready semaphores order copies before FG preparation; the presentation fence protects reuse. Blank/reused frames do not inherit stale scene metadata. Existing compilation pause and cooldown dependencies remain.

When temporal FSR is selected, generation requires matching scene inputs. Disabled generation returns before auxiliary compute work, so intro and 2D frames retain ordinary presentation. Existing standalone optical-flow fallback remains available when temporal FSR is not requested.

Validation: renderer build, 2,893 import checks and image self-test. Intro presentation returned to approximately 57?59 real FPS in the recorded test; logs confirmed generation using real depth/motion in 3D. FG still has poor cost/pacing on the tested workload; this change does not claim smooth or faster gameplay.
