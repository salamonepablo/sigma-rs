# Architecture - SIGMA-RS

## Overview

SIGMA-RS follows a **Clean Architecture** pattern organized as a **modular monolith**. This allows for clear separation of concerns while maintaining simplicity for deployment.

## Folder Structure

```
sigma-rs/
├── config/                         # Django configuration (settings, wsgi, urls)
├── apps/                           # Application modules (bounded contexts)
│   └── tickets/                    # Tickets module
│       ├── domain/                 # Domain layer (pure Python, no Django)
│       │   ├── entities/           # Domain entities (@dataclass)
│       │   ├── repositories/       # Repository interfaces (ABC)
│       │   └── services/           # Domain services (business logic)
│       ├── application/            # Application layer
│       │   └── use_cases/          # Use cases / interactors
│       ├── infrastructure/         # Infrastructure layer (Django, DB)
│       │   ├── models/             # Django ORM models
│       │   ├── repositories/       # Repository implementations
│       │   └── migrations/         # Django migrations
│       └── presentation/           # Presentation layer (HTTP)
│           ├── views/              # Django views
│           ├── forms/              # Django forms
│           ├── templates/          # HTML templates
│           └── urls.py             # URL routing
├── shared/                         # Shared code across modules
│   ├── domain/                     # Base classes, exceptions
│   └── infrastructure/             # Common utilities
├── core/                           # Legacy app (to be migrated)
├── tests/                          # Test suite (mirrors source structure)
│   └── tickets/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── presentation/
├── static/                         # Static files (CSS, JS, images)
├── docs/                           # Documentation
├── context/                        # Project context and prompts
└── db/                             # SQLite database
```

## Layer Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION                            │
│  (views, forms, templates, urls)                            │
│  Can import: application, domain, infrastructure            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION                             │
│  (use_cases)                                                │
│  Can import: domain                                         │
│  Uses: repository interfaces (injected)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOMAIN                                │
│  (entities, value_objects, repository interfaces, services) │
│  Can import: nothing (pure Python)                          │
│  NO Django imports allowed                                  │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE                           │
│  (Django models, repository implementations, migrations)    │
│  Can import: domain                                         │
│  Implements: repository interfaces                          │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Domain is pure Python**: No Django imports in `domain/` layer. Entities are `@dataclass` with validation in `__post_init__`.

2. **Dependency Inversion**: Application layer depends on repository interfaces (defined in domain), not implementations.

3. **Repository Pattern**: Infrastructure layer implements repository interfaces, converting between Django models and domain entities.

4. **Modular Monolith**: Each module in `apps/` is a bounded context that can potentially be extracted to a microservice.

## Adding a New Module

1. Create folder structure under `apps/<module_name>/`
2. Define domain entities in `domain/entities/`
3. Define repository interfaces in `domain/repositories/`
4. Implement Django models in `infrastructure/models/`
5. Implement repositories in `infrastructure/repositories/`
6. Create use cases in `application/use_cases/`
7. Create views and templates in `presentation/`
8. Add URLs to main router in `config/urls.py`

## Migration Strategy

The legacy `core/` app will be gradually migrated to the new structure:
1. Extract domain entities from `core/models.py` to `apps/tickets/domain/entities/`
2. Create repository interfaces
3. Implement repositories using existing Django models
4. Refactor views to use cases
5. Eventually remove `core/` when migration is complete
