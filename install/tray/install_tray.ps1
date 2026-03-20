param(
    [string]$ServerIp = "172.22.181.1",
    [string]$ServerPort = "8000",
    [string]$ServerScheme = "http",
    [string]$TargetDir = "C:\SigmaRS",
    [string]$ExeName = "SigmaRSIngresoTray.exe",
    [string]$TrayToken = "",
    [string]$SourceExe = "",
    [string]$TokenFile = "",
    [string]$ServerIpFile = "",
    [string]$ServerPortFile = "",
    [string]$ServerSchemeFile = ""
)

$resolvedSource = $SourceExe
if (!$resolvedSource) {
    $resolvedSource = Join-Path $PSScriptRoot $ExeName
}

if (!(Test-Path $resolvedSource)) {
    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
    $repoExe = Join-Path $repoRoot ("dist\\" + $ExeName)
    if (Test-Path $repoExe) {
        $resolvedSource = $repoExe
    }
}

$sourceExe = $resolvedSource
if (!(Test-Path $sourceExe)) {
    Write-Host "No se encontro el ejecutable en: $sourceExe"
    exit 1
}

$resolvedServerIpFile = $ServerIpFile
if (!$resolvedServerIpFile) {
    $resolvedServerIpFile = Join-Path $PSScriptRoot "server-ip.txt"
}
if (Test-Path $resolvedServerIpFile) {
    $ServerIp = (Get-Content $resolvedServerIpFile -Raw).Trim()
}

$resolvedServerPortFile = $ServerPortFile
if (!$resolvedServerPortFile) {
    $resolvedServerPortFile = Join-Path $PSScriptRoot "server-port.txt"
}
if (Test-Path $resolvedServerPortFile) {
    $ServerPort = (Get-Content $resolvedServerPortFile -Raw).Trim()
}

$resolvedServerSchemeFile = $ServerSchemeFile
if (!$resolvedServerSchemeFile) {
    $resolvedServerSchemeFile = Join-Path $PSScriptRoot "server-scheme.txt"
}
if (Test-Path $resolvedServerSchemeFile) {
    $ServerScheme = (Get-Content $resolvedServerSchemeFile -Raw).Trim()
}

if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

$targetExe = Join-Path $TargetDir $ExeName
Copy-Item -Path $sourceExe -Destination $targetExe -Force

$startupDir = Join-Path $env:APPDATA "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
if (!(Test-Path $startupDir)) {
    Write-Host "No se encontro la carpeta de inicio: $startupDir"
    exit 1
}

$batPath = Join-Path $startupDir "SigmaRSIngresoTray.bat"
$batContent = @(
    "@echo off",
    "set NO_PROXY=$ServerIp,localhost,127.0.0.1",
    '"' + $targetExe + '"'
)
Set-Content -Path $batPath -Value $batContent -Encoding Ascii

if (!$TrayToken) {
    $resolvedTokenFile = $TokenFile
    if (!$resolvedTokenFile) {
        $resolvedTokenFile = Join-Path $PSScriptRoot "tray-token.txt"
    }
    if (Test-Path $resolvedTokenFile) {
        $TrayToken = (Get-Content $resolvedTokenFile -Raw).Trim()
    }
}

if (!$TrayToken) {
    Write-Host "Falta INGRESO_TRAY_TOKEN. Use -TrayToken o cree tray-token.txt junto al instalador."
    exit 1
}

$trayDir = Join-Path $env:APPDATA "SigmaRS"
if (!(Test-Path $trayDir)) {
    New-Item -ItemType Directory -Path $trayDir | Out-Null
}

$trayConfigPath = Join-Path $trayDir "tray-config.json"
$baseUrl = "{0}://{1}:{2}/sigma" -f $ServerScheme, $ServerIp, $ServerPort
$trayConfig = @"
{
  "sigma_base_url": "$baseUrl",
  "ingreso_tray_token": "$TrayToken",
  "poll_interval_seconds": 15
}
"@
Set-Content -Path $trayConfigPath -Value $trayConfig -Encoding Ascii

Write-Host "OK: Ejecutable copiado a $targetExe"
Write-Host "OK: Atajo de inicio creado en $batPath"
Write-Host "OK: Config creado en $trayConfigPath"
