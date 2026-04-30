# SQLite Automation on Windows

This guide describes how to automate SQLite backup, integrity checks, and weekly vacuum tasks using PowerShell scripts and Windows Task Scheduler.

## What is included

- Daily maintenance script: `ops/db_maintenance_daily.ps1`
  - Runs `python manage.py db_backup --retention-days 30`
  - Runs `python manage.py db_integrity_check`
- Weekly maintenance script: `ops/db_maintenance_weekly.ps1`
  - Runs `python manage.py maintenance_vacuum --analyze`
- Task registration script: `ops/register_db_tasks.ps1`
  - `SigmaRS-DB-Backup-Integrity` (daily at 23:50)
  - `SigmaRS-DB-Vacuum` (weekly on Sunday at 03:00)

## Requirements

- Windows host with Task Scheduler enabled
- Project cloned locally
- Virtual environment created at `venv/`
- Django dependencies installed

## Installation

Run PowerShell as Administrator:

```powershell
cd C:\path\to\sigma-rs
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\register_db_tasks.ps1
```

The script recreates tasks if they already exist (`schtasks /F`).

## Validation

### 1. Verify task registration

```powershell
schtasks /Query /TN SigmaRS-DB-Backup-Integrity
schtasks /Query /TN SigmaRS-DB-Vacuum
```

### 2. Run scripts manually once

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\db_maintenance_daily.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\db_maintenance_weekly.ps1
```

### 3. Check outputs

- Daily logs: `logs/db_maintenance_daily_YYYYMMDD_HHMMSS.log`
- Weekly logs: `logs/db_maintenance_weekly_YYYYMMDD_HHMMSS.log`
- Backups: `db/backups/app_YYYYMMDD_HHMMSS.db`

## Backup and retention behavior

- `db_backup` creates a consistent SQLite backup using `sqlite3.Connection.backup`.
- By default backups are written to `db/backups/`.
- `--retention-days` removes older backup files with matching prefix.
- Filename format: `<prefix>_YYYYMMDD_HHMMSS.db` (default prefix: `app`).

## Restore procedure

1. Stop the Django/Waitress process.
2. Select the desired backup from `db/backups/`.
3. Replace `db/app.db` with the selected backup file.
4. Start the application again.
5. Run integrity check:

```powershell
venv\Scripts\python.exe manage.py db_integrity_check
```

## Useful manual commands

```powershell
venv\Scripts\python.exe manage.py db_backup
venv\Scripts\python.exe manage.py db_backup --output-dir C:\temp\sigma-backups --retention-days 14 --prefix sigma
venv\Scripts\python.exe manage.py db_integrity_check
venv\Scripts\python.exe manage.py db_integrity_check --quick
```
