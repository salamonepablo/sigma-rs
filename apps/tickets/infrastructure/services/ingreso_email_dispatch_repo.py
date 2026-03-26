"""Repository for maintenance entry email dispatches."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.tickets.infrastructure.models import MaintenanceEntryEmailDispatchModel


class IngresoEmailDispatchRepository:
    """Persistence adapter for email dispatch records."""

    def create_pending(
        self,
        *,
        entry,
        to_recipients: list[str],
        cc_recipients: list[str],
        subject: str,
        body: str,
        body_html: str | None,
        origin_terminal_id: str | None = None,
    ) -> MaintenanceEntryEmailDispatchModel:
        """Create a pending dispatch record."""

        return MaintenanceEntryEmailDispatchModel.objects.create(
            entry=entry,
            status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
            attempts=0,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            subject=subject,
            body=body,
            body_html=body_html,
            origin_terminal_id=origin_terminal_id,
        )

    def get_next_pending(
        self,
        terminal_id: str | None = None,
    ) -> MaintenanceEntryEmailDispatchModel | None:
        """Return the next pending dispatch for the given terminal.

        If terminal_id is provided, prioritizes dispatches for that terminal.
        Falls back to unassigned dispatches (no origin_terminal_id).
        Falls back to any pending dispatch (backward compatibility).

        Uses atomic claim with select_for_update to prevent race conditions.
        """

        # Release stale CLAIMED dispatches back to PENDING
        self._release_stale_claims()

        # Try to get a dispatch for this terminal first
        dispatch = self._atomic_claim(terminal_id=terminal_id)

        # If no dispatch for this terminal, try unassigned
        if not dispatch and terminal_id:
            dispatch = self._atomic_claim(terminal_id=None)

        # Fallback: any pending dispatch (backward compatibility)
        if not dispatch:
            dispatch = self._atomic_claim(terminal_id=None, allow_any=True)

        return dispatch

    def _release_stale_claims(self) -> int:
        """Release CLAIMED dispatches that have timed out."""
        stale_timeout = timezone.now() - timedelta(minutes=5)
        return MaintenanceEntryEmailDispatchModel.objects.filter(
            status=MaintenanceEntryEmailDispatchModel.Status.CLAIMED,
            claimed_at__lt=stale_timeout,
        ).update(
            status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
            claimed_at=None,
        )

    def _atomic_claim(
        self,
        terminal_id: str | None = None,
        allow_any: bool = False,
    ) -> MaintenanceEntryEmailDispatchModel | None:
        """Atomically claim a pending dispatch using select_for_update."""

        with transaction.atomic():
            # Build query based on terminal routing logic
            if allow_any:
                # Backward compatibility: any pending dispatch
                queryset = MaintenanceEntryEmailDispatchModel.objects.filter(
                    status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
                )
            elif terminal_id:
                # Priority 1: dispatch for this terminal
                queryset = MaintenanceEntryEmailDispatchModel.objects.filter(
                    status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
                    origin_terminal_id=terminal_id,
                )
                if not queryset.exists():
                    # Priority 2: unassigned dispatch (can be claimed by any terminal)
                    queryset = MaintenanceEntryEmailDispatchModel.objects.filter(
                        status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
                        origin_terminal_id__isnull=True,
                    )
            else:
                # No terminal_id: unassigned or any
                queryset = MaintenanceEntryEmailDispatchModel.objects.filter(
                    status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
                )

            # Use select_for_update with skip_locked to avoid race conditions
            dispatch = (
                queryset.select_for_update(skip_locked=True)
                .order_by("created_at")
                .select_related("entry", "entry__novedad")
                .first()
            )

            # Mark as CLAIMED if we found one
            if dispatch:
                dispatch.status = MaintenanceEntryEmailDispatchModel.Status.CLAIMED
                dispatch.claimed_at = timezone.now()
                dispatch.terminal_id = terminal_id or dispatch.terminal_id
                dispatch.save(
                    update_fields=["status", "claimed_at", "terminal_id", "updated_at"]
                )

            return dispatch

    def mark_sent(
        self, dispatch: MaintenanceEntryEmailDispatchModel, windows_username: str
    ) -> MaintenanceEntryEmailDispatchModel:
        """Mark a dispatch as sent."""

        dispatch.status = MaintenanceEntryEmailDispatchModel.Status.SENT
        dispatch.attempts += 1
        dispatch.last_error = None
        dispatch.windows_username = windows_username
        dispatch.sent_at = timezone.now()
        dispatch.save(
            update_fields=[
                "status",
                "attempts",
                "last_error",
                "windows_username",
                "sent_at",
                "updated_at",
            ]
        )
        return dispatch

    def mark_drafted(
        self, dispatch: MaintenanceEntryEmailDispatchModel, windows_username: str
    ) -> MaintenanceEntryEmailDispatchModel:
        """Mark a dispatch as drafted."""

        dispatch.status = MaintenanceEntryEmailDispatchModel.Status.DRAFTED
        dispatch.attempts += 1
        dispatch.last_error = None
        dispatch.windows_username = windows_username
        dispatch.drafted_at = timezone.now()
        dispatch.save(
            update_fields=[
                "status",
                "attempts",
                "last_error",
                "windows_username",
                "drafted_at",
                "updated_at",
            ]
        )
        return dispatch

    def mark_failed(
        self,
        dispatch: MaintenanceEntryEmailDispatchModel,
        error: str,
        windows_username: str,
    ) -> MaintenanceEntryEmailDispatchModel:
        """Mark a dispatch as failed."""

        dispatch.status = MaintenanceEntryEmailDispatchModel.Status.FAILED
        dispatch.attempts += 1
        dispatch.last_error = error
        dispatch.windows_username = windows_username
        dispatch.sent_at = timezone.now()
        dispatch.save(
            update_fields=[
                "status",
                "attempts",
                "last_error",
                "windows_username",
                "sent_at",
                "updated_at",
            ]
        )
        return dispatch

    def get_by_entry(self, entry_id) -> list[MaintenanceEntryEmailDispatchModel]:
        """Get all dispatches for an entry."""
        return list(
            MaintenanceEntryEmailDispatchModel.objects.filter(
                entry_id=entry_id
            ).order_by("-created_at")
        )
