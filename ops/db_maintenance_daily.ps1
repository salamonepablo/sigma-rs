# Daily SQLite maintenance: backup + integrity check

$ErrorActionPreference = "Stop"

$projectPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $projectPath "venv\Scripts\python.exe"
$logsDir = Join-Path $projectPath "logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logsDir "db_maintenance_daily_$timestamp.log"

if (-not (Test-Path $pythonPath)) {
    throw "Python executable not found at $pythonPath"
}

New-Item -Path $logsDir -ItemType Directory -Force | Out-Null

Start-Transcript -Path $logPath -Force

try {
    Write-Host "[$(Get-Date -Format s)] Running db_backup"
    & $pythonPath "$projectPath\manage.py" db_backup --retention-days 30
    if ($LASTEXITCODE -ne 0) {
        throw "db_backup failed with exit code $LASTEXITCODE"
    }

    Write-Host "[$(Get-Date -Format s)] Running db_integrity_check"
    & $pythonPath "$projectPath\manage.py" db_integrity_check
    if ($LASTEXITCODE -ne 0) {
        throw "db_integrity_check failed with exit code $LASTEXITCODE"
    }

    Write-Host "[$(Get-Date -Format s)] Daily DB maintenance finished successfully"
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Stop-Transcript | Out-Null
}

exit 0
