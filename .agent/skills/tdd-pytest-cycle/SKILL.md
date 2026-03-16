# Skill: tdd-pytest-cycle

## Intent

Apply Red -> Green -> Refactor with pytest in Sigma-RS.

## Apply when

- Implementing new behavior.
- Fixing bugs.
- Touching core business rules.

## Process

1. Red: add/adjust failing test.
2. Green: implement minimal change.
3. Refactor: improve structure safely.

## Testing baseline

- `python manage.py check`
- `ruff check .`
- `pytest -q`

## Checklist

- [ ] Test fails before implementation (when feasible).
- [ ] Regression test added for bugfixes.
- [ ] Assertions reflect business behavior.
- [ ] Tests remain readable and deterministic.

## Done criteria

- Target behavior is covered by tests.
- All relevant checks pass or failures are explicitly reported.
