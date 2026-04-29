import argparse
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import django

DEFAULT_UNIT = "FG001"
DEFAULT_SINCE_DATE = date(1900, 1, 1)


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validador general Access vs SQLite para Detenciones. "
            "Permite comparar una o varias unidades, o todas las unidades disponibles."
        )
    )
    parser.add_argument(
        "--unit",
        action="append",
        dest="units",
        help=(
            "Código de unidad a validar (ej: FG001). Puede repetirse múltiples veces."
        ),
    )
    parser.add_argument(
        "--all-units",
        action="store_true",
        help="Validar todas las unidades encontradas en Access (según --source).",
    )
    parser.add_argument(
        "--source",
        choices=["locs", "ccrr", "both"],
        default="both",
        help="Origen Access a usar: locs, ccrr o both (default: both).",
    )
    parser.add_argument(
        "--since-date",
        default=DEFAULT_SINCE_DATE.isoformat(),
        help="Fecha mínima (YYYY-MM-DD) para extraer desde Access (default: 1900-01-01).",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=5000,
        help="Heartbeat de progreso del extractor cada N filas (default: 5000).",
    )
    parser.add_argument(
        "--with-count",
        action="store_true",
        help=(
            "Solicita conteo previo de filas al extractor (más lento). "
            "Por defecto se usa skip_count=True."
        ),
    )
    parser.add_argument(
        "--limit-missing",
        type=int,
        default=20,
        help="Cantidad máxima de faltantes a imprimir por unidad (default: 20).",
    )
    parser.add_argument(
        "--limit-extra",
        type=int,
        default=20,
        help="Cantidad máxima de extras a imprimir por unidad (default: 20).",
    )
    return parser.parse_args()


def parse_since_date(raw_value: str) -> date:
    parsed = parse_date(raw_value)
    if not parsed:
        msg = (
            f"Fecha inválida para --since-date: {raw_value!r}. Usá formato YYYY-MM-DD."
        )
        raise SystemExit(msg)
    return parsed


def source_definitions(
    settings: object, selected_source: str
) -> list[tuple[str, Path, str]]:
    all_sources = [
        ("LOCS", Path(getattr(settings, "ACCESS_BASELOCS_PATH", "")), "Locs"),
        ("CCRR", Path(getattr(settings, "ACCESS_BASECCRR_PATH", "")), "Coche"),
    ]

    if selected_source == "locs":
        return [all_sources[0]]
    if selected_source == "ccrr":
        return [all_sources[1]]
    return all_sources


def resolve_units(args: argparse.Namespace, access_units: set[str]) -> list[str]:
    if args.all_units:
        return sorted(access_units)
    if args.units:
        return sorted({unit for unit in (norm_code(u) for u in args.units) if unit})
    return [DEFAULT_UNIT]


def print_unit_block(
    unit: str,
    access_rows: int,
    access_keys: set[tuple[date, str]],
    access_invalid_keys: int,
    sqlite_rows: int,
    sqlite_keys: set[tuple[date, str]],
    missing_in_sqlite: list[tuple[date, str]],
    extra_in_sqlite: list[tuple[date, str]],
    limit_missing: int,
    limit_extra: int,
) -> None:
    print(f"\n=== UNIDAD {unit} ===")
    print("Access rows:", access_rows)
    print("Access keys válidas (fecha_desde+interv):", len(access_keys))
    print("Access rows sin clave completa (fecha/interv vacía):", access_invalid_keys)
    print("SQLite rows:", sqlite_rows)
    print("SQLite keys válidas (fecha_desde+interv):", len(sqlite_keys))
    print("FALTAN en SQLite:", len(missing_in_sqlite))
    print("EXTRA en SQLite:", len(extra_in_sqlite))

    print(f"\nPrimeros {limit_missing} faltantes:")
    for item in missing_in_sqlite[:limit_missing]:
        print("  ", item)

    print(f"\nPrimeros {limit_extra} extra:")
    for item in extra_in_sqlite[:limit_extra]:
        print("  ", item)


