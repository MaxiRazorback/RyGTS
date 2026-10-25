# Motion blur

Graphics > Enhancements > Disable motion blur saves GPU.disable_motion_blur in
user/custom_configs/CUSA03220.json. It defaults to false, preserving the original
appearance. Changes take effect on the next game launch.

Build the launcher with loader/build.cmd and include renderer patch
0079-optional-motion-blur-disable.patch in libSceVideoOut.prx. A launcher alone
cannot disable the game's effects.

For CUSA03220 update 1.69, the renderer overrides the scene and fixed motion-blur
enable inputs when the game schedules its post-process jobs. The combined scene
motion-blur/depth-of-field job retains its normal control flow and output handling.
Both executable signatures are checked before applying the option; an unsupported
executable is logged and left unchanged. No game files or shader caches are edited.

Validation: launcher and renderer build; checkbox default and persistence checks;
2,610 local import bindings; patch applies to the isolated PR 100 renderer source.
In-game motion-blur comparison and depth-of-field regression testing remain pending.
