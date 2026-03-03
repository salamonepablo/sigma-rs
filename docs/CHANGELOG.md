# CHANGELOG.md

Todas las modificaciones relevantes del proyecto deben registrarse aquí siguiendo el formato semántico.

## [Unreleased]
### Added
- Login UI redesign with TA and ARS logos.
- New `PersonalModel` (interviniente) and CSV import via `load_initial_data`.
- New `affected_service` field (Yes/No) in ticket form.
- New `resolution` field for tickets when service is affected.
- Ticket list now shows affected service and allows marking as completed.
- GitHub Actions CI workflow (ruff + tests).
- Ruff configuration and pytest tooling.
- CRUD completo de Novedades (formularios, vistas, templates y filtros).
- Accesos desde el home a las novedades según tipo de unidad.
- Listado de novedades limitado a los últimos 60 días con carga incremental y aviso de procesamiento.
- Formularios de novedades con campos unificados (unidad/intervención/lugar) y autocompletado por código.
- Nuevo tipo de intervención `NOV` y mejoras de UX: sin fecha estimada, fecha hasta automática, inputs en mayúsculas, exclusión de AL por defecto e interfaz de filtros compacta.
- Overlay de carga con spinner al solicitar +30 días históricos en el listado de novedades.

### Changed
- Ticket numbers are auto-generated (YYYY-NNNN) and not user-editable.
- Login URL moved to `/sigma/login/` and root redirects to `/sigma/`.
- Supervisor input replaced by `Interviniente` FK selection.
- Navbar updated to `| Material Rodante - Linea Roca |`.
- Project structure documentation updated to reflect `apps/tickets/`.
- Layout de filtros de novedades optimizado para mantener un único renglón y etiquetas abreviadas.

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
