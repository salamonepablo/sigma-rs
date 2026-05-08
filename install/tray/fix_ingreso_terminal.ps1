param(
    [string]$TrayExePath = "C:\SigmaRS\SigmaRSIngresoTray.exe",
    [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Mask-Secret {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "(vacio)" }
    if ($Value.Length -le 8) { return ("*" * $Value.Length) }
    return "{0}...{1}" -f $Value.Substring(0, 4), $Value.Substring($Value.Length - 4)
}

function Prompt-IfMissing {
    param(
        [string]$Label,
        [string]$Current,
        [switch]$Sensitive,
        [scriptblock]$Validator
    )

    if (-not [string]::IsNullOrWhiteSpace($Current)) {
        if ($Sensitive) {
            Write-Host ("OK: {0} detectado ({1})" -f $Label, (Mask-Secret -Value $Current))
        } else {
            Write-Host ("OK: {0} detectado ({1})" -f $Label, $Current)
        }
        return $Current
    }

    if ($NonInteractive) {
        throw "Falta $Label y se ejecuto con -NonInteractive."
    }

    while ($true) {
        $value = Read-Host "Ingrese valor para $Label"
        if ([string]::IsNullOrWhiteSpace($value)) {
            Write-Host "El valor no puede estar vacio."
            continue
        }
        $trimmed = $value.Trim()
        if ($Validator -and -not (& $Validator $trimmed)) {
            Write-Host "Valor invalido para $Label. Reintente."
            continue
        }
        if ($Sensitive) {
            Write-Host ("OK: {0} recibido ({1})" -f $Label, (Mask-Secret -Value $trimmed))
        } else {
            Write-Host ("OK: {0} recibido ({1})" -f $Label, $trimmed)
        }
        return $trimmed
    }
}

$summary = [ordered]@{}
$summary["Config disponible"] = $false
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

if (-not (Test-Path -LiteralPath $trayDir)) {
    New-Item -ItemType Directory -Path $trayDir -Force | Out-Null
}

$configObj = @{}
if (Test-Path -LiteralPath $configPath) {
    try {
        $raw = Get-Content -LiteralPath $configPath -Raw
        if (-not [string]::IsNullOrWhiteSpace($raw)) {
            $configObj = ConvertFrom-Json -InputObject $raw -AsHashtable
        }
    } catch {
        Write-Host "WARN: tray-config.json invalido. Se recreara con datos nuevos."
        $configObj = @{}
    }
}

$summary["Config disponible"] = $true

$baseUrl = ""
$token = ""
$interval = ""

if ($configObj.ContainsKey("sigma_base_url")) { $baseUrl = [string]$configObj["sigma_base_url"] }
if ($configObj.ContainsKey("ingreso_tray_token")) { $token = [string]$configObj["ingreso_tray_token"] }
if ($configObj.ContainsKey("poll_interval_seconds")) { $interval = [string]$configObj["poll_interval_seconds"] }

$baseUrl = Prompt-IfMissing -Label "sigma_base_url" -Current $baseUrl -Validator {
    param($v)
    return $v -match "^https?://"
}

$token = Prompt-IfMissing -Label "ingreso_tray_token" -Current $token -Sensitive

$interval = Prompt-IfMissing -Label "poll_interval_seconds" -Current $interval -Validator {
    param($v)
    $n = 0
    return [int]::TryParse($v, [ref]$n) -and $n -ge 5 -and $n -le 3600
}

$configOut = [ordered]@{
    sigma_base_url = $baseUrl.TrimEnd('/')
    ingreso_tray_token = $token
    poll_interval_seconds = [int]$interval
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
Write-Host ("- ingreso_tray_token: {0}" -f (Mask-Secret -Value $configOut.ingreso_tray_token))
Write-Host ("- poll_interval_seconds: {0}" -f $configOut.poll_interval_seconds)
Write-Host ("- launcher: {0}" -f $startupBat)

if ($hasFailure) {
    Write-Host "Hay items en FAIL. Corrija y vuelva a ejecutar el script."
    exit 1
}

Write-Host "Todo OK en terminal."
exit 0
