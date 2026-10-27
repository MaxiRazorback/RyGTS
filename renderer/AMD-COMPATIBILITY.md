# Automatic AMD compatibility

Patch 0098 includes the Native renderer compressed-image fallback that was previously present only in the local investigation build. The older texture-cache fallback alone did not cover Native rendering, so the CI package could still report missing BC6H/BC5 images.

No environment variable or launcher option is required. The active Vulkan device is queried with the actual format and image usage. If a block-compressed image rejects storage usage, the renderer retries with sampling and transfers, preserving the original compressed format and HDR content. Drivers accepting the original request retain that path. This capability check covers AMD without guessing support from a GPU generation; other vendors retain their accepted path too.

Both immediate and prepared descriptor paths refuse writable storage bindings for images created without storage usage. Unsupported required storage is not silently emulated.

Existing published AMD family/driver profiles remain automatic. Do not enable all diagnostic switches: KHR material comparisons and separate-W experiments have not established a general road/car fix. This change addresses the confirmed image allocation rejection, not every remaining material defect. Polaris through RDNA generations still need hardware validation individually.

The local sampled-only candidate previously restored the skybox on Radeon 610M. The CI package must be rebuilt with this patch before its installed binaries contain the fix.

Patch 0099 enables the validated composition and two post-processing fragment descriptor paths, plus the single-shader zero-copy 4 KiB compute prefix, automatically for Vulkan vendor ID 0x1002 (AMD). Other vendors retain the previous default. Existing RYGT_COMPOSITION_BUFFER_DESCRIPTORS, RYGT_POSTPROCESS_BUFFER_DESCRIPTORS and RYGT_COMPUTE_PREFIX_DESCRIPTOR overrides remain available: 0 disables, 1 enables. These are runtime binding choices; no shader interface or shader-store revision changes. Unsupported imports still use their existing fallback checks. Broad compute gathers and the unsuccessful material experiment remain off.
