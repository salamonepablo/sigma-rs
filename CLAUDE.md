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
- Delegate ALL execution work (code reading/writing, tests, analysis) to sub-agents.

## Validation Baseline

For non-trivial changes, validate with:

- `python manage.py check`
- `ruff check .`
- `pytest -q`

## Skill-Driven Execution

Before changing code, select relevant skills from `.agent/skills/SKILLS.md`.

## Orchestrator Contract

- Do not execute changes inline.
- Sub-agents must return: Status, Summary, Artifacts, Next, Risks.
- Prefer Engram for persistence unless user asks for file artifacts.

## SDD Commands

- `/sdd-init`
- `/sdd-explore <topic>`
- `/sdd-new <change>`
- `/sdd-continue`
- `/sdd-ff <change>`
- `/sdd-apply`
- `/sdd-verify`
- `/sdd-archive`

Examples:

- Maintenance flow changes → `django-usecase-flow`, `tdd-pytest-cycle`
- PDF/mail output changes → `pdf-email-maint-entry`, `tdd-pytest-cycle`
- Structural refactor → `clean-arch-guard`, `solid-refactor`, `tdd-pytest-cycle`
