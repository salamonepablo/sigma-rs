from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sigma/", include("apps.tickets.urls", namespace="tickets")),
    path("", include("core.urls")),
]
