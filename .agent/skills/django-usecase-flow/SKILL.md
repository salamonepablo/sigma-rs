---
id: django-usecase-flow
name: Django Usecase Flow
---

# Skill: django-usecase-flow

## Intent

Keep Django workflow changes aligned with use-case orchestration.

## Apply when

- Editing maintenance entry flow.
- Updating forms/views/use cases for tickets/novedades.
- Changing recipient resolution, suggestions, or orchestration.

## Rules

- View: request/response, messages, redirects.
- Form: validation and field-level concerns.
- Use case: business orchestration and side effects.
- Domain service: pure decision logic.

## Checklist

- [ ] Business decisions live outside views/templates.
- [ ] Use case remains the orchestration center.
- [ ] Query changes are explicit and safe.
- [ ] Backward compatibility considered for existing URLs/forms.

## Done criteria

- Workflow remains coherent end-to-end.
- Layer boundaries are preserved.
