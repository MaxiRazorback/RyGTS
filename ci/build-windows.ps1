param([Parameter(Mandatory=$true)][ValidateSet('Launcher','Renderer')][string]$Target)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Set-Location (Split-Path $PSScriptRoot -Parent)
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
$out = Join-Path (Get-Location) ("artifacts/" + $Target.ToLowerInvariant())
New-Item -ItemType Directory -Force $out | Out-Null
if ($Target -eq 'Launcher') {
    Invoke-Checked 'cmd.exe' @('/d','/c', 'loader\build.cmd', $out)
    if (!(Test-Path "$out/RyGT.exe")) { throw 'Launcher output missing' }
} else {
    if (!$env:LLVM_ROOT) { throw 'Set LLVM_ROOT to the LLVM 23.1.3 distribution (see docs/dev/CI.md)' }
    $llvm = (Resolve-Path $env:LLVM_ROOT).Path
    $env:PATH = "$llvm/bin;$env:PATH"
    $version = & clang-cl --version
    if ($LASTEXITCODE -ne 0 -or "$version" -notmatch '23\.1\.3') { throw 'LLVM 23.1.3 required' }
    $builtins = Get-ChildItem "$llvm/lib" -Recurse -Filter clang_rt.builtins-x86_64.lib | Select-Object -First 1
    if (!$builtins) { throw 'Full LLVM archive with compiler-rt builtins is required' }
    $env:LIB = "$($builtins.DirectoryName);$env:LIB"
    $source = Join-Path (Get-Location) '.ci-renderer'
    Invoke-Checked 'python' @('ci/prepare-renderer.py', $source)
    if (!$env:VCINSTALLDIR) {
        $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
        $vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($LASTEXITCODE -ne 0 -or !$vs) { throw 'Visual Studio x64 C++ tools not found' }
        Import-Module (Join-Path $vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
        Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'
        # Developer-shell initialization can replace LIB/PATH; restore our pinned LLVM first.
        $env:PATH = "$llvm/bin;$env:PATH"
        $env:LIB = "$($builtins.DirectoryName);$env:LIB"
    }
    Invoke-Checked 'cmake' @('-S',$source,'-B',"$source/Build/ci",'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=clang-cl','-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_LINKER=lld-link','-DHAVE_ENDIAN_H=OFF','-DSHADGT_RYTY_GPU=ON','-DENABLE_DISCORD_RPC=ON')
    if (!(Select-String -LiteralPath "$source/Build/ci/CMakeCache.txt" -Pattern '^ENABLE_DISCORD_RPC:BOOL=ON$' -Quiet)) { throw 'Discord RPC was not enabled in renderer configuration' }
    Invoke-Checked 'cmake' @('--build',"$source/Build/ci",'--target','ryty_gpu','--parallel','2')
    $binary = Get-ChildItem "$source/Build/ci" -Recurse -Filter libSceVideoOut.prx
    if (@($binary).Count -ne 1) { throw 'Expected exactly one renderer output' }
    Copy-Item $binary.FullName $out
    Get-ChildItem "$source/Build/ci" -Recurse -Filter '*VideoOut*.pdb' | Copy-Item -Destination $out
    Copy-Item "$source/CI-SOURCE.txt" $out
    Invoke-Checked 'git' @('-C',$source,'submodule','status','--recursive')
}
$commit = & git rev-parse HEAD
if ($LASTEXITCODE) { throw 'Cannot record source revision' }
$commit | Set-Content "$out/RYGT-COMMIT.txt"
Get-ChildItem $out -File | Where-Object Name -ne 'SHA256SUMS.txt' | ForEach-Object {
    $hash = Get-FileHash $_.FullName -Algorithm SHA256
    "$($hash.Hash.ToLowerInvariant())  $($_.Name)"
} | Set-Content "$out/SHA256SUMS.txt"
