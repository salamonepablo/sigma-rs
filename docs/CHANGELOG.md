# CHANGELOG.md

Todas las modificaciones relevantes del proyecto deben registrarse aquí siguiendo el formato semántico.

## [Unreleased]

### Added
- Wagon parity for tickets/news, legacy import, and UI routes.

### Fixed
- Novedades filters: avoid select text overlapping the chevron; let key filter controls grow to use available horizontal space.

## [v1.1.0] - 2026-03-13
### Added
- Backfill migration for rolling stock category.
- Kilometrage records stored in the database with incremental import command.
- Category-specific URLs and navigation for locomotoras/coches motor vs coches remolcados.
- Improved PDF and email output with historical data (RG, Numeral, ABC).

### Changed
- Maintenance entry history labels now adapt to unit type and brand.
- Maintenance entry kilometrage lookups now use the database.
- Novedad fecha_hasta is no longer auto-filled; only closed interventions (with fecha_hasta) count as history.
- PDF now includes logo TA and title by unit type; email body includes full unit details and history.

### Fixed
- Maintenance entry draft now returns history summary to the template.
- History now only considers closed interventions (fecha_hasta not null).

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
