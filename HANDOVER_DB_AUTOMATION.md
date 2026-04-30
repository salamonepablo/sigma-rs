# Handover — Automatización de mantenimiento SQLite (Windows)

## Objetivo

Dejar el mantenimiento de SQLite funcionando en modo autónomo (sin intervención diaria), cubriendo **backup diario**, **chequeo de integridad** y **vacuum semanal**.

## Tareas programadas

- **SigmaRS-DB-Backup-Integrity** → todos los días a las **23:50**
- **SigmaRS-DB-Vacuum** → semanal, **domingo 03:00**

## Instalación (una sola vez)

Ejecutar en PowerShell (idealmente como Administrador):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\register_db_tasks.ps1
```

## Cómo verificar las tareas

```powershell
schtasks /Query /TN SigmaRS-DB-Backup-Integrity
schtasks /Query /TN SigmaRS-DB-Vacuum
```

## Prueba manual

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\db_maintenance_daily.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\db_maintenance_weekly.ps1
```

## Dónde quedan logs y backups

- **Logs diarios:** `logs/db_maintenance_daily_YYYYMMDD_HHMMSS.log`
- **Logs semanales:** `logs/db_maintenance_weekly_YYYYMMDD_HHMMSS.log`
- **Backups SQLite:** `db/backups/app_YYYYMMDD_HHMMSS.db`

## Restauración rápida

1. Detener el proceso de la app (Django/Waitress).
2. Elegir el backup a restaurar desde `db/backups/`.
3. Reemplazar `db/app.db` por el archivo backup elegido.
4. Levantar nuevamente la aplicación.
5. Validar integridad:

```powershell
venv\Scripts\python.exe manage.py db_integrity_check
```

## Contacto/Contexto

Documento preparado para **continuidad operativa sin intervención diaria**. Ante incidentes, priorizar restauración rápida desde backup y luego validación de integridad.
