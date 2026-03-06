"""Domain service for resolving email recipients by location."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RecipientConfig:
    """Recipient configuration record."""

    lugar_id: str | None
    unit_type: str
    recipient_type: str
    email: str


@dataclass(frozen=True)
class RecipientResolution:
    """Resolved recipient lists."""

    to: list[str]
    cc: list[str]
    status: str
    reason: str | None


class RecipientResolver:
    """Resolve recipient list with fallback rules."""

    def resolve(
        self,
        lugar_id: str | None,
        unit_type: str,
        recipients: Iterable[RecipientConfig],
    ) -> RecipientResolution:
        """Resolve recipients for a given location and unit type.

        Args:
            lugar_id: Lugar identifier (can be None for unknown).
            unit_type: Unit type identifier.
            recipients: Recipient configuration list.

        Returns:
            RecipientResolution with to/cc lists and status.
        """

        recipients_list = [r for r in recipients if r.unit_type == unit_type]
        by_lugar = [r for r in recipients_list if r.lugar_id == lugar_id]
        if not by_lugar:
            by_lugar = [r for r in recipients_list if r.lugar_id is None]

        if not by_lugar:
            return RecipientResolution(
                to=[],
                cc=[],
                status="missing",
                reason="No recipients configured",
            )

        to_list = [r.email for r in by_lugar if r.recipient_type == "to"]
        cc_list = [r.email for r in by_lugar if r.recipient_type == "cc"]

        return RecipientResolution(
            to=to_list,
            cc=cc_list,
            status="ok",
            reason=None,
        )
