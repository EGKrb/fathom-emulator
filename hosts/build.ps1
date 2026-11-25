# Builds emulator_host_x64.exe and emulator_host_x32.exe (the hosts of the emulator's child processes of the
# other architecture) with MSVC, next to this script. Needs Visual Studio or its Build Tools with the C++ workload.
#
#   powershell -File hosts\build.ps1 [-Arch x64|x32|all]
param(
    [ValidateSet('x64', 'x32', 'all')]
    [string] $Arch = 'all'
)
$ErrorActionPreference = 'Stop'

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path $vswhere)) { throw 'vswhere.exe not found: install Visual Studio or its Build Tools (C++)' }
$vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw 'no Visual Studio with the C++ tools (Microsoft.VisualStudio.Component.VC.Tools.x86.x64)' }
$vcvarsall = Join-Path $vs 'VC\Auxiliary\Build\vcvarsall.bat'
$env:PATH = (Split-Path $vswhere) + ';' + $env:PATH  # vcvarsall looks for vswhere on the PATH

$source = Join-Path $PSScriptRoot 'emulator_host.cpp'
$libs = 'ws2_32.lib wininet.lib user32.lib gdi32.lib ole32.lib oleaut32.lib shell32.lib advapi32.lib comctl32.lib'
$targets = if ($Arch -eq 'all') { 'x64', 'x32' } else { , $Arch }
foreach ($target in $targets) {
    $vcarch = if ($target -eq 'x64') { 'x64' } else { 'x64_x86' }
    $out = Join-Path $PSScriptRoot "emulator_host_$target.exe"
    $obj = Join-Path ([IO.Path]::GetTempPath()) "emulator_host_$target.obj"
    # static C runtime: the host needs no Visual C++ redistributable
    $script = Join-Path ([IO.Path]::GetTempPath()) "emulator_host_$target.cmd"
    Set-Content -Encoding ascii $script @(
        "@call `"$vcvarsall`" $vcarch >nul || exit /b 1",
        "@cl /nologo /O1 /MT /EHsc /DUNICODE /D_UNICODE `"$source`" /Fo`"$obj`" /Fe`"$out`" /link $libs"
    )
    cmd /c "`"$script`""
    $code = $LASTEXITCODE
    Remove-Item $script -ErrorAction SilentlyContinue
    if ($code -ne 0) { throw "the build of $out failed" }
    Remove-Item $obj -ErrorAction SilentlyContinue
    "built $out"
}
