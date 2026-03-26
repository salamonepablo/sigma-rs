"""Repository for tray terminal registry."""

from __future__ import annotations

from django.utils import timezone

from apps.tickets.infrastructure.models import TrayTerminalModel


class TrayTerminalRepository:
    """Persistence adapter for tray terminal registry."""

    def register(
        self,
        *,
        terminal_id: str,
        windows_username: str | None = None,
        hostname: str | None = None,
        registration_ip: str | None = None,
    ) -> TrayTerminalModel:
        """Register or update a terminal."""
        terminal, created = TrayTerminalModel.objects.update_or_create(
            terminal_id=terminal_id,
            defaults={
                "windows_username": windows_username,
                "hostname": hostname,
                "registration_ip": registration_ip,
                "last_seen": timezone.now(),
                "is_online": True,
            },
        )
        return terminal

    def heartbeat(
        self,
        *,
        terminal_id: str,
    ) -> TrayTerminalModel | None:
        """Update last_seen timestamp and mark as online."""
        try:
            terminal = TrayTerminalModel.objects.get(terminal_id=terminal_id)
            terminal.last_seen = timezone.now()
            terminal.is_online = True
            terminal.save(update_fields=["last_seen", "is_online", "updated_at"])
            return terminal
        except TrayTerminalModel.DoesNotExist:
            return None

    def get_status(self, terminal_id: str) -> TrayTerminalModel | None:
        """Get terminal status."""
        try:
            return TrayTerminalModel.objects.get(terminal_id=terminal_id)
        except TrayTerminalModel.DoesNotExist:
            return None

    def get_online_terminals(self) -> list[TrayTerminalModel]:
        """Get all online terminals."""
        return list(
            TrayTerminalModel.objects.filter(is_online=True).order_by("-last_seen")
        )

    def mark_offline_terminals(self, timeout_minutes: int = 5) -> int:
        """Mark terminals that haven't sent heartbeat as offline."""
        cutoff = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
        return TrayTerminalModel.objects.filter(
            is_online=True,
            last_seen__lt=cutoff,
        ).update(is_online=False)

    def is_terminal_online(self, terminal_id: str) -> bool:
        """Check if a terminal is currently online."""
        try:
            terminal = TrayTerminalModel.objects.get(terminal_id=terminal_id)
            # Consider online if last_seen is within the timeout period
            timeout = timezone.now() - timezone.timedelta(minutes=5)
            return (
                terminal.is_online
                and terminal.last_seen is not None
                and terminal.last_seen >= timeout
            )
        except TrayTerminalModel.DoesNotExist:
            return False

    def delete(self, terminal_id: str) -> bool:
        """Delete a terminal registration."""
        try:
            terminal = TrayTerminalModel.objects.get(terminal_id=terminal_id)
            terminal.delete()
            return True
        except TrayTerminalModel.DoesNotExist:
            return False
