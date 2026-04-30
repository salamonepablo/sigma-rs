# Weekly SQLite maintenance: VACUUM + ANALYZE

$ErrorActionPreference = "Stop"

$projectPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $projectPath "venv\Scripts\python.exe"
$logsDir = Join-Path $projectPath "logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logsDir "db_maintenance_weekly_$timestamp.log"

if (-not (Test-Path $pythonPath)) {
    throw "Python executable not found at $pythonPath"
}

New-Item -Path $logsDir -ItemType Directory -Force | Out-Null

Start-Transcript -Path $logPath -Force

try {
    Write-Host "[$(Get-Date -Format s)] Running maintenance_vacuum --analyze"
    & $pythonPath "$projectPath\manage.py" maintenance_vacuum --analyze
    if ($LASTEXITCODE -ne 0) {
        throw "maintenance_vacuum failed with exit code $LASTEXITCODE"
    }

    Write-Host "[$(Get-Date -Format s)] Weekly DB maintenance finished successfully"
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Stop-Transcript | Out-Null
}

exit 0
