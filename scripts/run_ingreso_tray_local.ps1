# run_ingreso_tray_local.ps1 - Run Django + tray poller locally

param(
    [string]$BaseUrl = "http://localhost:8000/sigma",
    [string]$TrayToken = "",
    [string]$SigningSecret = "",
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000
)

$projectPath = "C:\Users\pablo.salamone\Programmes\sigma-rs"
$venvPython = "$projectPath\venv\Scripts\python.exe"

if (-not $TrayToken) {
    $TrayToken = -join ((65..90)+(97..122)+(48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
}

if (-not $SigningSecret) {
    $SigningSecret = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 } | ForEach-Object { [byte]$_ }))
}

Write-Host "============================================"
Write-Host " SIGMA-RS - Ingreso Email (Local Tray)"
Write-Host "============================================"
Write-Host "Base URL: $BaseUrl"
Write-Host "Tray token: $TrayToken"
Write-Host "Signing secret: $SigningSecret"
Write-Host "============================================"
Write-Host "Se abriran dos ventanas: servidor y tray poller"

$envBlock = "`$env:INGRESO_TRAY_TOKEN='$TrayToken'; `$env:INGRESO_EMAIL_SIGNING_SECRET='$SigningSecret'; `$env:SIGMA_BASE_URL='$BaseUrl';"

Set-Location $projectPath

Start-Process pwsh -ArgumentList "-NoExit", "-Command", "$envBlock & '$venvPython' manage.py runserver $BindHost`:$Port" | Out-Null
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "$envBlock & '$venvPython' tray-app/src/poller.py" | Out-Null

Write-Host "Listo. Genera un ingreso en la UI para probar el envio."
