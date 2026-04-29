"""Tests for tickets app scheduler bootstrap guards."""

from __future__ import annotations

from apps.tickets.apps import _should_start_scheduler


def test_should_not_start_scheduler_for_standalone_script(monkeypatch):
    """Standalone scripts (not manage.py) must not start scheduler."""
    monkeypatch.setattr("apps.tickets.apps.sys.argv", ["fg001.py"])
    monkeypatch.delenv("TICKETS_DISABLE_SCHEDULER", raising=False)

    assert _should_start_scheduler() is False


def test_should_not_start_scheduler_when_env_disables(monkeypatch):
    """Env flag must force scheduler disable."""
    monkeypatch.setattr("apps.tickets.apps.sys.argv", ["manage.py", "runserver"])
    monkeypatch.setenv("TICKETS_DISABLE_SCHEDULER", "1")

    assert _should_start_scheduler() is False
