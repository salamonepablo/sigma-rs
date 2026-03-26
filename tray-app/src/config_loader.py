"""Load tray app configuration from disk or env overrides."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrayConfig:
    """Tray app configuration values."""

    sigma_base_url: str | None
    ingreso_tray_token: str | None
    poll_interval_seconds: int | None
    terminal_id: str | None


def _default_config_path() -> Path:
    appdata = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
    if not appdata:
        return Path("tray-config.json")
    return Path(appdata) / "SigmaRS" / "tray-config.json"


def _ensure_config_directory(config_path: Path) -> None:
    """Ensure the config directory exists."""
    config_path.parent.mkdir(parents=True, exist_ok=True)


def _generate_terminal_id() -> str:
    """Generate a new terminal UUID."""
    return str(uuid.uuid4())


def load_config() -> TrayConfig:
    """Load configuration from disk when available."""

    config_path_value = os.getenv("TRAY_CONFIG_PATH")
    config_path = (
        Path(config_path_value) if config_path_value else _default_config_path()
    )
    if not config_path.exists():
        return TrayConfig(None, None, None, None)

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError("Invalid tray-config.json") from exc

    poll_value = raw.get("poll_interval_seconds")
    poll_interval = int(poll_value) if poll_value is not None else None

    return TrayConfig(
        sigma_base_url=raw.get("sigma_base_url"),
        ingreso_tray_token=raw.get("ingreso_tray_token"),
        poll_interval_seconds=poll_interval,
        terminal_id=raw.get("terminal_id"),
    )


def get_or_create_terminal_id(config_path: Path | None = None) -> str:
    """Get existing terminal_id or create a new one."""

    if config_path is None:
        config_path = _default_config_path()

    # Try to load existing terminal_id
    if config_path.exists():
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            terminal_id = raw.get("terminal_id")
            if terminal_id:
                return terminal_id
        except (json.JSONDecodeError, OSError):
            pass

    # Generate new terminal_id
    terminal_id = _generate_terminal_id()

    # Save it to config
    _ensure_config_directory(config_path)

    # Read existing config or create new
    try:
        raw = (
            json.loads(config_path.read_text(encoding="utf-8"))
            if config_path.exists()
            else {}
        )
    except (json.JSONDecodeError, OSError):
        raw = {}

    raw["terminal_id"] = terminal_id
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    return terminal_id
