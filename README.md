# SIGMA-RS - Rolling Stock Ticketing System

SIGMA-RS is a Django-based system for tracking maintenance tickets for rolling stock. It replaces legacy MS Access workflows and supports multi-user access on a corporate LAN.

## Requirements

- Python 3.11+
- Internet access for initial dependency install

## Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/[usuario]/SIGMA-RS.git
cd SIGMA-RS

# 2. Create venv
python -m venv venv

# 3. Activate venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Load initial data (reference + personal)
python manage.py load_initial_data

# 8. Run server
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
```

## URLs

| Resource | URL |
|---|---|
| App | http://[SERVER_IP]:8000/sigma/ |
| Login | http://[SERVER_IP]:8000/sigma/login/ |
| Admin | http://[SERVER_IP]:8000/admin/ |

## Project Structure

```
sigma-rs/
├── apps/
│   └── tickets/          # Domain + application + infrastructure + presentation
├── config/               # Django settings, urls, wsgi
├── db/                   # SQLite database
├── static/               # Static assets
├── docs/                 # Documentation
├── tests/                # Tests
├── manage.py
└── requirements.txt
```

## Initial Data

The command `python manage.py load_initial_data` loads:

- Reference data (brands, GOPs, failure types, affected systems)
- Maintenance units (from `context/ums.csv`)
- Personnel (intervinientes) from `context/personal.csv`

## Kilometrage Updates

Kilometrage records are stored in the database. To import legacy TXT updates:

```powershell
python manage.py import_kilometrage
```

Use `--full` to reimport everything (duplicates are ignored):

```powershell
python manage.py import_kilometrage --full
```

For test runs, you can skip the heavy legacy import in migrations:

```powershell
set SKIP_KILOMETRAGE_IMPORT=1
```

## Database Maintenance (SQLite)

To compact the SQLite file and report size before/after:

```powershell
python manage.py maintenance_vacuum
```

Optionally run ANALYZE:

```powershell
python manage.py maintenance_vacuum --analyze
```

## CI (GitHub Actions)

Each push/PR runs:

- `ruff check .`
- `ruff format --check .`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `pytest -q`

## Notes

- `core/` prototype app was removed. All functionality lives in `apps/tickets/`.
- Ticket numbers are auto-generated (YYYY-NNNN).
- Login lives at `/sigma/login/` and redirects to `/sigma/`.

## Security

Do not commit sensitive files (`.env`, database files, credentials).

Because the repository is public, never upload official, personal, or confidential data. Use a local `.env` file for sensitive configuration and keep it out of version control.

## Changelog

See `docs/CHANGELOG.md`.
