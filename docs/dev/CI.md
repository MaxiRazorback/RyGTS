# GitLab CI

`.gitlab-ci.yml` runs three independent jobs on branch pushes, merge requests,
and tags. Branch pipelines are suppressed when an equivalent merge-request
pipeline exists. CI creates downloadable build artifacts; it does not publish
releases or change installed game files.

* `launcher`: builds `loader/build.cmd` with the .NET Framework compiler.
* `renderer`: builds the native `ryty_gpu` target as `libSceVideoOut.prx`,
  with symbols, source provenance and SHA-256 checksums.
* `converter-and-tests`: builds the Linux CLI preset on Ubuntu 24.04 and runs
  CTest, publishing a JUnit report. This job does not build the game runtime.

## Windows runner setup

Register a Windows **shell/PowerShell** GitLab runner tagged `rygt-windows`.
Use a short runner `builds_dir`, such as `C:\b`; nested dependency Git paths
can exceed Git for Windows limits under long user-profile checkout paths.
The two Windows jobs remain pending until a runner with that tag is available.
Use an isolated runner for trusted project code; do not expose a privileged
shell runner to untrusted fork merge requests or store signing credentials on it.

Install Visual Studio C++ x64 build tools and Windows SDK, .NET Framework 4.x,
Python 3, Git, CMake 3.30+ and Ninja. Install the full official LLVM 23.1.3
Windows x64 archive, including compiler-rt, and set `LLVM_ROOT` to its root.
The script loads the x64 MSVC developer environment when needed (INCLUDE, LIB,
and PATH); `clang-cl`, `lld-link`, `cmake`, `ninja`, `python`, and `git` must work
in a runner job. Use a fresh checkout per job: `.ci-renderer` is intentionally
not reused. Renderer compilation is limited to two workers; allow at least
16 GB RAM and sufficient disk space for its dependencies and build tree.

Linux jobs require a Docker runner that accepts untagged jobs and can pull
`ubuntu:24.04`. Windows jobs do not use Docker images.

## Reproducing the renderer

`ci/prepare-renderer.py <new-directory>` checks out the exact public ShadGT
base `1d13c88d2e57bc63ce1586fe0b8f3342b6afdd19`, applies the camera patch first,
then the DLSS patch and patches 0062 through 0097 in filename order, and
initializes pinned submodules. Every patch failure stops the job.

The camera and temporal-upscaler patches overlap in `ryty_entry.cpp`.
`ci/renderer-0064-camera-entry.patch` carries only that file's original 0064
changes with camera-aware context; the rest of 0064 applies unchanged.
Update the explicit patch range when publishing subsequent renderer patches.
No local experimental shader overrides, game executable, firmware, captures,
or shader caches are included. CI-SOURCE.txt records the renderer base and patch
names; RYGT-COMMIT.txt identifies the repository revision containing those patches.

To build locally from an x64 developer PowerShell:

```powershell
$env:LLVM_ROOT = 'C:\toolchains\clang+llvm-23.1.3-x86_64-pc-windows-msvc'
powershell -NoProfile -ExecutionPolicy Bypass -File ci/build-windows.ps1 -Target Launcher
powershell -NoProfile -ExecutionPolicy Bypass -File ci/build-windows.ps1 -Target Renderer
```

Artifacts expire after 14 days. Checksums detect changes but are not signatures
or proof of publisher identity. A successful compile/test pipeline does not
replace live GPU and game validation.
