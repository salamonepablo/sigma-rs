"""Export Novedades from SQLite to Access .mdb"""

from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings


@dataclass
class ExportConfig:
    """Configuration for Access export."""

    script_path: Path
    baselocs_path: Path | None
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
            str(self._config.baselocs_path),
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
            if returncode == 0 and stdout.strip():
                return ExportResult(
                    success=True,
                    legacy_id=int(stdout.strip()),
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
            "-ExecutionPolicy", "Bypass",
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
        script_path = getattr(settings, "ACCESS_EXTRACTOR_SCRIPT", "")
        db_password = getattr(settings, "ACCESS_DB_PASSWORD", "")

        if not baselocs_path:
            raise ValueError("ACCESS_BASELOCS_PATH is not configured.")
        if not script_path:
            raise ValueError("ACCESS_EXTRACTOR_SCRIPT is not configured.")

        return ExportConfig(
            script_path=Path(script_path),
            baselocs_path=Path(baselocs_path),
            db_password=db_password,
        )

    def export_all_pending(self) -> dict[str, Any]:
        """Export all pending Novedades to Access.

        Returns statistics about the export operation.
        """
        # Import here to avoid circular imports
        from apps.tickets.infrastructure.models.novedad import NovedadModel

        # Get pending novedades (new ones not yet exported)
        pending = NovedadModel.objects.filter(
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

                result = self.export_novedad(
                    unidad=unidad,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    fecha_est=fecha_est,
                    intervencion=intervencion,
                    lugar=lugar,
                    observaciones=Novelty.observaciones,
                )

                if result.success and result.legacy_id:
                    Novelty.is_exported = True
                    Novelty.legacy_id = result.legacy_id
                    Novelty.save(update_fields=["is_exported", "legacy_id"])
                    exported_count += 1
                elif "already exists" in (result.error or "").lower():
                    # Mark as exported even if already exists
                    Novelty.is_exported = True
                    Novelty.save(update_fields=["is_exported"])
                    skipped_count += 1
                else:
                    error_count += 1
                    errors.append(f"{unidad}: {result.error}")
            except Exception as e:
                error_count += 1
                errors.append(f"Error: {str(e)}")

        return {
            "exported": exported_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_details": errors,
        }
