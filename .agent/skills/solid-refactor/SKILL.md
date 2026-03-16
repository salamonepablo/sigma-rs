---
id: solid-refactor
name: SOLID Refactor
---

# Skill: solid-refactor

## Intent

Refactor safely with SOLID principles.

## Apply when

- Extracting methods/classes.
- Replacing conditional branching with policies/strategies.
- Splitting responsibilities.

## Rules

- Single Responsibility: one reason to change.
- Open/Closed: prefer extension over modification.
- Liskov: keep behavior contracts stable.
- Interface Segregation: narrow interfaces.
- Dependency Inversion: depend on abstractions at boundaries.

## Checklist

- [ ] Responsibilities reduced, not expanded.
- [ ] Conditional complexity reduced where meaningful.
- [ ] Contracts and call sites remain valid.
- [ ] Refactor covered by tests.

## Done criteria

- Code is easier to extend and reason about.
- No behavior change unless explicitly requested.
