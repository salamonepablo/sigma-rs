param(
    [switch]$SkipOnlineCheck,
    [string]$ServerBaseUrl = "",
    [string]$TrayToken = "",
    [string]$EmailSigningSecret = "",
    [string]$TerminalBaseUrl = "",
    [int]$PollIntervalSeconds = 15,
    [string]$DistributionDir = "",
    [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Set-FileUtf8NoBom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath,
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($LiteralPath, $Value, $utf8NoBom)
}

function Mask-Secret {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "(vacio)" }
    if ($Value.Length -le 8) { return ("*" * $Value.Length) }
    return "{0}...{1}" -f $Value.Substring(0, 4), $Value.Substring($Value.Length - 4)
}

function Upsert-EnvValue {
    param(
        [string]$Content,
        [string]$Key,
        [string]$Value
    )

    $line = "$Key=$Value"
    $pattern = "(?m)^\s*$([regex]::Escape($Key))\s*=.*$"
    if ([regex]::IsMatch($Content, $pattern)) {
        return [regex]::Replace($Content, $pattern, $line)
    }
    if ($Content -and -not $Content.EndsWith("`n")) {
        $Content += "`r`n"
    }
    return $Content + $line + "`r`n"
}

function Get-EnvValue {
    param(
        [string]$Content,
        [string]$Key
    )

    $m = [regex]::Match($Content, "(?m)^\s*$([regex]::Escape($Key))\s*=\s*(.+?)\s*$")
    if ($m.Success) {
        return $m.Groups[1].Value.Trim()
    }
    return ""
}

