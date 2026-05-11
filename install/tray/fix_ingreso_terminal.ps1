param(
    [string]$TrayExePath = "C:\SigmaRS\SigmaRSIngresoTray.exe",
    [string]$PackagePath = "",
    [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$summary = [ordered]@{}
$summary["Paquete de configuracion"] = $false
$summary["sigma_base_url"] = $false
$summary["ingreso_tray_token"] = $false
$summary["poll_interval_seconds"] = $false
$summary["Launcher Startup"] = $false
$summary["Tray iniciado"] = $false

$trayDir = Join-Path $env:APPDATA "SigmaRS"
$configPath = Join-Path $trayDir "tray-config.json"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$startupBat = Join-Path $startupDir "SigmaRSIngresoTray.bat"

Write-Host "==== Sigma-RS | Remediacion ingreso (TERMINAL) ===="

if ([string]::IsNullOrWhiteSpace($PackagePath)) {
    $PackagePath = Join-Path $PSScriptRoot "terminal-fix-config.json"
}

if (-not (Test-Path -LiteralPath $PackagePath)) {
    Write-Host "FAIL: No se encontro paquete de configuracion: $PackagePath"
    Write-Host "Accion: copie 'terminal-fix-config.json' generado en el servidor y reintente."
    exit 1
}

if (-not (Test-Path -LiteralPath $trayDir)) {
    New-Item -ItemType Directory -Path $trayDir -Force | Out-Null
}

$package = @{}
try {
    $packageRaw = Get-Content -LiteralPath $PackagePath -Raw
    $package = ConvertFrom-Json -InputObject $packageRaw -AsHashtable
} catch {
    Write-Host "FAIL: paquete invalido ($PackagePath): $($_.Exception.Message)"
    exit 1
}

$summary["Paquete de configuracion"] = $true

$baseUrl = ""
$token = ""
$interval = ""

if ($package.ContainsKey("sigma_base_url")) { $baseUrl = [string]$package["sigma_base_url"] }
if ($package.ContainsKey("ingreso_tray_token")) { $token = [string]$package["ingreso_tray_token"] }
if ($package.ContainsKey("poll_interval_seconds")) { $interval = [string]$package["poll_interval_seconds"] }

if ([string]::IsNullOrWhiteSpace($baseUrl) -or $baseUrl -notmatch "^https?://") {
    throw "sigma_base_url ausente o invalido en paquete: $PackagePath"
}

if ([string]::IsNullOrWhiteSpace($token)) {
    throw "ingreso_tray_token ausente en paquete: $PackagePath"
}

$intervalInt = 0
if (-not [int]::TryParse($interval, [ref]$intervalInt) -or $intervalInt -lt 5 -or $intervalInt -gt 3600) {
    throw "poll_interval_seconds invalido en paquete: $interval"
}

$baseUrl = $baseUrl.TrimEnd('/')

$configOut = [ordered]@{
    sigma_base_url = $baseUrl
    ingreso_tray_token = $token
    poll_interval_seconds = $intervalInt
}

$configJson = $configOut | ConvertTo-Json -Depth 3
Set-Content -LiteralPath $configPath -Encoding UTF8NoBOM -Value $configJson

$summary["sigma_base_url"] = $true
$summary["ingreso_tray_token"] = $true
$summary["poll_interval_seconds"] = $true

if (-not (Test-Path -LiteralPath $startupDir)) {
    throw "No se encontro carpeta Startup: $startupDir"
}

$launcherLines = @(
    "@echo off",
    ('start "" "{0}"' -f $TrayExePath)
)
Set-Content -LiteralPath $startupBat -Encoding Ascii -Value ($launcherLines -join "`r`n")
$summary["Launcher Startup"] = $true

if (Test-Path -LiteralPath $TrayExePath) {
    try {
        Start-Process -FilePath $TrayExePath | Out-Null
        $summary["Tray iniciado"] = $true
    } catch {
        Write-Host "WARN: no se pudo iniciar tray: $($_.Exception.Message)"
    }
} else {
    Write-Host "WARN: no se encontro tray exe en $TrayExePath"
}

Write-Host ""
Write-Host "==== Resumen ===="
$hasFailure = $false
foreach ($item in $summary.GetEnumerator()) {
    $status = if ($item.Value) { "PASS" } else { "FAIL" }
    if (-not $item.Value) { $hasFailure = $true }
    Write-Host ("[{0}] {1}" -f $status, $item.Key)
}

Write-Host ""
Write-Host "Datos para enviar al administrador:"
Write-Host ("- sigma_base_url: {0}" -f $configOut.sigma_base_url)
Write-Host ("- ingreso_tray_token: {0}" -f $configOut.ingreso_tray_token)
Write-Host ("- poll_interval_seconds: {0}" -f $configOut.poll_interval_seconds)
Write-Host ("- launcher: {0}" -f $startupBat)

if ($hasFailure) {
    Write-Host "Hay items en FAIL. Corrija y vuelva a ejecutar el script."
    exit 1
}

Write-Host "Todo OK en terminal."
exit 0
