# SIGMA-RS User Migration ToDo (from `pablo.salamone` to `Juan.Navone`)

> Goal: move the full SIGMA-RS server operation to `C:\Users\Juan.Navone` (app runtime, auto-start, DB maintenance, and GitHub auto-update flow used by `servidor_auto.ps1`).

---

## 0) Pre-migration safety (must do first)

- [ ] Confirm current service is healthy at `http://172.22.181.1:8000/`.
- [ ] Confirm latest code is on `origin/main`.
- [ ] Create a full backup copy of the current project folder:
  - `C:\Users\pablo.salamone\Programmes\sigma-rs`
- [ ] Backup SQLite DB and automatic backups folder:
  - `db\app.db`
  - `db\backups\`
- [ ] Export or securely transfer required secrets/env files (do **not** commit them):
  - `secrets\ingreso_env.ps1`
  - `.env` (if used)

---

## 1) Create destination working folder under new user

- [ ] Log in as `Juan.Navone`.
- [ ] Create destination path:
  - `C:\Users\Juan.Navone\Programmes\sigma-rs`
- [ ] Copy project files from old profile to new profile (including `db/`, `logs/`, `ops/`, `scripts/`, `secrets/`).
- [ ] Verify NTFS permissions: `Juan.Navone` must have read/write on full project tree.

---

## 2) Python environment on new user

- [ ] Open PowerShell in `C:\Users\Juan.Navone\Programmes\sigma-rs`.
- [ ] Create venv and install dependencies:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

- [ ] Run migrations/checks:

```powershell
python manage.py migrate
python manage.py check
ruff check .
```

---

## 3) Update hardcoded profile paths (critical)

The startup batch scripts currently include absolute path to `pablo.salamone`.

- [ ] Edit `ops\install_to_startup.bat`:
  - Update `set "PROJECT=..."` to `C:\Users\Juan.Navone\Programmes\sigma-rs`
- [ ] Edit `ops\start_sigma_rs.bat`:
  - Update `set "PROJECT=..."` to `C:\Users\Juan.Navone\Programmes\sigma-rs`
- [ ] (Optional but recommended) replace hardcoded path usage with dynamic script-relative path logic to avoid future user migrations.

---

## 4) GitHub access for auto-update (`servidor_auto.ps1`)

`servidor_auto.ps1` runs `git fetch/pull`, so `Juan.Navone` needs valid GitHub auth.

- [ ] Configure GitHub auth for `Juan.Navone` (choose one):
  - [ ] SSH key + repo access, **or**
  - [ ] Git Credential Manager (HTTPS) login with account that can read `salamonepablo/sigma-rs`.
- [ ] Test manually as `Juan.Navone`:

```powershell
git -C "C:\Users\Juan.Navone\Programmes\sigma-rs" fetch origin main
git -C "C:\Users\Juan.Navone\Programmes\sigma-rs" pull origin main
```

- [ ] Ensure remote URL is correct:

```powershell
git -C "C:\Users\Juan.Navone\Programmes\sigma-rs" remote -v
```

---

## 5) Startup auto-run under new user

- [ ] While logged as `Juan.Navone`, install startup entry:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\install_to_startup.bat
```

- [ ] Verify startup file exists in:
  - `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\start_sigma_rs.bat`
- [ ] Remove old startup entry from `pablo.salamone` profile to avoid double-running service.

---

## 6) Re-register DB maintenance scheduled tasks for new user context

- [ ] Register tasks from new profile:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\register_db_tasks.ps1
```

- [ ] Verify tasks exist:

```powershell
schtasks /Query /TN SigmaRS-DB-Backup-Integrity
schtasks /Query /TN SigmaRS-DB-Vacuum
```

- [ ] Confirm task "Run As" account is appropriate for unattended execution.

---

## 7) Functional validation (new user)

- [ ] Start service manually once:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\servidor_auto.ps1
```

- [ ] Validate web access from another internal PC:
  - `http://172.22.181.1:8000/`
- [ ] Run one manual sync from UI and confirm no errors.
- [ ] Verify new logs/backups are being created under new profile project path.

---

## 8) Cutover and cleanup

- [ ] Stop old session/processes running under `pablo.salamone`.
- [ ] Reboot terminal PC and verify startup under `Juan.Navone` works automatically.
- [ ] Confirm after reboot:
  - [ ] Waitress is running
  - [ ] URL responds
  - [ ] `servidor_auto.ps1` loop is active
  - [ ] Scheduled tasks are present and enabled
- [ ] Keep old profile/project backup read-only for rollback window (recommended: 1-2 weeks).

---

## 9) Rollback plan (if anything fails)

- [ ] Stop `Juan.Navone` server processes.
- [ ] Restore previous startup/task configuration for `pablo.salamone`.
- [ ] Restore previous working project folder and DB (`db\app.db`).
- [ ] Re-test URL and manual sync.

---

## Quick acceptance checklist

- [ ] App reachable at `http://172.22.181.1:8000/`
- [ ] `servidor_auto.ps1` fetch/pull works with new user credentials
- [ ] Manual sync works without JSON errors
- [ ] DB backup/integrity/vacuum automation active
- [ ] Old user disabled from runtime path
