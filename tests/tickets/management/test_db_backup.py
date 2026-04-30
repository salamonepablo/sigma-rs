"""Tests for the db_backup management command."""

from __future__ import annotations

import io
import os
import time

import pytest
from django.core.management import call_command
from django.test import override_settings


@pytest.mark.django_db
def test_db_backup_creates_file_and_applies_retention(tmp_path):
    output_dir = tmp_path / "backups"
    output_dir.mkdir(parents=True)

    old_backup = output_dir / "app_20000101_000000.db"
    old_backup.write_text("old", encoding="utf-8")
    old_timestamp = time.time() - (10 * 24 * 60 * 60)
    os.utime(old_backup, (old_timestamp, old_timestamp))

    stdout = io.StringIO()
    call_command(
        "db_backup",
        "--output-dir",
        str(output_dir),
        "--retention-days",
        "7",
        stdout=stdout,
    )

    backups = list(output_dir.glob("app_*.db"))
    assert len(backups) == 1
    assert backups[0].name != old_backup.name

    output = stdout.getvalue()
    assert "Deleted backups: 1" in output
    assert "Backup created:" in output


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "dummy",
        }
    }
)
def test_db_backup_skips_non_sqlite():
    stdout = io.StringIO()

    call_command("db_backup", stdout=stdout)

    assert "Skipping: database engine is not SQLite." in stdout.getvalue()
