"""Access extractor wrapper for PowerShell JSON output."""

from __future__ import annotations

import json
import subprocess
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class AccessExtractorConfig:
    """Configuration for the Access extractor."""

    script_path: Path
    powershell_path: Path


class AccessExtractor:
    """Run the PowerShell extractor for Access data."""

    def __init__(
        self,
        config: AccessExtractorConfig,
        stdout_writer=None,
        stderr_writer=None,
    ) -> None:
        self._config = config
        self._stdout_writer = stdout_writer
        self._stderr_writer = stderr_writer or stdout_writer

    def extract(
        self,
        db_path: Path,
        table: str,
        unit_field: str,
        since_date: date,
        db_password: str | None = None,
        progress_every: int = 500,
        source_label: str | None = None,
    ) -> list[dict]:
        if not self._config.script_path.exists():
            raise FileNotFoundError(f"Script not found: {self._config.script_path}")
        if not self._config.powershell_path.exists():
            raise FileNotFoundError(
                f"PowerShell not found: {self._config.powershell_path}"
            )
        if not db_path.exists():
            raise FileNotFoundError(f"Access DB not found: {db_path}")

        access_date = since_date.strftime("%m/%d/%Y")
        command = [
            str(self._config.powershell_path),
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._config.script_path),
            str(db_path),
            table,
            unit_field,
            access_date,
        ]
        if db_password:
            command.append(db_password)
        command.append(str(progress_every))

        prefix = self._build_prefix(source_label, table)
        self._emit_start(
            db_path=db_path,
            table=table,
            progress_every=progress_every,
            prefix=prefix,
        )
        stdout_data = self._run_extractor(command, prefix=prefix)
        self._emit_info("Conexion OK", prefix=prefix)
        if not stdout_data or not stdout_data.strip():
            return []

        payload = self._parse_stdout_json(stdout_data)
        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, list):
            return payload
        return []

    def _run_extractor(self, command: list[str], prefix: str | None) -> str:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        def _stream_stderr() -> None:
            if process.stderr is None:
                return
            for line in process.stderr:
                if self._stderr_writer:
                    message = line.rstrip()
                    if message:
                        self._stderr_writer(self._format_message(message, prefix))

        stderr_thread = threading.Thread(target=_stream_stderr)
        stderr_thread.start()

        stdout_data = ""
        if process.stdout is not None:
            stdout_data = process.stdout.read()
        process.wait()
        stderr_thread.join()

        if process.returncode != 0:
            raise RuntimeError(
                "Extractor fallo con codigo {code}.".format(code=process.returncode)
            )

        return stdout_data

    def _emit_start(
        self,
        db_path: Path,
        table: str,
        progress_every: int,
        prefix: str | None,
    ) -> None:
        if not self._stdout_writer:
            return
        progress_label = (
            f"progreso cada {progress_every}"
            if progress_every and progress_every > 0
            else "progreso deshabilitado"
        )
        message = f"Inicio DB {db_path.name} tabla {table} ({progress_label})"
        self._stdout_writer(self._format_message(message, prefix))

    def _emit_info(self, message: str, prefix: str | None) -> None:
        if not self._stdout_writer:
            return
        self._stdout_writer(self._format_message(message, prefix))

    @staticmethod
    def _build_prefix(source_label: str | None, table: str) -> str | None:
        if source_label:
            return f"[{source_label} {table}]"
        if table:
            return f"[{table}]"
        return None

    @staticmethod
    def _format_message(message: str, prefix: str | None) -> str:
        if prefix:
            return f"{prefix} {message}"
        return message

    @staticmethod
    def _parse_stdout_json(stdout_data: str) -> object:
        cleaned = stdout_data.lstrip("\ufeff").lstrip()
        if not cleaned:
            return []
        object_index = cleaned.find("{")
        array_index = cleaned.find("[")
        indices = [idx for idx in (object_index, array_index) if idx != -1]
        if not indices:
            return []
        start = min(indices)
        decoder = json.JSONDecoder()
        payload, _ = decoder.raw_decode(cleaned[start:])
        return payload
