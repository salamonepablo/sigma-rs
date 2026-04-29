from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from apps.tickets.infrastructure.services.access_extractor import (
    AccessExtractor,
    AccessExtractorConfig,
)


def _build_extractor(
    stdout_writer=None,
    stderr_writer=None,
    heartbeat_interval_seconds: float = 30,
) -> AccessExtractor:
    return AccessExtractor(
        config=AccessExtractorConfig(
            script_path=Path("extractor_access.ps1"),
            powershell_path=Path("powershell.exe"),
        ),
        stdout_writer=stdout_writer,
        stderr_writer=stderr_writer,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
    )


def test_run_extractor_uses_utf8_replace_decoding_for_stdout(monkeypatch):
    """No revienta ante bytes legacy porque fuerza decode UTF-8 replace."""

    popen_kwargs = {}

    class DummyStdout:
        def read(self):
            return "[]"

    class DummyProcess:
        returncode = 0

        def __init__(self):
            self.stdout = DummyStdout()
            self.stderr = []

        def wait(self, timeout=None):  # noqa: ARG002
            return 0

    def fake_popen(*args, **kwargs):
        if kwargs.get("encoding") != "utf-8" or kwargs.get("errors") != "replace":
            raise UnicodeDecodeError("utf-8", b"\x96", 0, 1, "invalid start byte")
        popen_kwargs.update(kwargs)
        return DummyProcess()

    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.subprocess.Popen",
        fake_popen,
    )

    extractor = _build_extractor()
    result = extractor._run_extractor(
        ["powershell", "-File", "extractor_access.ps1"], None
    )

    assert result == "[]"
    assert popen_kwargs["text"] is True
    assert popen_kwargs["encoding"] == "utf-8"
    assert popen_kwargs["errors"] == "replace"


def test_extract_passes_unit_value_to_powershell(monkeypatch):
    """Passes -UnitValue argument so extractor can filter in Access query."""

    popen_command = []

    class DummyStdout:
        def read(self):
            return "[]"

    class DummyProcess:
        returncode = 0

        def __init__(self):
            self.stdout = DummyStdout()
            self.stderr = []

        def wait(self, timeout=None):  # noqa: ARG002
            return 0

    def fake_popen(command, **kwargs):
        popen_command.extend(command)
        return DummyProcess()

    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.subprocess.Popen",
        fake_popen,
    )

    monkeypatch.setattr(Path, "exists", lambda _path: True)

    extractor = _build_extractor()
    db_path = Path("baseCCRR.mdb")

    extractor.extract(
        db_path=db_path,
        table="Detenciones",
        unit_field="Coche",
        unit_value="FG001",
        since_date=date(1900, 1, 1),
        progress_every=0,
    )

    assert "-UnitValue" in popen_command
    idx = popen_command.index("-UnitValue")
    assert popen_command[idx + 1] == "FG001"


def test_extract_passes_minimal_columns_flag(monkeypatch):
    """Passes -MinimalColumns to reduce payload for diagnostics scripts."""

    popen_command = []

    class DummyStdout:
        def read(self):
            return "[]"

    class DummyProcess:
        returncode = 0

        def __init__(self):
            self.stdout = DummyStdout()
            self.stderr = []

        def wait(self, timeout=None):  # noqa: ARG002
            return 0

    def fake_popen(command, **kwargs):
        popen_command.extend(command)
        return DummyProcess()

    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.subprocess.Popen",
        fake_popen,
    )
    monkeypatch.setattr(Path, "exists", lambda _path: True)

    extractor = _build_extractor()
    db_path = Path("baseCCRR.mdb")
    extractor.extract(
        db_path=db_path,
        table="Detenciones",
        unit_field="Coche",
        since_date=date(1900, 1, 1),
        minimal_columns=True,
        progress_every=0,
    )

    assert "-MinimalColumns" in popen_command


def test_extract_detenciones_uses_outfile_transport(monkeypatch):
    """For Detenciones, extractor should read JSON from temp file sink."""

    popen_command = []
    temp_path = Path("temp_access_payload.json")

    class DummyStdout:
        def read(self):
            return "[]"

    class DummyProcess:
        returncode = 0

        def __init__(self):
            self.stdout = DummyStdout()
            self.stderr = []

        def wait(self, timeout=None):  # noqa: ARG002
            return 0

    def fake_popen(command, **kwargs):
        popen_command.extend(command)
        return DummyProcess()

    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.subprocess.Popen",
        fake_popen,
    )
    monkeypatch.setattr(Path, "exists", lambda _path: True)
    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.tempfile.mkstemp",
        lambda **_kwargs: (123, str(temp_path)),
    )
    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.os.close",
        lambda _fd: None,
    )

    read_mock = MagicMock(
        return_value='[{"Unidad":"FG001","Fecha_desde":"2024-01-01","Intervencion":"RA"}]'
    )
    unlink_mock = MagicMock()
    monkeypatch.setattr(Path, "read_text", read_mock)
    monkeypatch.setattr(Path, "unlink", unlink_mock)

    extractor = _build_extractor()
    result = extractor.extract(
        db_path=Path("baseCCRR.mdb"),
        table="Detenciones",
        unit_field="Coche",
        since_date=date(1900, 1, 1),
        progress_every=0,
    )

    assert "-OutFile" in popen_command
    assert result and result[0]["Unidad"] == "FG001"
    read_mock.assert_called_once()
    unlink_mock.assert_called_once_with(missing_ok=True)


def test_run_extractor_emits_heartbeat_when_writer_and_long_running(monkeypatch):
    """Emite heartbeat periódico mientras el proceso sigue en ejecución."""

    stdout_messages: list[str] = []

    class DummyStdout:
        def read(self):
            return "[]"

    class DummyProcess:
        returncode = 0

        def __init__(self):
            self.stdout = DummyStdout()
            self.stderr = []
            self._wait_calls = 0

        def wait(self, timeout=None):  # noqa: ARG002
            self._wait_calls += 1
            if self._wait_calls <= 3:
                raise TimeoutError("still running")
            return 0

    class DummyTimeoutExpired(Exception):
        pass

    timeline = iter([0.0, 0.6, 1.1, 1.7, 2.0, 2.4])

    def fake_monotonic():
        return next(timeline)

    def fake_popen(*args, **kwargs):  # noqa: ARG001
        return DummyProcess()

    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.subprocess.Popen",
        fake_popen,
    )
    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.subprocess.TimeoutExpired",
        DummyTimeoutExpired,
    )
    monkeypatch.setattr(
        "apps.tickets.infrastructure.services.access_extractor.time.monotonic",
        fake_monotonic,
    )

    def patched_wait(self, timeout=None):  # noqa: ARG001
        self._wait_calls += 1
        if self._wait_calls <= 3:
            raise DummyTimeoutExpired("cmd", timeout or 0)
        return 0

    monkeypatch.setattr(DummyProcess, "wait", patched_wait)

    extractor = _build_extractor(
        stdout_writer=stdout_messages.append,
        heartbeat_interval_seconds=1,
    )

    result = extractor._run_extractor(
        ["powershell", "-File", "extractor_access.ps1"],
        prefix="[Detenciones]",
    )

    assert result == "[]"
    assert any(
        msg.startswith("[Detenciones] Extractor running... elapsed ")
        for msg in stdout_messages
    )
