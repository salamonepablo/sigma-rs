"""DTO for signed ingreso email payloads."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngresoEmailPayload:
    """Payload for tray app email dispatch."""

    dispatch_id: str
    entry_id: str
    to_recipients: list[str]
    cc_recipients: list[str]
    subject: str
    body: str
    body_html: str | None
    pdf_url: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""

        return {
            "dispatch_id": self.dispatch_id,
            "entry_id": self.entry_id,
            "to_recipients": list(self.to_recipients),
            "cc_recipients": list(self.cc_recipients),
            "subject": self.subject,
            "body": self.body,
            "body_html": self.body_html,
            "pdf_url": self.pdf_url,
        }
