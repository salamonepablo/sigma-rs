"""Background scheduler for automatic Access sync at shift changes."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from apscheduler.schedulers.background import BackgroundScheduler

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


def run_export(trigger: str = "scheduled_export") -> None:
    """Run AccessExportUseCase and persist the result in AccessSyncLogModel."""
    from apps.tickets.application.use_cases.access_export_use_case import (
        AccessExportUseCase,
    )
    from apps.tickets.infrastructure.models.access_sync_log import AccessSyncLogModel

    logger.info("Access export starting (trigger=%s)", trigger)

    try:
        use_case = AccessExportUseCase()
    except ValueError as exc:
        logger.warning("Access export skipped — not configured: %s", exc)
        AccessSyncLogModel.objects.create(
            trigger=trigger,
            status=AccessSyncLogModel.STATUS_SKIPPED,
            error_message=str(exc),
        )
        return

    try:
        result = use_case.execute()
        status = AccessSyncLogModel.STATUS_OK
        error_message = ""

        if result.errors > 0:
            status = AccessSyncLogModel.STATUS_ERROR
            error_message = "; ".join(result.error_details) or (
                f"Export finished with {result.errors} errors"
            )
            logger.error(
                "Access export completed with errors (trigger=%s) exported=%d skipped=%d errors=%d duration=%.1fs",
                trigger,
                result.exported,
                result.skipped,
                result.errors,
                result.duration_seconds,
            )
        elif result.skipped > 0:
            status = AccessSyncLogModel.STATUS_SKIPPED
            error_message = f"Skipped {result.skipped} records"
            logger.warning(
                "Access export completed with skips (trigger=%s) exported=%d skipped=%d duration=%.1fs",
                trigger,
                result.exported,
                result.skipped,
                result.duration_seconds,
            )
        else:
            logger.info(
                "Access export OK (trigger=%s) exported=%d skipped=%d duration=%.1fs",
                trigger,
                result.exported,
                result.skipped,
                result.duration_seconds,
            )

        AccessSyncLogModel.objects.create(
            trigger=trigger,
            novedades_inserted=result.exported,
            novedades_duplicates=result.skipped,
            kilometrage_inserted=0,
            duration_seconds=result.duration_seconds,
            status=status,
            error_message=error_message,
        )
    except Exception as exc:
        logger.exception("Access export failed (trigger=%s): %s", trigger, exc)
        AccessSyncLogModel.objects.create(
            trigger=trigger,
            status=AccessSyncLogModel.STATUS_ERROR,
            error_message=str(exc),
        )


def start_scheduler() -> None:
    """Start the background scheduler. Safe to call once per process."""
    global _scheduler

    # Lazy import to avoid blocking if apscheduler is not installed
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("apscheduler not installed — Access sync scheduler disabled")
        return

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

            _scheduler.add_job(
                run_export,
                trigger=CronTrigger(hour=hour, minute=5, timezone=_ART),
                kwargs={"trigger": "scheduled_export"},
                id=f"access_export_{hour:02d}h",
                replace_existing=True,
            )

        _scheduler.start()
        logger.info(
            "Access sync/export scheduler started — sync at %s ART, export at %s ART",
            ", ".join(f"{h:02d}:00" for h in SYNC_HOURS),
            ", ".join(f"{h:02d}:05" for h in SYNC_HOURS),
        )

    # Startup sync/export runs in a daemon thread so it doesn't block startup
    def _run_startup_tasks() -> None:
        run_sync(trigger="startup")
        run_export(trigger="startup_export")

    t = threading.Thread(
        target=_run_startup_tasks,
        name="access-sync-startup",
        daemon=True,
    )
    t.start()