def main() -> None:
    args = parse_args()
    since_date = parse_since_date(args.since_date)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    from django.conf import settings

    from apps.tickets.infrastructure.services.access_extractor import (
        AccessExtractor,
        AccessExtractorConfig,
    )
    from apps.tickets.models import MaintenanceUnitModel, NovedadModel

    log("Iniciando comparación Access vs SQLite")
    log(
        "Parámetros: "
        f"source={args.source}, since_date={since_date.isoformat()}, "
        f"progress_every={args.progress_every}, with_count={args.with_count}, "
        f"all_units={args.all_units}, units={args.units or [DEFAULT_UNIT]}"
    )

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

    sources = source_definitions(settings, args.source)

    access_rows_total = 0
    access_rows_by_unit: dict[str, int] = defaultdict(int)
    access_invalid_rows_by_unit: dict[str, int] = defaultdict(int)
    access_keys_by_unit: dict[str, set[tuple[date, str]]] = defaultdict(set)

    access_units: set[str] = set()
    if args.all_units:
        for label, db_path, unit_field in sources:
            if not db_path or not db_path.exists():
                log(f"Saltando origen {label}: DB inexistente ({db_path})")
                continue

            log(f"Descubriendo unidades en {label}...")
            rows = extractor.extract(
                db_path=db_path,
                table="Detenciones",
                unit_field=unit_field,
                since_date=since_date,
                db_password=(getattr(settings, "ACCESS_DB_PASSWORD", "") or None),
                progress_every=args.progress_every,
                skip_count=not args.with_count,
                source_label=label,
            )
            for row in rows:
                unit = norm_code(row.get("Unidad"))
                if unit:
                    access_units.add(unit)

    units_to_compare = resolve_units(args, access_units)
    if args.all_units and not units_to_compare:
        log("No se encontraron unidades en Access para el source seleccionado.")

    for unit in units_to_compare:
        for label, db_path, unit_field in sources:
            if not db_path or not db_path.exists():
                continue

            log(f"Extrayendo Detenciones desde {label} para unidad {unit}...")
            rows = extractor.extract(
                db_path=db_path,
                table="Detenciones",
                unit_field=unit_field,
                unit_value=unit,
                since_date=since_date,
                minimal_columns=True,
                db_password=(getattr(settings, "ACCESS_DB_PASSWORD", "") or None),
                progress_every=args.progress_every,
                skip_count=not args.with_count,
                source_label=label,
            )
            log(f"{label} {unit}: filas leídas {len(rows)}")
            access_rows_total += len(rows)

            for row in rows:
                row_unit = norm_code(row.get("Unidad"))
                if row_unit != unit:
                    continue
                access_rows_by_unit[unit] += 1
                fecha = parse_date(row.get("Fecha_desde"))
                intervencion = norm_code(row.get("Intervencion"))
                if fecha and intervencion:
                    access_keys_by_unit[unit].add((fecha, intervencion))
                else:
                    access_invalid_rows_by_unit[unit] += 1

    print("\n=== RESUMEN GLOBAL ACCESS ===")
    print("Access rows total leídas:", access_rows_total)
    print("Unidades detectadas en Access:", len(access_units))
    print("Unidades a comparar:", len(units_to_compare))

    global_missing = 0
    global_extra = 0
    global_access_keys = 0
    global_sqlite_keys = 0
    global_access_rows = 0
    global_sqlite_rows = 0

    for unit in units_to_compare:
        maintenance_unit = MaintenanceUnitModel.objects.filter(
            number__iexact=unit
        ).first()
        if maintenance_unit:
            qs = NovedadModel.objects.filter(maintenance_unit=maintenance_unit)
            qs = qs | NovedadModel.objects.filter(legacy_unit_code__iexact=unit)
        else:
            qs = NovedadModel.objects.filter(legacy_unit_code__iexact=unit)

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

        access_keys = access_keys_by_unit.get(unit, set())
        missing_in_sqlite = sorted(access_keys - sqlite_keys)
        extra_in_sqlite = sorted(sqlite_keys - access_keys)

        global_missing += len(missing_in_sqlite)
        global_extra += len(extra_in_sqlite)
        global_access_keys += len(access_keys)
        global_sqlite_keys += len(sqlite_keys)
        global_access_rows += access_rows_by_unit.get(unit, 0)
        global_sqlite_rows += len(sqlite_rows)

        print_unit_block(
            unit=unit,
            access_rows=access_rows_by_unit.get(unit, 0),
            access_keys=access_keys,
            access_invalid_keys=access_invalid_rows_by_unit.get(unit, 0),
            sqlite_rows=len(sqlite_rows),
            sqlite_keys=sqlite_keys,
            missing_in_sqlite=missing_in_sqlite,
            extra_in_sqlite=extra_in_sqlite,
            limit_missing=args.limit_missing,
            limit_extra=args.limit_extra,
        )

    print("\n=== RESUMEN GLOBAL COMPARACIÓN ===")
    print("Access rows (unidades comparadas):", global_access_rows)
    print("Access keys válidas (unidades comparadas):", global_access_keys)
    print("SQLite rows (unidades comparadas):", global_sqlite_rows)
    print("SQLite keys válidas (unidades comparadas):", global_sqlite_keys)
    print("FALTAN totales en SQLite:", global_missing)
    print("EXTRA totales en SQLite:", global_extra)


if __name__ == "__main__":
    main()
