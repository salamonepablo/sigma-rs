# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Instructions

See `docs/agents/CLAUDE.md` for full orchestration rules. Key points:

- Respond to the user in **Spanish**. Write code, docstrings, and technical docs in **English**.
- Apply Clean Architecture, SOLID, and TDD policies from `docs/agents/AGENTS.md`.
- Before changing code, select relevant skills from `.agent/skills/SKILLS.md`.

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

# Load initial reference data
python manage.py load_initial_data

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
│   └── use_cases/    # Orchestrates domain objects; depends only on domain.
├── infrastructure/   # Django ORM models, repository implementations, PDF/mail services.
│   ├── models/
│   ├── repositories/
│   ├── services/     # pdf_generator.py (WeasyPrint), outlook_client.py (Outlook draft via COM).
│   ├── migrations/
│   └── management/   # Custom management commands (import_kilometrage, load_initial_data, etc.)
└── presentation/     # Views, forms, templates, URL routing.
    ├── views/
    ├── forms/
    └── templates/
```

**Dependency rule**: domain ← application ← presentation; infrastructure implements domain interfaces.

Shared base classes and exceptions live in `shared/`. Tests mirror the source structure under `tests/tickets/`.

**URL routing**: all routes live under `/sigma/` with namespace `tickets:`. Root `/` redirects there. Reference: `config/urls.py`.

**Tray app** (`tray-app/`): local Windows tray application that automates Outlook draft creation. Packaged separately with PyInstaller. See `docs/TRAY_APP_INSTALL_ES.md`.

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

## Domain Glossary

| Term | Meaning |
|------|---------|
| Loc / Locs | Locomotora(s) |
| CR / CCRR | Coche(s) Remolcado(s) |
| CM / CMN | Coche Motor |
| GOP | Guardia Operativa |
| OT | Orden de Trabajo |
| UM | Unidad de Mantenimiento |
