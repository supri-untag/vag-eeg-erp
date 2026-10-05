param([string]$InnoCompiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe")
$ErrorActionPreference = "Stop"
if ($env:OS -ne "Windows_NT") { throw "Build .exe harus dijalankan di Windows x64." }
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
try {
    if (!(Test-Path $InnoCompiler)) { throw "Pasang Inno Setup 6 atau gunakan -InnoCompiler dengan path ISCC.exe." }
    py -3.12 -m venv .venv-build
    if ($LASTEXITCODE -ne 0) { throw "Pasang Python 3.12 x64 beserta Python Launcher." }
    $BuildPython = Join-Path $ProjectRoot ".venv-build\Scripts\python.exe"
    & $BuildPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Pembaruan pip gagal." }
    & $BuildPython -m pip install --upgrade ".[dev,build]"
    if ($LASTEXITCODE -ne 0) { throw "Instalasi dependensi gagal." }
    & $BuildPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Dependensi tidak kompatibel." }
    & $BuildPython -c "import struct; assert struct.calcsize('P') == 8, 'Python x64 diperlukan'"
    if ($LASTEXITCODE -ne 0) { throw "Python harus 64-bit." }
    & $BuildPython -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Tes gagal; build dihentikan." }
    & $BuildPython -m PyInstaller --clean --noconfirm packaging/vard.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller gagal." }
    & $BuildPython scripts/check_bundle.py dist/VARD-EEG-ERP/VARD-EEG-ERP.exe dist/bundle-smoke.json
    if ($LASTEXITCODE -ne 0) { throw "Uji executable gagal; installer tidak dibuat." }
    $AppVersion = & $BuildPython -c "import importlib.metadata; print(importlib.metadata.version('vard-eeg-erp'))"
    if ($LASTEXITCODE -ne 0) { throw "Versi aplikasi tidak ditemukan." }
    & $InnoCompiler "/DAppVersion=$AppVersion" packaging/installer.iss
    if ($LASTEXITCODE -ne 0) { throw "Pembuatan installer gagal." }
    & $BuildPython -m pip freeze | Set-Content -Encoding utf8 dist/requirements-windows-built.txt
    Get-FileHash "dist/installer/VARD-EEG-ERP-Setup-$AppVersion-x64.exe" -Algorithm SHA256 |
        Format-List | Out-File -Encoding utf8 dist/installer/SHA256.txt
    Write-Host "Build selesai: dist/installer. Uji instalasi, GUI, dan uninstall pada Windows sebelum distribusi."
} finally {
    Pop-Location
}
