param(
    [string]$OutputDir = "",
    [string]$ExeName = "SigmaRSIngresoTray.exe"
)

if (!$OutputDir) {
    $OutputDir = Join-Path $PSScriptRoot "pendrive_ready"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$sourceExe = Join-Path $repoRoot ("dist\\" + $ExeName)
$sourceInstaller = Join-Path $PSScriptRoot "install_tray.ps1"
$sourceReadme = Join-Path $PSScriptRoot "install_tray_README.txt"

if (!(Test-Path $sourceExe)) {
    Write-Host "No se encontro el ejecutable en: $sourceExe"
    exit 1
}

if (!(Test-Path $sourceInstaller)) {
    Write-Host "No se encontro el instalador en: $sourceInstaller"
    exit 1
}

if (!(Test-Path $sourceReadme)) {
    Write-Host "No se encontro el README en: $sourceReadme"
    exit 1
}

if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Copy-Item -Path $sourceExe -Destination (Join-Path $OutputDir $ExeName) -Force
Copy-Item -Path $sourceInstaller -Destination (Join-Path $OutputDir "install_tray.ps1") -Force
Copy-Item -Path $sourceReadme -Destination (Join-Path $OutputDir "install_tray_README.txt") -Force

Write-Host "OK: Pendrive listo en $OutputDir"
