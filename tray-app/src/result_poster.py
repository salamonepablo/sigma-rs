"""Post ingreso email results back to Sigma-RS."""

from __future__ import annotations

import getpass

import requests


class ResultPoster:
    """Send dispatch result updates to the server."""

    def __init__(
        self, base_url: str, tray_token: str, terminal_id: str | None = None
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._tray_token = tray_token
        self._terminal_id = terminal_id

    def post_result(
        self,
        *,
        dispatch_id: str,
        status: str,
        error: str | None,
        terminal_id: str | None = None,
    ) -> None:
        payload = {
            "dispatch_id": dispatch_id,
            "status": status,
            "windows_username": getpass.getuser(),
            "error": error,
            "terminal_id": terminal_id or self._terminal_id,
        }
        response = requests.post(
            f"{self._base_url}/api/ingresos/email/result/",
            json=payload,
            headers={"X-TRAY-TOKEN": self._tray_token},
            timeout=10,
        )
        response.raise_for_status()
