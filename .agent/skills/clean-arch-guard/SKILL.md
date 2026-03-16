# Skill: clean-arch-guard

## Intent

Protect CLEAN Architecture boundaries and dependency direction.

## Apply when

- Moving logic across layers.
- Adding new services/repositories.
- Updating use cases that touch domain and infrastructure.

## Rules

- Domain layer has no Django/framework imports.
- Application layer orchestrates workflows and uses domain abstractions.
- Infrastructure implements persistence, integrations, framework concerns.
- Presentation handles HTTP/forms/templates only.

## Checklist

- [ ] No infrastructure import leaked into domain.
- [ ] Business rule belongs to domain or application, not view/template.
- [ ] New dependency direction follows outer -> inner only.
- [ ] Public contracts preserved or explicitly migrated.

## Done criteria

- Layer responsibilities are clear.
- No architecture regression introduced.
