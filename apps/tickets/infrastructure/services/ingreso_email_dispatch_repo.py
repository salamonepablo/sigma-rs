"""Repository for maintenance entry email dispatches."""

from __future__ import annotations

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
        )

    def get_next_pending(self) -> MaintenanceEntryEmailDispatchModel | None:
        """Return the oldest pending dispatch if any."""

        return (
            MaintenanceEntryEmailDispatchModel.objects.filter(
                status=MaintenanceEntryEmailDispatchModel.Status.PENDING
            )
            .order_by("created_at")
            .select_related("entry", "entry__novedad")
            .first()
        )

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
