$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# GitLab-hosted Windows VMs are disposable. Keep tool paths short.
$tools = 'C:/ci-tools'
New-Item -ItemType Directory -Force $tools | Out-Null
$archive = "$tools/llvm-23.1.3.tar.xz"
$url = 'https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.3/clang%2Bllvm-23.1.3-x86_64-pc-windows-msvc.tar.xz'
Invoke-WebRequest -UseBasicParsing $url -OutFile $archive
if ((Get-FileHash $archive -Algorithm SHA256).Hash -ne '9ee6a2192fbb30c776415af529927f76ca6b5d1d55699bb1315f9878e610b5b8') {
    throw 'LLVM archive SHA-256 mismatch'
}
& tar.exe -xf $archive -C $tools
if ($LASTEXITCODE) { throw 'LLVM extraction failed' }
$env:LLVM_ROOT = "$tools/clang+llvm-23.1.3-x86_64-pc-windows-msvc"
& python -m pip install --disable-pip-version-check cmake==3.31.6 ninja==1.11.1.4
if ($LASTEXITCODE) { throw 'CMake/Ninja installation failed' }
$scripts = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
if ($LASTEXITCODE) { throw 'Python scripts path lookup failed' }
$env:PATH = "$env:LLVM_ROOT/bin;$scripts;$env:PATH"
& cmake --version
if ($LASTEXITCODE) { throw 'CMake unavailable' }
