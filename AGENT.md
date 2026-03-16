# AGENT.md — Sigma-RS Orchestrator (Lite)

This file defines how AI agents should coordinate work in this repository.

## Role

You are a **coordinator + executor** in a practical hybrid mode:

- For small requests: execute directly.
- For medium/large requests: follow phase flow (`explore -> propose -> apply -> verify`).
- Keep user communication concise and decision-oriented.

## Source of Truth

Before starting any task, load in this order:

1. `AGENTS.md`
2. `.agent/skills/SKILLS.md`
3. Required skill files from the registry

If any rule conflicts, `AGENTS.md` wins.

## Lite Phase Flow

### 1) Explore

- Confirm scope and constraints.
- Inspect relevant files and dependencies.
- Identify architecture boundary impacts (domain/application/infrastructure/presentation).

### 2) Propose

- Describe minimal change set.
- Call out risks and migration/testing impact.
- Align with CLEAN + SOLID.

### 3) Apply

- Implement smallest safe patch first.
- Avoid unrelated refactors.
- Preserve public APIs unless change is required.

### 4) Verify

- Run or reason about checks:
  - `python manage.py check`
  - `ruff check .`
  - `pytest -q`
- Report what was validated and what was not run.

## TDD Policy

When feasible, use:

1. Add/update failing test (Red)
2. Implement minimal code (Green)
3. Refactor safely (Refactor)

Bugfixes should include a regression test.

## Session Notes

For substantial work, append a short summary to `docs/ends_day/YYYY-MM-DD.md` when requested by the user.

## Anti-Patterns

- Do not bypass domain rules from presentation layer.
- Do not add infrastructure imports into domain modules.
- Do not mix unrelated fixes in a single patch.
- Do not skip validation silently.
