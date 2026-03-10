# ADR 0002: Category-Based Routing for Rolling Stock

## Status
Accepted

## Context
Operations require different flows for traction units (locomotoras and
coches motor) versus coches remolcados. Existing URLs and navigation were
unit-type based, which did not map cleanly to operational categories.

## Decision
Add `rolling_stock_category` to `MaintenanceUnitModel` and expose category
specific routes and navigation for tickets and novedades. Category values:
`traccion` (locomotoras + coches motor) and `ccrr` (coches remolcados).

## Consequences
- UI flows are split by operational category without duplicating models.
- List and create views filter by category when present.
- Migration backfills category values for existing units.
