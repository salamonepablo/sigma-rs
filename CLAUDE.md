# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Instructions

See `docs/agents/CLAUDE.md` for full orchestration rules. Key points:

- Respond to the user in **Spanish**. Write code, docstrings, and technical docs in **English**.
- Apply Clean Architecture, SOLID, and TDD policies from `docs/agents/AGENTS.md`.
- Before changing code, select relevant skills from `.agent/skills/SKILLS.md`.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## Commands

```bash
# Run server
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application

# Run all tests
pytest -q

# Run single test by name pattern
pytest -k "test_name_here" -v

# Run specific test file
pytest tests/tickets/domain/test_entities.py -v

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Lint
ruff check .
ruff format --check .

# Django checks
python manage.py check
python manage.py makemigrations --check

# Full quality gate (run before pushing)
python manage.py check && python manage.py makemigrations --check && ruff check . && pytest -q

# Import kilometrage from legacy TXT files
python manage.py import_kilometrage        # incremental
python manage.py import_kilometrage --full # full reimport (deduplication applied)

# Import kilometrage from Access database (Locs or CCRR)
python manage.py import_kilometrage_access --type locs
python manage.py import_kilometrage_access --type ccrr --update  # update existing records

# Build km snapshot (pre-computes per-unit km-since-last-intervention; run after bulk km import)
python manage.py build_km_snapshot

# Sync novedad km values from km records
python manage.py sync_novedades_kilometraje

# Load initial reference data
python manage.py load_initial_data

# One-time migration helpers
python manage.py migrate_railcar_wagons
python manage.py seed_wagon_cycles
python manage.py backfill_novedad_legacy_codes
python manage.py normalize_cnrdalian_ckd_codes

# SQLite maintenance
python manage.py maintenance_vacuum
python manage.py maintenance_vacuum --analyze
```

Set `SKIP_KILOMETRAGE_IMPORT=1` to skip the heavy legacy migration import during test runs.

## Architecture

**Clean Architecture modular monolith** — single module `apps/tickets/` organized into four layers:

```
apps/tickets/
├── domain/           # Pure Python — no Django imports. Entities are @dataclass,
│   ├── entities/     # repository interfaces are ABC.
│   ├── repositories/ # Interfaces only; implementations live in infrastructure.
│   ├── services/     # Domain services (business logic).
│   ├── dto/          # Data Transfer Objects between layers.
│   └── value_objects/# Immutable domain value types.
├── application/
│   ├── use_cases/    # Orchestrates domain objects; depends only on domain.
│   └── formatters/   # Pure formatting utilities (e.g. km_format.py).
├── infrastructure/   # Django ORM models, repository implementations, PDF/mail services.
│   ├── models/
│   ├── repositories/
│   ├── services/     # pdf_generator.py (WeasyPrint), outlook_client.py (Outlook draft via COM),
│   │                 # kilometrage_repository.py, unit_maintenance_snapshot_service.py.
│   ├── migrations/
│   └── management/   # Custom management commands.
└── presentation/     # Views, forms, templates, URL routing.
    ├── views/        # ticket_views.py, novedad_views.py, tray_api.py, ingreso_email_api.py.
    ├── forms/
    └── templates/
```

**Dependency rule**: domain ← application ← presentation; infrastructure implements domain interfaces.

Shared base classes and exceptions live in `shared/`. Tests mirror the source structure under `tests/tickets/`.

**URL routing**: all routes live under `/sigma/` with namespace `tickets:`. Root `/` redirects there. Reference: `config/urls.py`.

**Core workflow** (`MaintenanceEntryUseCase`): a Novedad (maintenance event) is the entry point. From it, `prepare_draft` computes the intervention suggestion and history; `create_entry` saves the entry, generates a PDF (WeasyPrint), and enqueues an email dispatch record. The tray app polls the dispatch queue and sends Outlook drafts via COM automation.

**Km snapshot** (`UnitMaintenanceSnapshotService` / `build_km_snapshot`): pre-computes km-since-last-intervention per unit to avoid live SUM queries on every ingreso. Falls back to live queries if no snapshot exists. Rebuild after bulk km imports.

**Email dispatch queue** (`MaintenanceEntryEmailDispatchModel`): decoupled from the web request. The tray app claims and sends pending dispatches. `ingreso_email_api.py` exposes the claim/ack endpoints.

**Access DB integration**: PowerShell extractor script (`extractor_access.ps1`) reads legacy `.mdb` files; `import_kilometrage_access` calls it via subprocess and upserts records.

**Tray app** (`tray-app/`): local Windows tray application. Packaged separately with PyInstaller. See `docs/TRAY_APP_INSTALL_ES.md`.

**Initial data**: CSV seed files for maintenance units and personnel live in `context/ums.csv` and `context/personal.csv` (loaded by `load_initial_data`).

> Note: `docs/agents/AGENTS.md` still references a `core/` legacy app that has been fully removed. Ignore those references.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.1 |
| WSGI Server | Waitress 3.0.0 |
| Database | SQLite |
| Linter | Ruff 0.8.6 (rules: E, W, F, I, B, C4, ARG, SIM) |
| Test Runner | pytest 8.3.5 |

## Code Style

- Type hints mandatory on public functions; use `T | None` not `Optional[T]`.
- Docstrings: Google format in English. Test descriptions in Spanish (business context).
- Line length: 88 (ruff default).
- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`.

## Environment Variables

Defined in `.env` at project root (auto-loaded by `config/settings.py`):

| Variable | Purpose |
|----------|---------|
| `INGRESO_TRAY_TOKEN` | Shared secret between Django and the tray app for dispatch API auth |
| `INGRESO_EMAIL_SIGNING_SECRET` | HMAC secret for signing ingreso email payloads |
| `INGRESO_REQUEST_CACHE_ENABLED` | Set to `1` to enable request-scoped draft/km caching |
| `LEGACY_DATA_PATH` | Path to legacy TXT kilometrage files (defaults to `context/db-legacy`) |
| `ACCESS_BASELOCS_PATH` | Path to Access `.mdb` for locomotive km |
| `ACCESS_BASECCRR_PATH` | Path to Access `.mdb` for CCRR km |
| `ACCESS_DB_PASSWORD` | Password for the Access database |
| `ACCESS_EXTRACTOR_SCRIPT` | Path to the PowerShell extractor script |
| `SKIP_KILOMETRAGE_IMPORT` | Set to `1` to skip heavy km migration during tests |

## Domain Glossary

| Term | Meaning |
|------|---------|
| Loc / Locs | Locomotora(s) |
| CR / CCRR | Coche(s) Remolcado(s) |
| CM / CMN | Coche Motor |
| GOP | Guardia Operativa |
| OT | Orden de Trabajo |
| UM | Unidad de Mantenimiento |
| MR | Material Rodante (rolling stock) |
| Novedad | Maintenance work order / event record (`NovedadModel`) |
| Ingreso | Maintenance entry document generated from a Novedad |
| Lugar | Physical location / workshop where maintenance occurs |
| RG | Reparación General — full overhaul intervention code |
| RP | Reparación Parcial — partial repair intervention code |
| A1–A4, SEM, MEN | Periodic inspection codes (hierarchy: A4 > A3 > A2 > A1 > SEM > MEN) |
| ABC | Inspection sub-type used for some rolling stock families |
| CKD | Chinese locomotive family (Dalian CNR); detected by brand/model heuristics |
