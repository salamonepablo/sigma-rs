"""Access extractor wrapper for PowerShell JSON output."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import time
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
        heartbeat_interval_seconds: float = 30,
    ) -> None:
        self._config = config
        self._stdout_writer = stdout_writer
        self._stderr_writer = stderr_writer or stdout_writer
        self._heartbeat_interval_seconds = max(0.0, float(heartbeat_interval_seconds))

    def extract(
        self,
        db_path: Path,
        table: str,
        unit_field: str,
        since_date: date,
        unit_value: str | None = None,
        minimal_columns: bool = False,
        db_password: str | None = None,
        progress_every: int = 5000,
        skip_count: bool = True,
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
            "-DbPath",
            str(db_path),
            "-Tabla",
            table,
            "-UnitField",
            unit_field,
            "-UnitValue",
            unit_value or "",
            "-SinceDate",
            access_date,
            "-ProgressEvery",
            str(progress_every),
        ]

        json_temp_file = ""
        if table.lower() == "detenciones":
            fd, json_temp_file = tempfile.mkstemp(
                prefix="access_extract_", suffix=".json"
            )
            os.close(fd)
            command.extend(["-OutFile", json_temp_file])
        if db_password:
            command.extend(["-ClaveBD", db_password])
        if skip_count:
            command.append("-SkipCount")
        if minimal_columns:
            command.append("-MinimalColumns")

        prefix = self._build_prefix(source_label, table)
        self._emit_start(
            db_path=db_path,
            table=table,
            progress_every=progress_every,
            prefix=prefix,
        )
        stdout_data = self._run_extractor(command, prefix=prefix)
        if json_temp_file:
            try:
                stdout_data = Path(json_temp_file).read_text(encoding="utf-8")
            finally:
                Path(json_temp_file).unlink(missing_ok=True)
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
            encoding="utf-8",
            errors="replace",
        )

        stdout_chunks: list[str] = []

        def _stream_stdout() -> None:
            if process.stdout is None:
                return
            stdout_chunks.append(process.stdout.read())

        def _stream_stderr() -> None:
            if process.stderr is None:
                return
            for line in process.stderr:
                if self._stderr_writer:
                    message = line.rstrip()
                    if message:
                        self._stderr_writer(self._format_message(message, prefix))

        stdout_thread = threading.Thread(target=_stream_stdout)
        stderr_thread = threading.Thread(target=_stream_stderr)
        stdout_thread.start()
        stderr_thread.start()

        started_at = time.monotonic()
        next_heartbeat_at = started_at + self._heartbeat_interval_seconds
        while True:
            try:
                process.wait(timeout=0.5)
                break
            except subprocess.TimeoutExpired:
                if (
                    self._stdout_writer
                    and self._heartbeat_interval_seconds > 0
                    and time.monotonic() >= next_heartbeat_at
                ):
                    elapsed_seconds = int(time.monotonic() - started_at)
                    self._stdout_writer(
                        self._format_message(
                            f"Extractor running... elapsed {elapsed_seconds}s", prefix
                        )
                    )
                    next_heartbeat_at += self._heartbeat_interval_seconds

        stdout_thread.join()
        stderr_thread.join()
        stdout_data = "".join(stdout_chunks)

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
        cleaned = stdout_data.lstrip("\ufeff")
        if not cleaned or not cleaned.strip():
            return []
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if not lines:
            return []

        # Prefer the last JSON-looking line to avoid noisy non-JSON output.
        json_candidate = ""
        for line in reversed(lines):
            if line.startswith("[") or line.startswith("{"):
                json_candidate = line
                break
        cleaned = json_candidate or cleaned.lstrip()

        object_index = cleaned.find("{")
        array_index = cleaned.find("[")
        indices = [idx for idx in (object_index, array_index) if idx != -1]
        if not indices:
            return []
        start = min(indices)
        decoder = json.JSONDecoder()
        candidate = cleaned[start:]

        # Try direct decode first; if trailing garbage exists, raw_decode still returns
        # payload and end index. Ensure tail is only whitespace.
        payload, end = decoder.raw_decode(candidate)
        if candidate[end:].strip():
            raise json.JSONDecodeError(
                "Unexpected trailing content after JSON payload",
                candidate,
                end,
            )
        return payload
