from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TicketForm
from .models import Ticket


def login_view(request):
    """Login de usuarios."""
    if request.user.is_authenticated:
        return redirect("ticket_list")

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("ticket_list")
        messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "core/login.html")


def logout_view(request):
    """Cierre de sesión."""
    logout(request)
    return redirect("login")


@login_required
def ticket_list(request):
    """Listado de tickets con filtros básicos."""
    tickets = Ticket.objects.select_related("creado_por").all()

    estado = request.GET.get("estado")
    if estado:
        tickets = tickets.filter(estado=estado)

    return render(request, "core/ticket_list.html", {
        "tickets": tickets,
        "estados": Ticket.Estado.choices,
        "filtro_estado": estado or "",
    })


@login_required
def ticket_create(request):
    """Crear nuevo ticket."""
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()
            messages.success(request, f"Ticket #{ticket.numero} creado.")
            return redirect("ticket_list")
    else:
        form = TicketForm()

    return render(request, "core/ticket_form.html", {
        "form": form,
        "action": "Crear",
    })


@login_required
def ticket_edit(request, pk):
    """Editar ticket existente."""
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == "POST":
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ticket #{ticket.numero} actualizado.")
            return redirect("ticket_list")
    else:
        form = TicketForm(instance=ticket)

    return render(request, "core/ticket_form.html", {
        "form": form,
        "action": "Editar",
        "ticket": ticket,
    })


@login_required
def ticket_delete(request, pk):
    """Eliminar ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == "POST":
        numero = ticket.numero
        ticket.delete()
        messages.success(request, f"Ticket #{numero} eliminado.")
        return redirect("ticket_list")

    return render(request, "core/ticket_confirm_delete.html", {
        "ticket": ticket,
    })
