"""Authentication views for the tickets app."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views import View


class LoginView(View):
    """Handle user login."""

    template_name = "login.html"

    def get(self, request):
        """Render login form or redirect if already authenticated."""
        if request.user.is_authenticated:
            return redirect("tickets:home")
        return render(request, self.template_name)

    def post(self, request):
        """Process login form submission."""
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("tickets:home")
        
        messages.error(request, "Usuario o contraseña incorrectos.")
        return render(request, self.template_name)


class LogoutView(View):
    """Handle user logout."""

    def get(self, request):
        """Log out user and redirect to login page."""
        logout(request)
        return redirect("tickets:login")

    def post(self, request):
        """Log out user and redirect to login page."""
        logout(request)
        return redirect("tickets:login")
