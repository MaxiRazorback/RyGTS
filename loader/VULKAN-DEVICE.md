# Vulkan device selection

Settings > Display > Vulkan device lists the devices reported by Vulkan, including
integrated and discrete GPUs. Automatic preserves the renderer's existing selection
policy. Choosing a device saves its UUID and the renderer's Vulkan.gpu_id in
user/custom_configs/CUSA03220.json. Before Play the launcher resolves the UUID to
its current Vulkan index. An unavailable device blocks Play and asks the user to
choose another device or Automatic; it is not silently replaced with another GPU.
The device must meet the renderer's existing Vulkan 1.3 requirements.

VulkanDevices.cs is built by loader/build.cmd and needs no extra packaged DLL.
Enumeration creates and destroys a temporary Vulkan instance; handles and unmanaged
query buffers are released on success and failure. Other configuration is preserved.

Fast flips is also presented under Display with its existing saved value and default.
It controls internal presentation scheduling, not monitor VRR.

Validated locally with AMD integrated and NVIDIA discrete devices: enumeration,
UUID-based index resolution, missing-device handling, configuration preservation,
Automatic selection, and the WinForms dropdown/save event. The launcher builds;
an actual game run on a manually selected adapter has not yet been validated.
