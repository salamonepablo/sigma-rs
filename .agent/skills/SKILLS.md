# Sigma-RS Skills Registry

Load relevant skills **before implementation**.

## How to use

1. Identify task type.
2. Load one or more matching skills.
3. Apply checklists and done criteria.
4. Keep changes aligned with `docs/agents/AGENTS.md`.

## Skills

| Skill | Trigger | Path |
|---|---|---|
| `clean-arch-guard` | Any change touching boundaries between domain/application/infrastructure/presentation. | `.agent/skills/clean-arch-guard/SKILL.md` |
| `solid-refactor` | Refactors, extraction, decomposition, reducing conditional complexity. | `.agent/skills/solid-refactor/SKILL.md` |
| `tdd-pytest-cycle` | New behavior, bugfixes, regression scenarios. | `.agent/skills/tdd-pytest-cycle/SKILL.md` |
| `django-usecase-flow` | Maintenance entry workflow, use cases, views/forms orchestration. | `.agent/skills/django-usecase-flow/SKILL.md` |
| `pdf-email-maint-entry` | PDF generation, mail draft body/subject, formatting consistency. | `.agent/skills/pdf-email-maint-entry/SKILL.md` |
