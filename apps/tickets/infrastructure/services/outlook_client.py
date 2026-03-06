"""Windows Outlook draft client."""

from __future__ import annotations


class OutlookDraftError(RuntimeError):
    """Raised when Outlook draft creation fails."""


class OutlookDraftClient:
    """Create Outlook draft emails on Windows."""

    def create_draft(
        self,
        to_recipients: list[str],
        cc_recipients: list[str],
        subject: str,
        body: str,
        attachment_path: str | None,
        sender_email: str | None,
    ) -> None:
        """Create and display an Outlook draft message.

        Args:
            to_recipients: Primary recipients.
            cc_recipients: CC recipients.
            subject: Email subject.
            body: Email body.
            attachment_path: File path to attach.
            sender_email: Sender email address.
        """

        try:
            import win32com.client  # type: ignore
        except Exception as exc:  # pragma: no cover - platform specific
            raise OutlookDraftError("Outlook integration not available") from exc

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            message = outlook.CreateItem(0)
            message.To = ";".join(to_recipients)
            message.CC = ";".join(cc_recipients)
            message.Subject = subject
            message.Body = body
            if sender_email:
                message.SentOnBehalfOfName = sender_email
            if attachment_path:
                message.Attachments.Add(attachment_path)
            message.Display()
        except Exception as exc:  # pragma: no cover - COM failure
            raise OutlookDraftError("Failed to create Outlook draft") from exc
