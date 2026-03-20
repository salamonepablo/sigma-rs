# set_ingreso_secrets.ps1
# Genera y configura secretos para Sigma-RS

param(
    [ValidateSet("Machine", "User")]
    [string]$Scope = "Machine"
)

$token = -join ((65..90)+(97..122)+(48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
$secret = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 } | ForEach-Object { [byte]$_ }))

# Always set for current session
$env:INGRESO_TRAY_TOKEN = $token
$env:INGRESO_EMAIL_SIGNING_SECRET = $secret

try {
    [Environment]::SetEnvironmentVariable("INGRESO_TRAY_TOKEN", $token, $Scope)
    [Environment]::SetEnvironmentVariable("INGRESO_EMAIL_SIGNING_SECRET", $secret, $Scope)
    Write-Host "Variables configuradas ($Scope). Guardar estos valores:"
} catch {
    Write-Host "No se pudieron escribir variables en el registro ($Scope)."
    Write-Host "Se dejaron cargadas SOLO en la sesion actual."
    Write-Host "Error: $($_.Exception.Message)"
}

if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
    $token | Set-Clipboard
    Write-Host "Token copiado al portapapeles (INGRESO_TRAY_TOKEN)."
}
Write-Host "INGRESO_TRAY_TOKEN=$token"
Write-Host "INGRESO_EMAIL_SIGNING_SECRET=$secret"
Write-Host "Reiniciá el servicio/app server para aplicar cambios."
