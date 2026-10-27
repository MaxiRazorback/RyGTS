# GitLab CI

`.gitlab-ci.yml` builds on GitLab-hosted machines. No runner, service or build
process on a developer PC is required. Branch pushes, merge requests and tags
run CI; duplicate push/MR pipelines are suppressed.

* `launcher`: Windows .NET Framework build of `loader/build.cmd`.
* `renderer`: native Windows `ryty_gpu` build producing `libSceVideoOut.prx`,
  PDB symbols, source provenance and SHA-256 checksums.
* `converter-and-tests`: Ubuntu 24.04 Linux CLI build and CTest with JUnit output.
* `package`: waits for all three jobs to succeed, downloads their required
  artifacts, and assembles one verified Windows distribution ZIP plus its hash.

The Windows jobs select GitLab's `saas-windows-medium-amd64` hosted runner.
The renderer setup script installs LLVM 23.1.3 from the official archive,
checks its pinned SHA-256, and installs CMake 3.31.6 and Ninja 1.11.1.4.
The MSVC developer environment comes from the hosted image's Visual Studio
C++ tools. The renderer uses two compiler workers and has a three-hour job
limit. Hosted Windows provisioning can take several minutes. Availability,
compute quota and the project's maximum job timeout still apply.

## Complete distribution package

Download `dist/RyGT-development-<commit>.zip` from the `package` job's artifacts.
It contains the fresh CI launcher and renderer, the converter and other required
redistributable runtime files, default configuration, documentation and licenses.
Symbols stay in the renderer job artifact and are excluded from the release ZIP.

The remaining Windows runtime/helper files, including `converter/ryty.exe` and
`adcpatch.exe`, come from the immutable October 25 published prerelease archive,
pinned by full SHA-256 in `ci/package.py`. The Linux converter test binary is not
substituted for a Windows executable. This pipeline does **not** rebuild every
runtime library or Windows helper. BUILD_INFO.txt records that distinction,
the exact source revision, renderer patch list and runtime archive identity.
Updating those retained files requires a reviewed change to the pinned runtime.

Package assembly verifies both build artifact checksums and source revisions,
rejects unsafe ZIP paths and unwanted game/user data, checks required runtime
files, regenerates the complete checksum manifest, then reads back and verifies
every packaged file. No game executable/data, firmware, saves, logs, shader
caches or NVIDIA SDK files are included. Players supply their own game and
required firmware modules through normal setup.

The package is a development artifact; CI does not create a release or publish
a tag automatically. Package artifacts expire after 30 days; individual build
artifacts expire after 14 days. Checksums are not publisher signatures.

## Renderer source

`renderer/source.json` pins a full commit on ShadGT's `ryty-gpu` branch.
`ci/prepare-renderer.py <new-directory>` fetches that exact commit, verifies HEAD,
and initializes its pinned submodules. CI does not apply renderer patches.
Git long-path support remains enabled for Windows dependency checkout.

Renderer changes belong in ShadGT as ordinary commits. After testing and pushing
them to `ryty-gpu`, update the commit in `renderer/source.json` for the next RyGT
build. `CI-SOURCE.txt` in the renderer artifact records that revision.
Unfinished local experiments are not included automatically.

To build manually from a Windows x64 developer PowerShell, install the same
LLVM distribution and set LLVM_ROOT to it, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ci/build-windows.ps1 -Target Launcher
powershell -NoProfile -ExecutionPolicy Bypass -File ci/build-windows.ps1 -Target Renderer
```

Successful CI compilation and packaging do not replace live game/GPU validation.
