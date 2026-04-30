"""Tests for the db_integrity_check management command."""

from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import override_settings

from apps.tickets.management.commands.db_integrity_check import Command


@pytest.mark.django_db
def test_db_integrity_check_ok():
    stdout = io.StringIO()

    call_command("db_integrity_check", stdout=stdout)

    assert "SQLite integrity_check: ok" in stdout.getvalue()


@pytest.mark.django_db
def test_db_integrity_check_quick_ok():
    stdout = io.StringIO()

    call_command("db_integrity_check", "--quick", stdout=stdout)

    assert "SQLite quick_check: ok" in stdout.getvalue()


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "dummy",
        }
    }
)
def test_db_integrity_check_skips_non_sqlite():
    stdout = io.StringIO()

    call_command("db_integrity_check", stdout=stdout)

    assert "Skipping: database engine is not SQLite." in stdout.getvalue()


@pytest.mark.django_db
def test_db_integrity_check_raises_on_invalid_result(monkeypatch):
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def execute(self, _query):
            return None

        def fetchall(self):
            return [("database disk image is malformed",)]

    monkeypatch.setattr(connections["default"], "cursor", lambda: FakeCursor())

    with pytest.raises(CommandError, match="SQLite integrity_check failed"):
        Command().handle(quick=False)
