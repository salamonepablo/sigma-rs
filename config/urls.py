from __future__ import annotations

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def redirect_to_sigma(request):
    """Redirect root URL to /sigma/."""
    return redirect("tickets:home")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("sigma/", include("apps.tickets.urls", namespace="tickets")),
    path("", redirect_to_sigma, name="root"),
]
