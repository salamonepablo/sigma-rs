"""Background scheduler for automatic Access sync at shift changes."""

from __future__ import annotations

import logging
import threading
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_ART = ZoneInfo("America/Argentina/Buenos_Aires")
_scheduler: BackgroundScheduler | None = None
_lock = threading.Lock()

# Shift-change hours (local ART time)
SYNC_HOURS = (6, 14, 22)


def run_sync(trigger: str = "scheduled") -> None:
    """Run AccessSyncUseCase and persist the result in AccessSyncLogModel."""
    from apps.tickets.application.use_cases.access_sync_use_case import (
        AccessSyncUseCase,
    )
    from apps.tickets.infrastructure.models.access_sync_log import AccessSyncLogModel

    logger.info("Access sync starting (trigger=%s)", trigger)

    try:
        use_case = AccessSyncUseCase()
    except ValueError as exc:
        logger.warning("Access sync skipped — not configured: %s", exc)
        AccessSyncLogModel.objects.create(
            trigger=trigger,
            status=AccessSyncLogModel.STATUS_SKIPPED,
            error_message=str(exc),
        )
        return

    try:
        result = use_case.run()
        AccessSyncLogModel.objects.create(
            trigger=trigger,
            novedades_inserted=result.novedades.inserted,
            novedades_duplicates=result.novedades.duplicates,
            kilometrage_inserted=result.kilometrage.inserted,
            duration_seconds=result.duration_seconds,
            status=AccessSyncLogModel.STATUS_OK,
        )
        logger.info(
            "Access sync OK (trigger=%s) novedades=%d km=%d duration=%.1fs",
            trigger,
            result.novedades.inserted,
            result.kilometrage.inserted,
            result.duration_seconds,
        )
    except Exception as exc:
        logger.exception("Access sync failed (trigger=%s): %s", trigger, exc)
        AccessSyncLogModel.objects.create(
            trigger=trigger,
            status=AccessSyncLogModel.STATUS_ERROR,
            error_message=str(exc),
        )


def start_scheduler() -> None:
    """Start the background scheduler. Safe to call once per process."""
    global _scheduler

    with _lock:
        if _scheduler is not None:
            return

        _scheduler = BackgroundScheduler(timezone=_ART)

        for hour in SYNC_HOURS:
            _scheduler.add_job(
                run_sync,
                trigger=CronTrigger(hour=hour, minute=0, timezone=_ART),
                kwargs={"trigger": "scheduled"},
                id=f"access_sync_{hour:02d}h",
                replace_existing=True,
            )

        _scheduler.start()
        logger.info(
            "Access sync scheduler started — jobs at %s ART",
            ", ".join(f"{h:02d}:00" for h in SYNC_HOURS),
        )

    # Startup sync runs in a daemon thread so it doesn't block server startup
    t = threading.Thread(
        target=run_sync,
        kwargs={"trigger": "startup"},
        name="access-sync-startup",
        daemon=True,
    )
    t.start()
