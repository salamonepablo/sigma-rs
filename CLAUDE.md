# CLAUDE.md — Bridge for Claude Code CLI

Claude Code should load this file first, then follow repository contracts.

## Mandatory Load Order

1. `AGENTS.md`
2. `AGENT.md`
3. `.agent/skills/SKILLS.md`
4. Task-relevant skills from `.agent/skills/*/SKILL.md`

## Required Behavior

- Respond to the user in **Spanish**.
- Write code, docstrings, and technical documentation in **English**.
- Apply **CLEAN Architecture**, **SOLID**, and **TDD** policies from `AGENTS.md`.
- Use minimal, focused patches.

## Validation Baseline

For non-trivial changes, validate with:

- `python manage.py check`
- `ruff check .`
- `pytest -q`

## Skill-Driven Execution

Before changing code, select relevant skills from `.agent/skills/SKILLS.md`.

Examples:

- Maintenance flow changes → `django-usecase-flow`, `tdd-pytest-cycle`
- PDF/mail output changes → `pdf-email-maint-entry`, `tdd-pytest-cycle`
- Structural refactor → `clean-arch-guard`, `solid-refactor`, `tdd-pytest-cycle`
