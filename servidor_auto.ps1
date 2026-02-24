# servidor_auto.ps1 - Servidor SIGMA-RS con sync automatico

$projectPath = "C:\Users\pablo.salamone\Programmes\sigma-rs"
$checkInterval = 120
$venvPython = "$projectPath\venv\Scripts\python.exe"
$waitressJob = $null

Set-Location $projectPath

Write-Host "============================================"
Write-Host "  SIGMA-RS - Servidor Automatico"
Write-Host "============================================"
Write-Host "Sync cada: $checkInterval segundos"
Write-Host "Presiona Ctrl+C para detener"
Write-Host "============================================"

# Iniciar Waitress en background
Write-Host "Iniciando Waitress..."
$waitressJob = Start-Job -ScriptBlock {
    param($python, $path)
    Set-Location $path
    & $python -m waitress --host=0.0.0.0 --port=8000 --threads=16 config.wsgi:application
} -ArgumentList $venvPython, $projectPath

Write-Host "Waitress iniciado (Job ID: $($waitressJob.Id))"
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds $checkInterval
        
        Set-Location $projectPath
        $before = git rev-parse HEAD
        git fetch origin main 2>$null
        $after = git rev-parse origin/main
        
        if ($before -ne $after) {
            Write-Host ""
            Write-Host "[CAMBIOS DETECTADOS] Actualizando..."
            
            # Detener Waitress
            Stop-Job -Job $waitressJob -ErrorAction SilentlyContinue
            Remove-Job -Job $waitressJob -Force -ErrorAction SilentlyContinue
            
            # Pull
            git pull origin main
            
            # Migrate
            & $venvPython manage.py migrate --no-input
            
            # Reiniciar Waitress
            $waitressJob = Start-Job -ScriptBlock {
                param($python, $path)
                Set-Location $path
                & $python -m waitress --host=0.0.0.0 --port=8000 --threads=16 config.wsgi:application
            } -ArgumentList $venvPython, $projectPath
            
            Write-Host "[ACTUALIZADO] Servidor reiniciado"
            [console]::beep(1000,200)
        }
        else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Sin cambios"
        }
    }
}
finally {
    Stop-Job -Job $waitressJob -ErrorAction SilentlyContinue
    Remove-Job -Job $waitressJob -Force -ErrorAction SilentlyContinue
    Write-Host "Servidor detenido."
}
