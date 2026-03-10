# ADR 0001: Store Kilometrage Records in the Database

## Status
Accepted

## Context
Kilometrage values were stored in legacy TXT exports and read at runtime.
This caused slow test runs and made incremental updates cumbersome.
We needed a normalized, queryable storage for kilometrage while keeping
the ability to import periodic updates from legacy files.

## Decision
Create a `KilometrageRecordModel` and migrate legacy TXT data into the
database. Runtime lookups now use `KilometrageRepository` backed by the DB.
Provide a management command (`import_kilometrage`) to perform incremental
imports based on the latest record per unit.

## Consequences
- Runtime kilometrage lookups are faster and consistent with DB data.
- Tests can skip heavy imports with `SKIP_KILOMETRAGE_IMPORT=1`.
- Legacy TXT files are only needed for periodic imports.
