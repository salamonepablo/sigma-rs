"""Export Novedades from SQLite to Access .mdb"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings


@dataclass
class ExportConfig:
    """Configuration for Access export."""

    script_path: Path
    baselocs_path: Path | None
    baseccrr_path: Path | None = None
    db_password: str = ""
    powershell_path: Path | None = None


@dataclass
class ExportResult:
    """Result of a single export operation."""

    success: bool
    legacy_id: int | None = None
    error: str | None = None


class AccessNovedadExporter:
    """Export Novedad records to Access database."""

    def __init__(self, config: ExportConfig | None = None) -> None:
        self._config = config or self._build_default_config()

    def check_exists_in_access(
        self,
        unidad: str,
        fecha_hasta: str | None,
        intervencion: str,
        lugar: str,
    ) -> int | None:
        """Check if a Novedad exists in Access by PK composite.

        Returns the Access ID if exists, None otherwise.
        """
        ps_path = self._get_powershell_path()
        args = [
            str(ps_path),
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._config.script_path),
            "-DbPath",
            str(self._config.baselocs_path),
            "-Operation",
            "CHECK",
            "-Unidad",
            unidad,
            "-Intervencion",
            intervencion,
            "-Lugar",
            lugar,
        ]

        if self._config.db_password:
            args.extend(["-DbPassword", self._config.db_password])

        if fecha_hasta:
            args.extend(["-Fecha_hasta", fecha_hasta])

        try:
            returncode, stdout, stderr = self._run_script(args)
            if returncode == 0 and stdout.strip():
                return int(stdout.strip())
            return None
        except Exception:
            return None

    def export_novedad(
        self,
        unidad: str,
        fecha_desde: str,
        fecha_hasta: str | None,
        fecha_est: str | None,
        intervencion: str,
        lugar: str,
        observaciones: str | None,
        db_path: Path | None = None,
        unit_field: str = "Locs",
    ) -> ExportResult:
        """Export a single Novedad to Access.

        Uses INSERT directly - assumes no duplicates.
        """
        ps_path = self._get_powershell_path()
        args = [
            str(ps_path),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._config.script_path),
            "-DbPath",
            str(db_path or self._config.baselocs_path),
            "-UnitField",
            unit_field,
            "-Operation",
            "INSERT",
            "-Unidad",
            unidad,
            "-Fecha_desde",
            fecha_desde,
            "-Intervencion",
            intervencion,
            "-Lugar",
            lugar,
        ]

        if self._config.db_password:
            args.extend(["-DbPassword", self._config.db_password])

        if fecha_hasta:
            args.extend(["-Fecha_hasta", fecha_hasta])
        if fecha_est:
            args.extend(["-Fecha_est", fecha_est])
        if observaciones:
            args.extend(["-Observaciones", observaciones])

        try:
            returncode, stdout, stderr = self._run_script(args)
            if returncode == 0:
                legacy_id = None
                output = stdout.strip()
                if output:
                    try:
                        legacy_id = int(output)
                    except ValueError:
                        # Keep backward compatibility: successful insert may not return ID.
                        legacy_id = None

                return ExportResult(
                    success=True,
                    legacy_id=legacy_id,
                )

            return ExportResult(
                success=False,
                error=stderr or "Unknown error",
            )
        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
            )

    def update_exported_novedad(
        self,
        legacy_id: int,
        unidad: str,
        fecha_hasta: str | None,
        fecha_est: str | None,
        intervencion: str,
        lugar: str,
        observaciones: str | None,
    ) -> ExportResult:
        """Update an existing Novedad in Access."""
        ps_path = self._get_powershell_path()
        args = [
            str(ps_path),
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._config.script_path),
            "-DbPath",
            str(self._config.baselocs_path),
            "-Operation",
            "UPDATE",
            "-Unidad",
            unidad,
            "-Intervencion",
            intervencion,
            "-Lugar",
            lugar,
        ]

        if self._config.db_password:
            args.extend(["-DbPassword", self._config.db_password])

        if fecha_hasta:
            args.extend(["-Fecha_hasta", fecha_hasta])
        if fecha_est:
            args.extend(["-Fecha_est", fecha_est])
        if observaciones:
            args.extend(["-Observaciones", observaciones])

        try:
            returncode, stdout, stderr = self._run_script(args)
            if returncode == 0:
                return ExportResult(
                    success=True,
                    legacy_id=legacy_id,
                )
            else:
                return ExportResult(
                    success=False,
                    error=stderr or "Unknown error",
                )
        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
            )

    def _get_powershell_path(self) -> Path:
        """Get the PowerShell executable path."""
        if self._config.powershell_path:
            return self._config.powershell_path
        # Default to SysWOW64 (32-bit) for Access ACE/Jet OLEDB
        return Path(r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe")

    def _run_script(self, args: list[str]) -> tuple[int, str, str]:
        """Run PowerShell script and return (returncode, stdout, stderr)."""
        # Use -NoProfile to avoid profile loading issues
        cmd = [
            str(self._get_powershell_path()),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
        ] + args[1:]  # skip ps.exe from args

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout_data = ""
        if process.stdout is not None:
            stdout_data = process.stdout.read()
        process.wait()
        stderr_data = ""
        if process.stderr is not None:
            stderr_data = process.stderr.read()

        return process.returncode, stdout_data, stderr_data

    @staticmethod
    def _build_default_config() -> ExportConfig:
        baselocs_path = getattr(settings, "ACCESS_BASELOCS_PATH", "")
        baseccrr_path = getattr(settings, "ACCESS_BASECCRR_PATH", "")
        script_path = getattr(settings, "ACCESS_EXPORT_SCRIPT", "")
        db_password = getattr(settings, "ACCESS_DB_PASSWORD", "")

        if not baselocs_path:
            raise ValueError("ACCESS_BASELOCS_PATH is not configured.")
        if not script_path:
            raise ValueError("ACCESS_EXPORT_SCRIPT is not configured.")

        script_name = Path(script_path).name.lower()
        if script_name == "extractor_access.ps1":
            raise ValueError(
                "ACCESS_EXPORT_SCRIPT points to extractor_access.ps1; use scripts/export_to_access.ps1."
            )

        return ExportConfig(
            script_path=Path(script_path),
            baselocs_path=Path(baselocs_path),
            baseccrr_path=Path(baseccrr_path) if baseccrr_path else None,
            db_password=db_password,
        )

    def _resolve_export_target(self, novelty: Any) -> tuple[Path | None, str]:
        """Resolve Access DB path and Detenciones unit field for a novelty."""
        maintenance_unit = getattr(novelty, "maintenance_unit", None)
        unit_type = getattr(maintenance_unit, "unit_type", None)
        rolling_category = getattr(maintenance_unit, "rolling_stock_category", None)

        # Compare by persisted values to avoid importing model constants here.
        # In legacy Access, traction stock (locomotoras + coches motor) belongs to baseLocs.
        unit_type_value = str(unit_type).lower() if unit_type else ""
        category_value = str(rolling_category).lower() if rolling_category else ""
        is_traction = unit_type_value in {"locomotora", "coche_motor"} or (
            category_value == "traccion"
        )

        if is_traction:
            return self._config.baselocs_path, "Locs"

        target_db = self._config.baseccrr_path or self._config.baselocs_path
        target_field = "Coche" if self._config.baseccrr_path else "Locs"
        return target_db, target_field

    def export_all_pending(self) -> dict[str, Any]:
        """Export all pending Novedades to Access.

        Returns statistics about the export operation.
        """
        # Import here to avoid circular imports
        from apps.tickets.infrastructure.models.novedad import NovedadModel

        # Get pending novedades (new ones not yet exported)
        pending = NovedadModel.objects.filter(  # type: ignore[attr-defined]
            is_legacy=False,
            is_exported=False,
        )

        exported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        for Novelty in pending:
            try:
                # Get unit identifier
                unidad = (
                    Novelty.maintenance_unit.number
                    if Novelty.maintenance_unit
                    else Novelty.legacy_unit_code
                )

                if not unidad:
                    skipped_count += 1
                    continue

                # Get intervencion and lugar codes
                intervencion = (
                    Novelty.intervencion.codigo
                    if Novelty.intervencion
                    else Novelty.legacy_intervencion_codigo
                )
                lugar = (
                    str(Novelty.lugar.codigo)
                    if Novelty.lugar
                    else str(Novelty.legacy_lugar_codigo)
                    if Novelty.legacy_lugar_codigo
                    else ""
                )

                if not intervencion or not lugar:
                    skipped_count += 1
                    continue

                # Format dates
                fecha_desde = (
                    Novelty.fecha_desde.isoformat() if Novelty.fecha_desde else None
                )
                fecha_hasta = (
                    Novelty.fecha_hasta.isoformat() if Novelty.fecha_hasta else None
                )
                fecha_est = (
                    Novelty.fecha_estimada.isoformat()
                    if Novelty.fecha_estimada
                    else None
                )

                if not fecha_desde:
                    skipped_count += 1
                    continue

                db_path, unit_field = self._resolve_export_target(Novelty)
                db_name = db_path.name if db_path else "<none>"

                result = self.export_novedad(
                    unidad=unidad,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    fecha_est=fecha_est,
                    intervencion=intervencion,
                    lugar=lugar,
                    observaciones=Novelty.observaciones,
                    db_path=db_path,
                    unit_field=unit_field,
                )

                if result.success:
                    Novelty.is_exported = True
                    update_fields = ["is_exported"]
                    if result.legacy_id:
                        Novelty.legacy_id = result.legacy_id
                        update_fields.append("legacy_id")
                    Novelty.save(update_fields=update_fields)
                    exported_count += 1
                elif "already exists" in (result.error or "").lower():
                    # Mark as exported even if already exists
                    Novelty.is_exported = True
                    Novelty.save(update_fields=["is_exported"])
                    skipped_count += 1
                else:
                    error_count += 1
                    errors.append(
                        f"db={db_name} unit_field={unit_field} unidad={unidad} "
                        f"intervencion={intervencion} lugar={lugar}: {result.error}"
                    )
            except Exception as e:
                error_count += 1
                errors.append(f"Error: {str(e)}")

        return {
            "exported": exported_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_details": errors,
        }
