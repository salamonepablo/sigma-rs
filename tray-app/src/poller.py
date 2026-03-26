"""Polling loop for pending ingreso emails."""

from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from config_loader import get_or_create_terminal_id, load_config
from outlook_sender import OutlookSender
from result_poster import ResultPoster


class IngresoEmailPoller:
    """Poll server for pending ingreso email payloads."""

    def __init__(self, base_url: str, tray_token: str, poll_interval: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._tray_token = tray_token
        self._poll_interval = poll_interval
        self._outlook = OutlookSender()
        self._poster = ResultPoster(self._base_url, self._tray_token)
        self._terminal_id = get_or_create_terminal_id()

    def _get_headers(self) -> dict:
        """Get headers including terminal_id."""
        return {
            "X-TRAY-TOKEN": self._tray_token,
            "X-TERMINAL-ID": self._terminal_id,
        }

    def register_with_server(self) -> None:
        """Register this terminal with the server."""
        import getpass

        try:
            response = requests.post(
                f"{self._base_url}/api/tray/register/",
                json={
                    "terminal_id": self._terminal_id,
                    "windows_username": getpass.getuser(),
                    "hostname": os.getenv("COMPUTERNAME", ""),
                },
                headers={"X-TRAY-TOKEN": self._tray_token},
                timeout=10,
            )
            response.raise_for_status()
            print(f"Terminal {self._terminal_id} registered successfully")
        except requests.RequestException as exc:
            print(f"Failed to register terminal: {exc}")

    def send_heartbeat(self) -> None:
        """Send heartbeat to server to mark terminal as online."""
        try:
            response = requests.post(
                f"{self._base_url}/api/tray/heartbeat/",
                json={"terminal_id": self._terminal_id},
                headers={"X-TRAY-TOKEN": self._tray_token},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Heartbeat failed: {exc}")

    def poll_once(self) -> None:
        response = requests.get(
            f"{self._base_url}/api/ingresos/email/pending/",
            headers=self._get_headers(),
            timeout=10,
        )
        if response.status_code == 204:
            return
        response.raise_for_status()

        payload = response.json()["payload"]
        signature = response.json()["signature"]

        pdf_path = self._download_pdf(payload["pdf_url"], signature)

        try:
            self._outlook.create_draft(
                to_recipients=payload["to_recipients"],
                cc_recipients=payload["cc_recipients"],
                subject=payload["subject"],
                body=payload["body"],
                body_html=payload.get("body_html"),
                attachment_path=str(pdf_path),
            )
            self._poster.post_result(
                dispatch_id=payload["dispatch_id"],
                status="drafted",
                error=None,
                terminal_id=self._terminal_id,
            )
        except Exception as exc:
            self._poster.post_result(
                dispatch_id=payload["dispatch_id"],
                status="failed",
                error=str(exc) or "Outlook error",
                terminal_id=self._terminal_id,
            )

    def _download_pdf(self, pdf_url: str, signature: str) -> Path:
        target = Path(os.getenv("TMP", ".")) / "ingreso_email.pdf"
        response = requests.get(
            pdf_url,
            params={"signature": signature},
            headers=self._get_headers(),
            timeout=15,
        )
        response.raise_for_status()
        target.write_bytes(response.content)
        return target

    def run(self) -> None:
        # Register with server on startup
        self.register_with_server()

        # Send initial heartbeat
        self.send_heartbeat()

        heartbeat_interval = 30  # Send heartbeat every 30 seconds
        last_heartbeat = time.time()

        while True:
            self.poll_once()
            # After processing, poll again immediately in case a new dispatch was created
            # This helps the "active" tray claim new dispatches faster
            self.poll_once()

            # Send heartbeat periodically
            if time.time() - last_heartbeat >= heartbeat_interval:
                self.send_heartbeat()
                last_heartbeat = time.time()

            time.sleep(self._poll_interval)


def main() -> None:
    config = load_config()
    base_url = (
        os.getenv("SIGMA_BASE_URL")
        or config.sigma_base_url
        or "http://localhost:8000/sigma"
    )
    tray_token = os.getenv("INGRESO_TRAY_TOKEN") or config.ingreso_tray_token or ""
    poll_interval_value = (
        os.getenv("POLL_INTERVAL_SECONDS") or config.poll_interval_seconds or "15"
    )
    poll_interval = int(poll_interval_value)
    if not tray_token:
        raise RuntimeError("INGRESO_TRAY_TOKEN is required")

    IngresoEmailPoller(base_url, tray_token, poll_interval).run()


if __name__ == "__main__":
    main()
