"""Outlook COM email sender for tray app."""

from __future__ import annotations

import contextlib


class OutlookSender:
    """Create Outlook drafts via local Outlook profile using COM."""

    def create_draft(
        self,
        *,
        to_recipients: list[str],
        cc_recipients: list[str],
        subject: str,
        body: str,
        body_html: str | None,
        attachment_path: str | None,
    ) -> None:
        try:
            import pythoncom  # type: ignore
            import win32com.client  # type: ignore
        except Exception as exc:  # pragma: no cover - platform specific
            raise RuntimeError("Outlook integration not available") from exc

        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            message = outlook.CreateItem(0)
            message.To = ";".join(to_recipients)
            message.CC = ";".join(cc_recipients)
            message.Subject = subject
            message.Body = body
            if body_html:
                message.HTMLBody = body_html
            if attachment_path:
                message.Attachments.Add(attachment_path)
            message.Display()
        except Exception as exc:  # pragma: no cover - COM failure
            message = str(exc) or "Failed to draft Outlook email"
            raise RuntimeError(message) from exc
        finally:
            with contextlib.suppress(Exception):
                pythoncom.CoUninitialize()
