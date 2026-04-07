"""Actions for novelty and dispatch management."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from apps.tickets.application.use_cases.maintenance_entry_use_case import (
    MaintenanceEntryUseCase,
)
from apps.tickets.infrastructure.models import (
    MaintenanceEntryEmailDispatchModel,
    MaintenanceEntryModel,
    NovedadModel,
)
from apps.tickets.infrastructure.services.ingreso_email_dispatch_repo import (
    IngresoEmailDispatchRepository,
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


class DeleteIngresoView(View):
    """Delete a maintenance entry (admin only)."""

    def get(self, request, pk):
        if not self._is_admin(request.user):
            messages.error(request, "Acción disponible solo para administradores.")
            return HttpResponseRedirect(self._fallback_url(pk))

        novedad = self._get_novedad(pk)
        if not novedad:
            messages.error(request, "Novedad no encontrada.")
            return HttpResponseRedirect(reverse("tickets:novedad_list"))

        entry = self._get_entry(pk)
        if not entry:
            messages.error(request, "Ingreso no encontrado.")
            return HttpResponseRedirect(self._fallback_url(pk))

        had_sent_dispatch = IngresoEmailDispatchRepository().has_sent_by_entry(entry.id)
        return render(
            request,
            "tickets/ingreso_confirm_delete.html",
            {
                "novedad": novedad,
                "entry": entry,
                "had_sent_dispatch": had_sent_dispatch,
                "confirm_action": reverse(
                    "tickets:novedad_delete_ingreso", kwargs={"pk": pk}
                ),
                "cancel_url": self._fallback_url(pk),
            },
        )

    def post(self, request, pk):
        if not self._is_admin(request.user):
            messages.error(request, "Acción disponible solo para administradores.")
            return HttpResponseRedirect(self._fallback_url(pk))

        novedad = self._get_novedad(pk)
        if not novedad:
            messages.error(request, "Novedad no encontrada.")
            return HttpResponseRedirect(reverse("tickets:novedad_list"))

        entry = self._get_entry(pk)
        if not entry:
            messages.error(request, "Ingreso no encontrado.")
            return HttpResponseRedirect(self._fallback_url(pk))

        confirm_sent = request.POST.get("confirm_sent") == "1"
        had_sent_dispatch = IngresoEmailDispatchRepository().has_sent_by_entry(entry.id)
        if had_sent_dispatch and not confirm_sent:
            return render(
                request,
                "tickets/ingreso_confirm_delete.html",
                {
                    "novedad": novedad,
                    "entry": entry,
                    "had_sent_dispatch": had_sent_dispatch,
                    "confirm_action": reverse(
                        "tickets:novedad_delete_ingreso", kwargs={"pk": pk}
                    ),
                    "cancel_url": self._fallback_url(pk),
                },
            )

        use_case = MaintenanceEntryUseCase()
        try:
            use_case.delete_entry(
                novedad_id=str(pk),
                user=request.user,
                confirm_sent=confirm_sent,
            )
        except PermissionError:
            messages.error(request, "Acción disponible solo para administradores.")
            return HttpResponseRedirect(self._fallback_url(pk))
        except ValueError as exc:
            messages.error(request, exc.args[0] if exc.args else "No se pudo borrar.")
            return HttpResponseRedirect(self._fallback_url(pk))

        messages.success(
            request,
            "Ingreso eliminado. Para revertirlo se necesita restaurar la base de datos.",
        )
        return HttpResponseRedirect(self._fallback_url(pk))

    @staticmethod
    def _get_novedad(pk):
        return NovedadModel.objects.filter(pk=pk).first()

    @staticmethod
    def _get_entry(pk):
        return (
            MaintenanceEntryModel.objects.filter(novedad_id=pk)
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def _is_admin(user) -> bool:
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(user.is_staff or user.is_superuser)

    @staticmethod
    def _fallback_url(pk) -> str:
        return reverse("tickets:novedad_detail", kwargs={"pk": pk})
