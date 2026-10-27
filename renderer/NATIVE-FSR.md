# Native FSR temporal reconstruction

Patch 0092 connects Native TAA inputs and final scene composition to the existing temporal FSR backend. It validates the full color/depth/motion/history set, dimensions, formats and jitter. Real D32 and D32+stencil depth is extracted into a separate R32 image; no D32-only view is created over a D32+stencil attachment. Native image references are non-owning and source layouts return to GENERAL. The existing resize/completion boundary is retained.

A scene-sized composition scratch image supplies the actual lower-resolution input while output and subsequent HUD draws retain normal resolution. Failure uses the existing fallback path. Native FSR presentation was confirmed across showroom/menu and race loads, and its active title remained present after the depth-alias correction. This is not validation of all temporal backends or a correction for unrelated AMD texture defects.

Validation: renderer build, 2,893 import checks, image self-test, repeated successful FSR dispatch/presentation and user rendering checks. The image self-test alone does not validate FSR motion or temporal quality.