function Prompt-RequiredSecret {
    param(
        [string]$Label,
        [string]$Current
    )

    if (-not [string]::IsNullOrWhiteSpace($Current)) {
        Write-Host ("OK: {0} detectado ({1})" -f $Label, (Mask-Secret -Value $Current))
        return $Current
    }

    if ($NonInteractive) {
        throw "Falta $Label y se ejecuto con -NonInteractive."
    }

    while ($true) {
        $value = Read-Host "Ingrese valor para $Label"
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            Write-Host ("OK: {0} recibido ({1})" -f $Label, (Mask-Secret -Value $value))
            return $value.Trim()
        }
        Write-Host "El valor no puede estar vacio."
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envPath = Join-Path $repoRoot ".env"
$managePath = Join-Path $repoRoot "manage.py"

$summary = [ordered]@{}
$summary["Contexto repo"] = $false
$summary[".env disponible"] = $false
$summary["INGRESO_TRAY_TOKEN"] = $false
$summary["INGRESO_EMAIL_SIGNING_SECRET"] = $false
$summary["SIGMA_BASE_URL"] = $false
$summary["POLL_INTERVAL_SECONDS"] = $false
$summary["Paquete terminal"] = $false
$summary["manage.py shell"] = $false
$summary["/tray/online"] = $false

Write-Host "==== Sigma-RS | Remediacion ingreso (SERVER) ===="
Write-Host "Repositorio: $repoRoot"

if (-not (Test-Path -LiteralPath $managePath)) {
    throw "No se encontro manage.py en $repoRoot. Ejecute el script dentro del repo de Sigma-RS."
}
$summary["Contexto repo"] = $true

if (-not (Test-Path -LiteralPath $envPath)) {
    New-Item -ItemType File -Path $envPath -Force | Out-Null
    Write-Host "Se creo .env porque no existia."
}
$summary[".env disponible"] = $true

$envRaw = Get-Content -LiteralPath $envPath -Raw -ErrorAction SilentlyContinue
if ($null -eq $envRaw) { $envRaw = "" }

$token = Get-EnvValue -Content $envRaw -Key "INGRESO_TRAY_TOKEN"
$secret = Get-EnvValue -Content $envRaw -Key "INGRESO_EMAIL_SIGNING_SECRET"
$sigmaBaseUrl = Get-EnvValue -Content $envRaw -Key "SIGMA_BASE_URL"
$pollSeconds = Get-EnvValue -Content $envRaw -Key "POLL_INTERVAL_SECONDS"

if ($envRaw -match "(?m)^\s*INGRESSO_TRAY_TOKEN\s*=") {
    Write-Host "WARN: se encontro INGRESSO_TRAY_TOKEN (mal escrito). Se usara INGRESO_TRAY_TOKEN."
}
if ($envRaw -match "(?m)^\s*INGRESSO_EMAIL_SIGNING_SECRET\s*=") {
    Write-Host "WARN: se encontro INGRESSO_EMAIL_SIGNING_SECRET (mal escrito). Se usara INGRESO_EMAIL_SIGNING_SECRET."
}

if (-not [string]::IsNullOrWhiteSpace($TrayToken)) { $token = $TrayToken.Trim() }
if (-not [string]::IsNullOrWhiteSpace($EmailSigningSecret)) { $secret = $EmailSigningSecret.Trim() }
if (-not [string]::IsNullOrWhiteSpace($TerminalBaseUrl)) { $sigmaBaseUrl = $TerminalBaseUrl.Trim() }
if ($PollIntervalSeconds -gt 0) { $pollSeconds = [string]$PollIntervalSeconds }

$token = Prompt-RequiredSecret -Label "INGRESO_TRAY_TOKEN" -Current $token
$secret = Prompt-RequiredSecret -Label "INGRESO_EMAIL_SIGNING_SECRET" -Current $secret

if ([string]::IsNullOrWhiteSpace($sigmaBaseUrl)) {
    if ($NonInteractive) {
        throw "Falta SIGMA_BASE_URL y se ejecuto con -NonInteractive."
    }
    $sigmaBaseUrl = Read-Host "Ingrese SIGMA_BASE_URL para terminales (ej: http://SERVER:8000/sigma)"
}

if ([string]::IsNullOrWhiteSpace($sigmaBaseUrl) -or $sigmaBaseUrl -notmatch "^https?://") {
    throw "SIGMA_BASE_URL invalida. Debe comenzar con http:// o https://"
}

$pollInt = 0
if (-not [int]::TryParse($pollSeconds, [ref]$pollInt)) {
    throw "POLL_INTERVAL_SECONDS invalido: '$pollSeconds'"
}
if ($pollInt -lt 5 -or $pollInt -gt 3600) {
    throw "POLL_INTERVAL_SECONDS fuera de rango (5-3600): $pollInt"
}

$sigmaBaseUrl = $sigmaBaseUrl.TrimEnd('/')

$envRaw = Upsert-EnvValue -Content $envRaw -Key "INGRESO_TRAY_TOKEN" -Value $token
$envRaw = Upsert-EnvValue -Content $envRaw -Key "INGRESO_EMAIL_SIGNING_SECRET" -Value $secret
$envRaw = Upsert-EnvValue -Content $envRaw -Key "SIGMA_BASE_URL" -Value $sigmaBaseUrl
$envRaw = Upsert-EnvValue -Content $envRaw -Key "POLL_INTERVAL_SECONDS" -Value ([string]$pollInt)

Set-FileUtf8NoBom -LiteralPath $envPath -Value $envRaw

$summary["INGRESO_TRAY_TOKEN"] = $true
$summary["INGRESO_EMAIL_SIGNING_SECRET"] = $true
$summary["SIGMA_BASE_URL"] = $true
$summary["POLL_INTERVAL_SECONDS"] = $true

if ([string]::IsNullOrWhiteSpace($DistributionDir)) {
    $DistributionDir = Join-Path $repoRoot "ops\out\ingreso_terminal_fix"
}
if (-not (Test-Path -LiteralPath $DistributionDir)) {
    New-Item -ItemType Directory -Path $DistributionDir -Force | Out-Null
}

$distConfigPath = Join-Path $DistributionDir "terminal-fix-config.json"
$distReadmePath = Join-Path $DistributionDir "LEEME_TERMINAL.txt"

$distConfig = [ordered]@{
    sigma_base_url = $sigmaBaseUrl
    ingreso_tray_token = $token
    poll_interval_seconds = $pollInt
}
Set-FileUtf8NoBom -LiteralPath $distConfigPath -Value ($distConfig | ConvertTo-Json -Depth 3)

$readmeLines = @(
    "PAQUETE DE REMEDIACION TERMINAL (Sigma-RS)",
    "",
    "1) Copiar este archivo y terminal-fix-config.json a la PC terminal.",
    "2) En la terminal, abrir una consola en la carpeta con fix_ingreso_terminal.bat.",
    "3) Ejecutar:",
    "   fix_ingreso_terminal.bat",
    "",
    "El script tomara automaticamente terminal-fix-config.json y corregira tray-config.json.",
    "",
    "Valores incluidos:",
    ("- sigma_base_url: {0}" -f $sigmaBaseUrl),
    ("- ingreso_tray_token: {0}" -f $token),
    ("- poll_interval_seconds: {0}" -f $pollInt)
)
Set-FileUtf8NoBom -LiteralPath $distReadmePath -Value ($readmeLines -join "`r`n")
$summary["Paquete terminal"] = $true

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "No se encontro 'python' en PATH. Active el entorno correcto y reintente."
}

