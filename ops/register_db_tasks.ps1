# Register Windows scheduled tasks for SQLite maintenance

$ErrorActionPreference = "Stop"

$taskDaily = "SigmaRS-DB-Backup-Integrity"
$taskWeekly = "SigmaRS-DB-Vacuum"

$projectPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$dailyScript = Join-Path $projectPath "ops\db_maintenance_daily.ps1"
$weeklyScript = Join-Path $projectPath "ops\db_maintenance_weekly.ps1"

if (-not (Test-Path $dailyScript)) {
    throw "Daily script not found at $dailyScript"
}

if (-not (Test-Path $weeklyScript)) {
    throw "Weekly script not found at $weeklyScript"
}

$dailyCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$dailyScript`""
$weeklyCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$weeklyScript`""

schtasks /Create /TN $taskDaily /SC DAILY /ST 23:50 /TR $dailyCommand /F
if ($LASTEXITCODE -ne 0) {
    throw "Failed to register task $taskDaily"
}

schtasks /Create /TN $taskWeekly /SC WEEKLY /D SUN /ST 03:00 /TR $weeklyCommand /F
if ($LASTEXITCODE -ne 0) {
    throw "Failed to register task $taskWeekly"
}

Write-Host "Scheduled tasks registered successfully:"
Write-Host " - $taskDaily (daily 23:50)"
Write-Host " - $taskWeekly (weekly Sunday 03:00)"
