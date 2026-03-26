"""API endpoints for tray terminal management."""

from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.tickets.infrastructure.services.tray_terminal_repo import (
    TrayTerminalRepository,
)


def _is_tray_authorized(request) -> bool:
    from django.conf import settings

    token = request.headers.get("X-TRAY-TOKEN") or request.META.get("HTTP_X_TRAY_TOKEN")
    expected = settings.INGRESO_TRAY_TOKEN
    return bool(expected) and token == expected


def _require_tray_token(request):
    if not _is_tray_authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=403)
    return None


@csrf_exempt
@require_POST
def tray_register(request):
    """Register a tray terminal with the server."""
    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    terminal_id = data.get("terminal_id")
    windows_username = data.get("windows_username") or ""
    hostname = data.get("hostname") or ""

    if not terminal_id:
        return JsonResponse({"detail": "terminal_id is required"}, status=400)

    # Get client IP for registration
    registration_ip = _get_client_ip(request)

    repo = TrayTerminalRepository()
    terminal = repo.register(
        terminal_id=terminal_id,
        windows_username=windows_username,
        hostname=hostname,
        registration_ip=registration_ip,
    )

    return JsonResponse(
        {
            "status": "ok",
            "terminal_id": str(terminal.terminal_id),
            "is_online": terminal.is_online,
        }
    )


@csrf_exempt
@require_POST
def tray_heartbeat(request):
    """Update terminal heartbeat to mark it as online."""
    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    terminal_id = data.get("terminal_id")

    if not terminal_id:
        return JsonResponse({"detail": "terminal_id is required"}, status=400)

    repo = TrayTerminalRepository()
    terminal = repo.heartbeat(terminal_id=terminal_id)

    if not terminal:
        return JsonResponse({"detail": "Terminal not registered"}, status=404)

    return JsonResponse(
        {
            "status": "ok",
            "terminal_id": str(terminal.terminal_id),
            "is_online": terminal.is_online,
        }
    )


@csrf_exempt
@require_GET
def tray_status(request):
    """Get terminal status."""
    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    terminal_id = request.headers.get("X-TERMINAL-ID") or request.GET.get("terminal_id")

    if not terminal_id:
        return JsonResponse({"detail": "terminal_id is required"}, status=400)

    repo = TrayTerminalRepository()
    terminal = repo.get_status(terminal_id)

    if not terminal:
        return JsonResponse({"detail": "Terminal not registered"}, status=404)

    return JsonResponse(
        {
            "terminal_id": str(terminal.terminal_id),
            "windows_username": terminal.windows_username,
            "hostname": terminal.hostname,
            "is_online": terminal.is_online,
            "last_seen": terminal.last_seen.isoformat() if terminal.last_seen else None,
        }
    )


@csrf_exempt
@require_GET
def tray_list_online(request):
    """List all online terminals (for admin/debugging)."""
    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    repo = TrayTerminalRepository()
    terminals = repo.get_online_terminals()

    return JsonResponse(
        {
            "terminals": [
                {
                    "terminal_id": str(t.terminal_id),
                    "windows_username": t.windows_username,
                    "hostname": t.hostname,
                    "last_seen": t.last_seen.isoformat() if t.last_seen else None,
                }
                for t in terminals
            ]
        }
    )


def _get_client_ip(request) -> str | None:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