$validationSnippet = @'
import os
ok = bool(os.getenv("INGRESO_TRAY_TOKEN")) and bool(os.getenv("INGRESO_EMAIL_SIGNING_SECRET"))
print("INGRESO_ENV_OK=" + ("1" if ok else "0"))
'@

$shellOut = & python "manage.py" shell -c $validationSnippet 2>&1
if ($LASTEXITCODE -eq 0 -and ($shellOut -join "`n") -match "INGRESO_ENV_OK=1") {
    $summary["manage.py shell"] = $true
    Write-Host "OK: validacion por manage.py shell exitosa."
} else {
    Write-Host "WARN: no se pudo confirmar variables desde manage.py shell."
    Write-Host ($shellOut -join "`n")
}

if (-not $SkipOnlineCheck) {
    if ([string]::IsNullOrWhiteSpace($ServerBaseUrl)) {
        $ServerBaseUrl = Read-Host "URL base de Sigma para test online (ej: http://localhost:8000/sigma) o Enter para omitir"
    }
    if (-not [string]::IsNullOrWhiteSpace($ServerBaseUrl)) {
        $onlineUrl = ($ServerBaseUrl.TrimEnd('/')) + "/api/tray/online/?token=$token"
        try {
            $response = Invoke-WebRequest -Uri $onlineUrl -Method GET -TimeoutSec 10
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                $summary["/tray/online"] = $true
                Write-Host "OK: endpoint /api/tray/online/ responde correctamente."
            }
        } catch {
            Write-Host "WARN: fallo validacion online: $($_.Exception.Message)"
        }
    }
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
if ($hasFailure) {
    Write-Host "Accion recomendada: corregir items en FAIL y volver a ejecutar este script."
    exit 1
}

Write-Host ""
Write-Host "==== Distribucion para terminales ===="
Write-Host ("Carpeta: {0}" -f $DistributionDir)
Write-Host ("Config: {0}" -f $distConfigPath)
Write-Host ("Instructivo: {0}" -f $distReadmePath)
Write-Host ""
Write-Host "Pasos (copiar/pegar para operador):"
Write-Host "1) Copiar 'terminal-fix-config.json' al mismo directorio de 'fix_ingreso_terminal.bat' en cada terminal."
Write-Host "2) En cada terminal, ejecutar: fix_ingreso_terminal.bat"
Write-Host "3) Pedir evidencia: captura del bloque '==== Resumen ====' con todos PASS."

Write-Host "Todo OK. Puede continuar con pruebas de ingreso y tray."
exit 0
