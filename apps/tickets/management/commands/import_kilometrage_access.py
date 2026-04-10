"""Import kilometrage records from Access via PowerShell JSON output."""

from __future__ import annotations

import json
import subprocess
import threading
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Max

from apps.tickets.models import KilometrageRecordModel


class Command(BaseCommand):
    """Import kilometrage data using a 32-bit PowerShell Access extractor."""

    help = "Import kilometrage from Access using PowerShell JSON output"

    DEFAULT_POWERSHELL = getattr(
        settings,
        "ACCESS_POWERSHELL_PATH",
        r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe",
    )
    DEFAULT_SCRIPT = getattr(
        settings, "ACCESS_EXTRACTOR_SCRIPT", "extractor_access.ps1"
    )
    DEFAULT_DB_PATH = getattr(settings, "ACCESS_BASELOCS_PATH", "")

    def add_arguments(self, parser):
        parser.add_argument(
            "--script-path",
            type=str,
            default=self.DEFAULT_SCRIPT,
            help="Path to extractor_access.ps1",
        )
        parser.add_argument(
            "--db-path",
            type=str,
            default=self.DEFAULT_DB_PATH,
            help="Path to Access .mdb file",
        )
        parser.add_argument(
            "--unit-field",
            type=str,
            default="Locs",
            help="Access field that contains the unit code",
        )
        parser.add_argument(
            "--powershell",
            type=str,
            default=self.DEFAULT_POWERSHELL,
            help="Path to 32-bit PowerShell executable",
        )
        parser.add_argument(
            "--since-date",
            type=str,
            default=None,
            help="Override last date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--db-password",
            type=str,
            default=None,
            help="Access database password",
        )
        parser.add_argument(
            "--progress-every",
            type=int,
            default=500,
            help="Log progress every N records (0 disables)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report without writing",
        )

    def handle(self, *args, **options):
        script_path = Path(options["script_path"])
        if not script_path.exists():
            self.stderr.write(f"Script not found: {script_path}")
            return

        db_path = Path(options["db_path"]) if options["db_path"] else None
        if not db_path or not db_path.exists():
            self.stderr.write(f"Access DB not found: {db_path}")
            return

        ultima_fecha = self._resolve_last_date(options["since_date"])
        access_date = ultima_fecha.strftime("%m/%d/%Y")
        self.stdout.write(f"Ultima fecha usada: {access_date}")

        command = [
            options["powershell"],
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            str(db_path),
            "Kilometraje",
            options["unit_field"],
            access_date,
        ]
        if options["db_password"]:
            command.append(options["db_password"])
        command.append(str(options["progress_every"]))

        self.stdout.write("Ejecutando extractor Access...")
        stdout_data = self._run_extractor(command)
        if stdout_data is None:
            return
        if not stdout_data.strip():
            self.stderr.write(
                "No se recibio JSON por stdout. Verifica el extractor y el "
                "acceso al .mdb."
            )
            return

        try:
            payload = self._parse_stdout_json(stdout_data)
        except json.JSONDecodeError as exc:
            self.stderr.write("JSON invalido en stdout.")
            self.stderr.write(str(exc))
            return

        if isinstance(payload, dict):
            records = [payload]
        else:
            records = list(payload or [])

        if not records:
            self.stdout.write("No hay registros para importar.")
            return

        self._import_records(
            records,
            progress_every=options["progress_every"],
            dry_run=options["dry_run"],
        )

    def _resolve_last_date(self, since_date: str | None) -> date:
        if since_date:
            return datetime.strptime(since_date, "%Y-%m-%d").date()

        last = KilometrageRecordModel.objects.aggregate(Max("record_date"))[
            "record_date__max"
        ]
        return last or date(1990, 1, 1)

    def _run_extractor(self, command: list[str]) -> str | None:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        def _stream_stderr():
            assert process.stderr is not None
            for line in process.stderr:
                self.stdout.write(line.rstrip())

        stderr_thread = threading.Thread(target=_stream_stderr)
        stderr_thread.start()

        assert process.stdout is not None
        stdout_data = process.stdout.read()
        process.wait()
        stderr_thread.join()

        if process.returncode != 0:
            self.stderr.write(f"Extractor fallo con codigo {process.returncode}.")
            return None

        return stdout_data

    @staticmethod
    def _parse_stdout_json(stdout_data: str) -> object:
        cleaned = stdout_data.lstrip("\ufeff").lstrip()
        if not cleaned:
            raise json.JSONDecodeError("Empty stdout", stdout_data, 0)
        object_index = cleaned.find("{")
        array_index = cleaned.find("[")
        indices = [idx for idx in (object_index, array_index) if idx != -1]
        if not indices:
            raise json.JSONDecodeError("JSON start not found", cleaned, 0)
        start = min(indices)
        decoder = json.JSONDecoder()
        payload, _ = decoder.raw_decode(cleaned[start:])
        return payload

    def _import_records(
        self,
        records: list[dict],
        progress_every: int,
        dry_run: bool,
    ) -> None:
        total = len(records)
        processed = 0
        inserted = 0
        skipped = 0
        invalid = 0

        for record in records:
            processed += 1
            unit = (record.get("Unidad") or "").strip()
            raw_date = record.get("Fecha")
            raw_km = record.get("Kilometros")

            record_date = self._parse_date(raw_date)
            km_value = self._parse_decimal(raw_km)

            if not unit or record_date is None or km_value is None:
                invalid += 1
                self._log_progress(
                    processed,
                    total,
                    inserted,
                    skipped,
                    invalid,
                    progress_every,
                )
                continue

            if not dry_run:
                _, created = KilometrageRecordModel.objects.get_or_create(
                    unit_number=unit,
                    record_date=record_date,
                    defaults={
                        "km_value": km_value,
                        "source": "access",
                    },
                )
                if created:
                    inserted += 1
                else:
                    skipped += 1

            self._log_progress(
                processed,
                total,
                inserted,
                skipped,
                invalid,
                progress_every,
            )

        self.stdout.write(
            "Sincronizacion completa. Leidos {processed}, insertados "
            "{inserted}, duplicados {skipped}, invalidos {invalid}.".format(
                processed=processed,
                inserted=inserted,
                skipped=skipped,
                invalid=invalid,
            )
        )

    def _log_progress(
        self,
        processed: int,
        total: int,
        inserted: int,
        skipped: int,
        invalid: int,
        progress_every: int,
    ) -> None:
        if progress_every <= 0:
            return
        if processed % progress_every != 0 and processed != total:
            return
        percent = (processed / total) * 100 if total else 0
        self.stdout.write(
            "Progreso: {processed}/{total} ({percent:.1f}%) - "
            "insertados {inserted}, duplicados {skipped}, invalidos {invalid}".format(
                processed=processed,
                total=total,
                percent=percent,
                inserted=inserted,
                skipped=skipped,
                invalid=invalid,
            )
        )

    def _parse_date(self, value: object) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        value_str = str(value).strip()
        if not value_str:
            return None
        try:
            return datetime.fromisoformat(value_str).date()
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value_str, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_decimal(self, value: object) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        value_str = str(value).strip()
        if not value_str:
            return None
        value_str = value_str.replace(".", "").replace(",", ".")
        try:
            return Decimal(value_str)
        except (InvalidOperation, ValueError):
            return None
