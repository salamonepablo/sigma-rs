import os
from datetime import date, datetime
from pathlib import Path

import django

UNIT = "FG001"


def log(message: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def norm_code(value: object) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    from django.conf import settings

    from apps.tickets.infrastructure.services.access_extractor import (
        AccessExtractor,
        AccessExtractorConfig,
    )
    from apps.tickets.models import MaintenanceUnitModel, NovedadModel

    log(f"Iniciando comparación Access vs SQLite para unidad {UNIT}")

    extractor = AccessExtractor(
        AccessExtractorConfig(
            script_path=Path(
                getattr(settings, "ACCESS_EXTRACTOR_SCRIPT", "extractor_access.ps1")
            ),
            powershell_path=Path(
                getattr(
                    settings,
                    "ACCESS_POWERSHELL_PATH",
                    r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe",
                )
            ),
        ),
        stdout_writer=log,
        stderr_writer=log,
    )

    sources = [
        ("LOCS", Path(getattr(settings, "ACCESS_BASELOCS_PATH", "")), "Locs"),
        ("CCRR", Path(getattr(settings, "ACCESS_BASECCRR_PATH", "")), "Coche"),
    ]

    access_keys: set[tuple[date, str]] = set()
    access_rows_total = 0
    access_rows_fg001 = 0
    access_rows_invalid_key = 0

    for label, db_path, unit_field in sources:
        if not db_path or not db_path.exists():
            log(f"Saltando origen {label}: DB inexistente ({db_path})")
            continue

        log(f"Extrayendo Detenciones desde {label}...")
        rows = extractor.extract(
            db_path=db_path,
            table="Detenciones",
            unit_field=unit_field,
            since_date=date(1900, 1, 1),
            db_password=(getattr(settings, "ACCESS_DB_PASSWORD", "") or None),
            progress_every=5000,
            skip_count=True,
            source_label=label,
        )
        log(f"{label}: filas leídas {len(rows)}")
        access_rows_total += len(rows)

        for row in rows:
            unit = norm_code(row.get("Unidad"))
            if unit != UNIT:
                continue
            access_rows_fg001 += 1
            fecha = parse_date(row.get("Fecha_desde"))
            intervencion = norm_code(row.get("Intervencion"))
            if fecha and intervencion:
                access_keys.add((fecha, intervencion))
            else:
                access_rows_invalid_key += 1

    maintenance_unit = MaintenanceUnitModel.objects.filter(number__iexact=UNIT).first()
    if maintenance_unit:
        qs = NovedadModel.objects.filter(maintenance_unit=maintenance_unit)
        qs = qs | NovedadModel.objects.filter(legacy_unit_code__iexact=UNIT)
    else:
        qs = NovedadModel.objects.filter(legacy_unit_code__iexact=UNIT)

    sqlite_rows = list(qs.select_related("intervencion"))
    sqlite_keys: set[tuple[date, str]] = set()
    for row in sqlite_rows:
        code = norm_code(
            row.intervencion.codigo
            if row.intervencion
            else row.legacy_intervencion_codigo
        )
        if row.fecha_desde and code:
            sqlite_keys.add((row.fecha_desde, code))

    missing_in_sqlite = sorted(access_keys - sqlite_keys)
    extra_in_sqlite = sorted(sqlite_keys - access_keys)

    print("\n=== FG001 COMPARACIÓN ACCESS vs SQLITE ===")
    print("Access rows total leídas:", access_rows_total)
    print("Access rows FG001:", access_rows_fg001)
    print("Access keys válidas FG001 (fecha_desde+interv):", len(access_keys))
    print(
        "Access rows FG001 sin clave completa (fecha/interv vacía):",
        access_rows_invalid_key,
    )
    print("SQLite rows FG001:", len(sqlite_rows))
    print("SQLite keys válidas FG001 (fecha_desde+interv):", len(sqlite_keys))
    print("FALTAN en SQLite:", len(missing_in_sqlite))
    print("EXTRA en SQLite:", len(extra_in_sqlite))

    print("\nPrimeros 20 faltantes:")
    for item in missing_in_sqlite[:20]:
        print("  ", item)

    print("\nPrimeros 20 extra:")
    for item in extra_in_sqlite[:20]:
        print("  ", item)


if __name__ == "__main__":
    main()
