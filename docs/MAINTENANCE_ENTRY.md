# Maintenance Entry Workflow

## Overview

The maintenance entry feature lets users create an operational "Ingreso a Mantenimiento" from a Novedad. It suggests the intervention based on the unit, cycle definitions, and legacy kilometrage, generates a PDF checklist, and opens an Outlook draft email to notify recipients by location.

## User Flow

1. Open the Novedad list and click the ⚙️ "Ingreso" action or use the "Ingreso a Mantenimiento" button in Novedad detail.
2. Complete entry date/time, kilometers or period (months), location, intervention (optional), checklist tasks, and observations.
3. Save the entry to generate the PDF and open the Outlook draft.

## Data Model

### `MaintenanceCycleModel`

Defines the maintenance cycles that drive intervention suggestions.

- `rolling_stock_type`: locomotora, coche_remolcado, coche_motor
- `brand`, `model` (optional)
- `intervention_code`, `intervention_name`
- `trigger_type`: km or time
- `trigger_value`, `trigger_unit` (km or month)

### `MaintenanceEntryModel`

Stores a maintenance entry and generated PDF path.

- `novedad`, `maintenance_unit`, `lugar`
- `entry_datetime`, `exit_datetime`
- `trigger_type`, `trigger_value`, `trigger_unit`
- `suggested_intervention_code`, `selected_intervention`
- `checklist_tasks`, `observations`
- `pdf_path`, `created_by`

### `LugarEmailRecipientModel`

Recipient configuration by location and unit type.

- `lugar` (nullable for defaults)
- `unit_type`, `recipient_type` (to/cc)
- `email`

## Suggestion Rules

Suggestion logic is handled by `InterventionSuggestionService`.

- Uses cycle definitions with the same trigger type.
- Picks the highest cycle with `trigger_value <= input` (or the smallest cycle if below).
- Priority lists depend on unit type and brand/model:
  - Locomotora GM: `RG`, `N11` ... `A`
  - Locomotora CKD (CNR): `720K`, `360K`, `R6` ... `EX`
  - Coche Remolcado CNR: `A4` ... `MEN`
  - Coche Remolcado Materfer: `RG`, `RP`, `ABC`, `AB`, `A`
  - Coche Motor Nohab: `RG`, `RP`, `SEM`, `MEN`
- Uses Novedad history to show the last eligible intervention.

## Recipient Resolution

Recipient resolution is handled by `RecipientResolver`.

- First tries exact `lugar_id` + `unit_type`.
- Falls back to default recipients where `lugar` is null.
- If no recipients exist, the UI shows a warning.

## PDF + Outlook Draft

- PDF generated via `MaintenanceEntryPdfGenerator` (ReportLab).
- File path: `generated/maintenance_entries/ingreso_<uuid>.pdf`.
- Outlook draft uses `pywin32` and opens a draft with recipients, subject, body, and attachment.

## Legacy Kilometrage

Kilometrage values are read from legacy TXT exports:

- `context/db-legacy/KilometrajeLocs.txt`
- `context/db-legacy/Kilometraje_CCRR.txt`

`LegacyKilometrageRepository` provides `get_latest_km` and `get_km_at_or_before`.

## Setup

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Apply migrations:
   - `python manage.py migrate`
3. Seed cycles and default recipients (migration `0013` runs automatically).
4. Open the app and use the new “Ingreso” action.

## Known Warnings

- ReportLab emits a deprecation warning on `ast.NameConstant` (Python 3.14). This is upstream and can be ignored for now.

## Follow-ups

- Add UX polish for entry form (dynamic suggestion updates on input changes).
- Allow editing or listing maintenance entries.
- Add a dedicated download link for the generated PDF.
