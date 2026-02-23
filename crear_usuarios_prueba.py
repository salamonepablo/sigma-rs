"""
Crear usuarios de prueba para testear acceso concurrente.
Ejecutar: python crear_usuarios_prueba.py
"""
from __future__ import annotations

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

USUARIOS = [
    ("operativo1", "Operativo", "Uno", "test1234"),
    ("operativo2", "Operativo", "Dos", "test1234"),
    ("manten1", "Mantenimiento", "Uno", "test1234"),
    ("manten2", "Mantenimiento", "Dos", "test1234"),
]

for username, first, last, pwd in USUARIOS:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"first_name": first, "last_name": last},
    )
    if created:
        user.set_password(pwd)
        user.save()
        print(f"  Creado: {username} / {pwd}")
    else:
        print(f"  Ya existe: {username}")

print("\nUsuarios listos. Password para todos: test1234")
