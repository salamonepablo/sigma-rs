# AGENTS.md - SIGMA-RS (Sistema de Gestión de Tickets para Material Rodante)

> AI coding agent instructions. Respond in  **Spanish**. Code, docstrings, and technical docs in **English**.

## AI Orchestration Entry Points

- Main project contract: `AGENTS.md` (this file)
- Orchestrator guide: `AGENT.md`
- Claude CLI bridge: `CLAUDE.md`
- Skills registry: `.agent/skills/SKILLS.md`

## Engineering Principles (Mandatory)

### CLEAN Architecture

- Keep domain logic isolated from frameworks and infrastructure details.
- Follow dependency rule: outer layers depend on inner layers, never the reverse.
- Use application/use-case layer for orchestration and business workflows.

### SOLID

- **S**: One reason to change per module/class/function.
- **O**: Extend behavior through composition/policies instead of risky condition sprawl.
- **L**: Respect contracts when replacing implementations.
- **I**: Keep interfaces narrow and purpose-driven.
- **D**: Depend on abstractions in domain/application boundaries.

### TDD

- Prefer **Red → Green → Refactor** for non-trivial changes.
- Write/adjust failing tests first when possible.
- Every bug fix should include a regression test.
- Run at minimum: `python manage.py check`, `ruff check .`, `pytest -q`.

## Quick Start

```powershell
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Run server
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
```

## Project Structure

```
sigma-rs/
├── config/        # Django settings, WSGI, URLs
├── core/          # Main app (models, views, templates)
├── db/            # SQLite database
├── static/        # Static files
├── docs/          # Documentation
├── tests/         # Tests (mirror structure)
└── manage.py      # Django entrypoint
```

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend | Django | 5.1 |
| WSGI Server | Waitress | 3.0.0 |
| Database | SQLite | default |
| Linter | Ruff | 0.8.6 |
| Test Runner | pytest | 8.3.5 |
| Python | 3.11+ | |

## Commands

```powershell
# Django checks
python manage.py check
python manage.py makemigrations --check

# Lint (required before push)
ruff check .

# Run all tests
pytest -q

# Run single test (by name pattern)
pytest -k "test_name_here" -v

# Run specific test file
pytest tests/core/test_models.py -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

## Code Style

- **Imports order**: stdlib → third-party → local/first-party
- **Type hints**: Mandatory on public functions, use `None` instead of `Optional[x]`
- **Docstrings**: Google format, in English. Tests in Spanish (business context)
- **Naming**: Classes PascalCase, functions snake_case, constants UPPER_SNAKE
- **Line length**: 88 characters (ruff default)
- **Ruff rules enabled**: E, W, F, I, B, C4, ARG, SIM

## Django Models

```python
import uuid
from django.db import models

class TicketModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField("Título", max_length=200)
    descripcion = models.TextField("Descripción")
    estado = models.CharField("Estado", max_length=20)
    created_at = models.DateTimeField("Creado", auto_now_add=True)

    class Meta:
        db_table = "ticket"
        verbose_name = "Ticket"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.titulo
```

## Tests

```python
import pytest
from core.models import TicketModel

class TestTicketModel:
    """Business tests for Ticket model."""

    def test_str(self):
        ticket = TicketModel(titulo="Test", descripcion="Desc", estado="nuevo")
        assert str(ticket) == "Test"
```

- Test classes: `Test*` prefix
- Test methods: `test_*` prefix
- Fixtures in `conftest.py`
- Use `unittest.mock.patch` for mocking

## Error Handling & Logging

- Use descriptive exceptions (`ValueError`, custom exceptions)
- Logging: `logging.getLogger(__name__)`
- Close connections in `finally` blocks
- Django: use `get_object_or_404` for 404 handling

## Git Workflow

```powershell
# Make changes
git add .
git commit -m "feat: clear description"
git push origin main
```

- Use conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`
- Never commit: `.env`, `db.sqlite3`, credentials
- Run CI pipeline before pushing

## CI Pipeline

```powershell
python manage.py check
python manage.py makemigrations --check
ruff check .
pytest -q
```

## Domain Glossary

| Abbreviation | Meaning |
|--------------|---------|
| Loc, Locs | Locomotora(s) |
| CR, CCRR | Coche(s) Remolcado(s) |
| CM, CMN | Coche Motor |
| GOP | Guardia Operativa |
| OT | Orden de Trabajo |

---

See `docs/SIGMA-RS_RESUMEN_PROYECTO.md` for details.
Changelog at `docs/CHANGELOG.md`.
