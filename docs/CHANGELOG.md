# CHANGELOG.md

Todas las modificaciones relevantes del proyecto deben registrarse aquí siguiendo el formato semántico.

## [Unreleased]
### Added
- Login UI redesign with TA and ARS logos.
- New `PersonalModel` (interviniente) and CSV import via `load_initial_data`.
- New `affected_service` field (Yes/No) in ticket form.
- GitHub Actions CI workflow (ruff + tests).
- Ruff configuration and pytest tooling.

### Changed
- Ticket numbers are auto-generated (YYYY-NNNN) and not user-editable.
- Login URL moved to `/sigma/login/` and root redirects to `/sigma/`.
- Supervisor input replaced by `Interviniente` FK selection.
- Navbar updated to `| Material Rodante - Linea Roca |`.
- Project structure documentation updated to reflect `apps/tickets/`.

### Fixed
- Removed prototype app and legacy templates to avoid landing on old index.
- Linting/formatting issues resolved with ruff.

### Removed
- Prototype `core/` app (models, views, templates, urls).

## [v1.0.0] - 2026-02-24
### Added
- Estructura inicial del proyecto SIGMA-RS.
- Gestión de tickets CRUD.
- Sistema de login/logout y panel de administración.
- Filtrado de tickets por estado.

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

---

Formato sugerido para nuevas versiones:

## [vX.Y.Z] - YYYY-MM-DD
### Added
- ...
### Changed
- ...
### Fixed
- ...
### Removed
- ...
