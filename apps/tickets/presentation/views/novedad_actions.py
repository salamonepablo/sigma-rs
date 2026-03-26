"""Actions for novelty and dispatch management."""

from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.tickets.infrastructure.models import (
    MaintenanceEntryEmailDispatchModel,
    NovedadModel,
)


class ResetIngresoView(View):
    """Reset ingreso_generado flag to allow regenerating a failed dispatch."""

    def post(self, request, pk):
        novelty = NovedadModel.objects.filter(pk=pk).first()
        if not novelty:
            from django.contrib import messages

            messages.error(request, "Novedad no encontrada.")
            return HttpResponseRedirect(reverse("tickets:novedad_list"))

        # Reset the flag
        novelty.ingreso_generado = False
        novelty.save(update_fields=["ingreso_generado", "updated_at"])

        # Also reset any failed dispatch to pending so it can be retried
        MaintenanceEntryEmailDispatchModel.objects.filter(
            entry__novedad_id=pk,
        ).update(
            status=MaintenanceEntryEmailDispatchModel.Status.PENDING,
            claimed_at=None,
        )

        from django.contrib import messages

        messages.success(request, "Ingreso reseteado. Ahora podés generar uno nuevo.")
        return HttpResponseRedirect(
            reverse("tickets:novedad_detail", kwargs={"pk": pk})
        )
