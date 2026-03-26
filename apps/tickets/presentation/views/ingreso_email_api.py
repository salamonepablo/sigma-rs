"""API endpoints for tray-based ingreso email dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.tickets.domain.dto import IngresoEmailPayload
from apps.tickets.domain.services.ingreso_email_signer import IngresoEmailSigner
from apps.tickets.infrastructure.models import MaintenanceEntryEmailDispatchModel
from apps.tickets.infrastructure.services.ingreso_email_dispatch_repo import (
    IngresoEmailDispatchRepository,
)


def _is_tray_authorized(request) -> bool:
    token = request.headers.get("X-TRAY-TOKEN") or request.META.get("HTTP_X_TRAY_TOKEN")
    expected = settings.INGRESO_TRAY_TOKEN
    return bool(expected) and token == expected


def _require_tray_token(request):
    if not _is_tray_authorized(request):
        return JsonResponse({"detail": "Unauthorized"}, status=403)
    return None


def _require_signing_secret():
    secret = settings.INGRESO_EMAIL_SIGNING_SECRET
    if not secret:
        return None, JsonResponse({"detail": "Signing secret missing"}, status=500)
    return secret, None


def _build_payload(
    dispatch: MaintenanceEntryEmailDispatchModel, request
) -> IngresoEmailPayload:
    pdf_base = request.build_absolute_uri(reverse("tickets:ingreso_email_pdf"))
    pdf_url = f"{pdf_base}?{urlencode({'dispatch_id': str(dispatch.id)})}"
    return IngresoEmailPayload(
        dispatch_id=str(dispatch.id),
        entry_id=str(dispatch.entry_id),
        to_recipients=list(dispatch.to_recipients or []),
        cc_recipients=list(dispatch.cc_recipients or []),
        subject=dispatch.subject,
        body=dispatch.body,
        body_html=dispatch.body_html,
        pdf_url=pdf_url,
    )


@csrf_exempt
@require_GET
def ingreso_email_pending(request):
    """Return the next pending ingreso email payload for the requesting terminal."""

    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    secret, secret_error = _require_signing_secret()
    if secret_error:
        return secret_error

    # Get terminal_id from header (optional)
    terminal_id = request.headers.get("X-TERMINAL-ID") or request.GET.get("terminal_id")

    repo = IngresoEmailDispatchRepository()
    dispatch = repo.get_next_pending(terminal_id=terminal_id)
    if not dispatch:
        return HttpResponse(status=204)

    payload = _build_payload(dispatch, request)
    signature = IngresoEmailSigner.sign(payload.as_dict(), secret)
    return JsonResponse({"payload": payload.as_dict(), "signature": signature})


@csrf_exempt
@require_POST
def ingreso_email_result(request):
    """Receive tray app delivery result for an ingreso email."""

    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    dispatch_id = data.get("dispatch_id")
    status = data.get("status")
    windows_username = data.get("windows_username") or ""
    error = data.get("error") or "Unknown error"

    if not dispatch_id or status not in {"sent", "failed", "drafted"}:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    dispatch = get_object_or_404(MaintenanceEntryEmailDispatchModel, pk=dispatch_id)
    repo = IngresoEmailDispatchRepository()
    if status == "sent":
        repo.mark_sent(dispatch, windows_username)
    elif status == "drafted":
        repo.mark_drafted(dispatch, windows_username)
    else:
        repo.mark_failed(dispatch, error, windows_username)

    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_GET
def ingreso_email_pdf(request):
    """Serve the ingreso PDF for a signed dispatch payload."""

    auth_error = _require_tray_token(request)
    if auth_error:
        return auth_error

    secret, secret_error = _require_signing_secret()
    if secret_error:
        return secret_error

    dispatch_id = request.GET.get("dispatch_id")
    signature = request.GET.get("signature")
    if not dispatch_id or not signature:
        return JsonResponse({"detail": "Missing parameters"}, status=400)

    dispatch = get_object_or_404(MaintenanceEntryEmailDispatchModel, pk=dispatch_id)
    payload = _build_payload(dispatch, request)
    if not IngresoEmailSigner.verify(payload.as_dict(), signature, secret):
        return JsonResponse({"detail": "Invalid signature"}, status=403)

    pdf_path = Path(dispatch.entry.pdf_path or "")
    if not pdf_path.exists():
        return JsonResponse({"detail": "PDF not found"}, status=404)

    return FileResponse(
        pdf_path.open("rb"),
        as_attachment=True,
        filename=pdf_path.name,
    )
