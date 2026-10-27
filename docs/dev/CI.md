# CI packages

GitLab is the authoritative source and download host. GitHub Actions in
[`xacidr4inx/RyGT-ci`](https://github.com/xacidr4inx/RyGT-ci/actions/workflows/ci-package.yml)
builds, tests, packages and publishes. No GitLab runner is used.

The workflow checks the public GitLab `development` branch every 15 minutes and
builds its exact commit when no completed CI package exists for that revision.
GitHub schedules can be delayed. To start sooner or retry, use **Run workflow**;
enable **force** to rebuild an already published revision. Changes arriving
during a build are picked up by a later check. Builds are serialized to avoid
duplicate uploads. Only development is automatically packaged; main, tags and
merge-request branches are not publication inputs.

## Downloads

Open GitLab **Deploy → Package Registry**, then package **rygt-ci**.
Each version is `development-<full source commit>` and contains:

- `RyGT-development-<short commit>.zip`
- the matching `.zip.sha256`
- `CI-BUILD.json`, recording source commit, checksum and GitHub run URL

These are CI builds. Publishing does not create a tag, release, announcement or
changelog. The completion marker is uploaded last, after reading back and
verifying both package files. Package versions persist until removed from the
registry. GitHub intermediate artifacts expire after seven days.

## Build and validation

The Windows job builds the launcher and pinned renderer using
`ci/setup-hosted-windows.ps1` and `ci/build-windows.ps1`. A separate GitHub Linux
job builds and tests the converter with CTest. Packaging requires both jobs to
succeed and verifies source revisions, artifact checksums, runtime archive
identity, required files, safe ZIP paths and packaged-file checksums.

The Windows converter and other helper/runtime binaries still come from the
immutable October 25 redistributable archive pinned by SHA-256 in `ci/package.py`.
They are not rebuilt by this workflow; the Linux test binary is not substituted
for a Windows executable. BUILD_INFO.txt records exactly what was rebuilt.
Game executable/data, firmware, saves, logs, shader caches and NVIDIA SDK files
are excluded. Compilation and package validation do not replace live GPU tests.

`renderer/source.json` pins the ShadGT `ryty-gpu` commit. Push a renderer change
there before publishing a RyGT pin that references it. Local investigation
branches and unpushed renderer commits are not included automatically.

## Workflow maintenance and credentials

The reviewed workflow and control-script sources are retained under
`ci/github-registry/`. The deployed copies live in the GitHub workflow repository
as `.github/workflows/ci-package.yml` and `ci/registry_ci.py`. Update both together.
Official actions are pinned to full commit IDs. The old GitLab bridge is retired;
`.gitlab-ci.yml` explicitly disables GitLab pipelines.

GitHub secret `GITLAB_PACKAGE_TOKEN` is a project deploy token restricted to
RyGT package read/write access. It is exposed only to the final publish step,
not to Windows builds or Linux converter tests. The initial token expires
January 25, 2027; rotate it before then. It cannot create releases, modify source
or report commit statuses. Build status and logs are in GitHub Actions; GitLab
holds packages rather than runner jobs. Never put credentials in source files.

To build manually in a Windows developer PowerShell, install LLVM 23.1.3 with
compiler-rt, set `LLVM_ROOT`, and run:

```powershell
./ci/build-windows.ps1 -Target Launcher
./ci/build-windows.ps1 -Target Renderer
```
