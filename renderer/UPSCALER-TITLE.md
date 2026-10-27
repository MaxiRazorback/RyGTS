# Active upscaler title status

Patch 0094 reports the successfully presented backend and observed scale class. Examples: `FSR 3.1 | Quality`, `FSR 3.1 FG | Ultra Performance`, and `DLAA | Native`. With an active upscaler, resolution-arrow text is omitted. With no active upscaler, output-to-observed-scene resolution is shown.

FG is appended to the backend name only after recent extra presentation counts have been observed; settings alone do not enable the badge. It expires after inactivity and clears on failures or generation disable. The counts are activity evidence, not proof of even display spacing or generated-frame visual quality.

Validation: seven title assertions, renderer build/import/image checks, persistent FSR title observed in live 3D rendering. DLSSG activity uses its existing actual-presentation counter.
