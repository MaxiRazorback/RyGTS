# Logging

The launcher dropdown selects the minimum severity written by the renderer to
`stdout.log`: Trace, Debug, Info, Warning, or Error. Warning is the
default. Critical diagnostics are emitted as Error; legacy Critical settings map to Error. A missing or invalid setting
also uses Warning. Changes take effect on the next game launch.

The selection is stored as `stdout_level=Warning` in `RyGT.ini`. The renderer
reads this file from the game's working directory, which the launcher sets to
the package directory. Other launchers should use that working directory too.

ShadGT stdout is diagnostic output and is enabled only at Trace or Debug. At Info, Warning, or Error, all ShadGT stdout messages are suppressed. When enabled, messages retain their original severity and the selected threshold still applies.
Its existing internal log files keep their independent class filters. Native file-open and thread-start diagnostics are Trace; other native stdout diagnostics are Debug. Raw game stdout remains unchanged. `stderr.log` and `setup.log`
are never severity-filtered.

Active logs are in the package's `logs` directory:

- `stdout.log` and `stderr.log` belong to a game session.
- `setup.log` belongs to a setup operation.

Before opening a log for a new session or setup operation, the previous file is
archived with a UTC timestamp, for example
`stdout.log.20261018T223045123Z`. A numeric suffix prevents timestamp collisions
from replacing an archive. Legacy logs in the package root are migrated into
`logs` with a `legacy` marker. Archives are retained until manually removed.
The runtime preserves inherited Windows standard handles, including debugger
or terminal redirection, as before.

Rotation uses standard C++ filesystem/chrono APIs in `LogFiles.hpp`; the
launcher uses the equivalent managed `System.IO` APIs. No Windows API is added
to shared logging code. The existing detached Windows stream adapter remains
in `CrashReport.cpp`; non-Windows standard streams use the same portable file
helper.

## Building and checking

Rebuild the launcher and libc. The renderer is a separate build: apply
`renderer/shadGT-patches/0019-leveled-stdout-logging.patch` to shadGT `ryty-gpu`
at `afc9e36cdcf1601336776147893581650410569e` (which already contains patches
0001 through 0018), then apply `0020-fix-host-library-linking.patch` and `0021-default-stdout-error.patch`, then `0022-gate-shadgt-stdout-at-debug.patch`, then `0023-merge-critical-into-error.patch`, then `0024-default-stdout-warning.patch` and rebuild the host libraries. An older prebuilt renderer does
not implement `stdout_level`.

With libc tests enabled, `ctest -R '^log_files$' --output-on-failure` checks
severity parsing, the threshold matrix, and lossless log rotation. The
standalone launcher test can be compiled with the .NET Framework C# compiler:

```bat
csc /target:exe /out:LoggingTests.exe loader\Logging.cs loader\LoggingTests.cs
LoggingTests.exe
```

Place the freshly built `RyGT.exe` beside `LoggingTests.exe`; the test also
checks persistence against the actual launcher's settings class.

`renderer/stdout_level.h` is the testable copy of the header carried by patch
0019. Keep both copies identical when changing the severity policy.

The launcher creates stdout.log and stderr.log under logs before starting the game,
including launches that produce no output. Runtime stdout and stderr use unbuffered
stdio. The launcher rotates previous runtime logs once, creates the two active files, and
passes their prepared directory only to the child process. The runtime reuses them;
direct launches without that marker perform their own rotation. Regenerate GTSport.exe with the updated converter to
remove the old unconditional startup banner.
