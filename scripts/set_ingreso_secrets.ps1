# set_ingreso_secrets.ps1
# Genera y configura secretos para Sigma-RS (Machine scope)
$token = -join ((65..90)+(97..122)+(48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
$secret = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 } | ForEach-Object { [byte]$_ }))
[Environment]::SetEnvironmentVariable("INGRESO_TRAY_TOKEN", $token, "Machine")
[Environment]::SetEnvironmentVariable("INGRESO_EMAIL_SIGNING_SECRET", $secret, "Machine")

if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
    $token | Set-Clipboard
    Write-Host "Token copiado al portapapeles (INGRESO_TRAY_TOKEN)."
}
Write-Host "Variables configuradas (Machine). Guardar estos valores:"
Write-Host "INGRESO_TRAY_TOKEN=$token"
Write-Host "INGRESO_EMAIL_SIGNING_SECRET=$secret"
Write-Host "Reiniciá el servicio/app server para aplicar cambios."
