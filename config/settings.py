"""
Configuración Django - Prototipo Material Rodante
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)

# SECURITY WARNING: cambiar en producción
SECRET_KEY = "proto-mr-dev-key-cambiar-en-produccion"

DEBUG = True

# Permite acceso desde cualquier PC de la red
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.tickets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "apps" / "tickets" / "presentation" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# SQLite con WAL mode para mejor concurrencia
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db" / "app.db",
        "OPTIONS": {
            "timeout": 30,
            "init_command": "PRAGMA journal_mode=WAL;",
        },
    }
}

# Asegurar que exista el directorio de la BD
os.makedirs(BASE_DIR / "db", exist_ok=True)
os.makedirs(BASE_DIR / "logs", exist_ok=True)

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/sigma/login/"
LOGIN_REDIRECT_URL = "/sigma/"
LOGOUT_REDIRECT_URL = "/sigma/login/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "ingresos_file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "filename": BASE_DIR / "logs" / "ingresos.log",
            "formatter": "simple",
        },
    },
    "loggers": {
        "apps.tickets.presentation.views.novedad_views": {
            "handlers": ["ingresos_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Tray app integration
INGRESO_TRAY_TOKEN = os.getenv("INGRESO_TRAY_TOKEN", "")
INGRESO_EMAIL_SIGNING_SECRET = os.getenv("INGRESO_EMAIL_SIGNING_SECRET", "")
INGRESO_REQUEST_CACHE_ENABLED = os.getenv(
    "INGRESO_REQUEST_CACHE_ENABLED", ""
).strip().lower() in {"1", "true", "yes", "on"}

LEGACY_DATA_PATH = os.getenv("LEGACY_DATA_PATH", "").strip() or str(
    BASE_DIR / "context" / "db-legacy"
)
# Shared path reference: G:\Material Rodante\IFM\DOCUMENT\db-access

ACCESS_BASELOCS_PATH = os.getenv("ACCESS_BASELOCS_PATH", "").strip()
ACCESS_BASECCRR_PATH = os.getenv("ACCESS_BASECCRR_PATH", "").strip()
ACCESS_DB_PASSWORD = os.getenv("ACCESS_DB_PASSWORD", "").strip()
ACCESS_EXTRACTOR_SCRIPT = os.getenv("ACCESS_EXTRACTOR_SCRIPT", "").strip() or str(
    BASE_DIR / "extractor_access.ps1"
)
ACCESS_EXPORT_SCRIPT = os.getenv("ACCESS_EXPORT_SCRIPT", "").strip() or str(
    BASE_DIR / "scripts" / "export_to_access.ps1"
)
ACCESS_POWERSHELL_PATH = os.getenv("ACCESS_POWERSHELL_PATH", "").strip() or str(
    r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
)

# UM detail fixed averages (km/month)
UM_DETAIL_FIXED_AVG_KM = {
    "GM": 8000,
    "CKD": 7500,
    "CCRR_MATERFER": 7000,
    "CCRR_CNR_APR_NOV": 8500,
    "CCRR_CNR_DEC_MAR": 12500,
}
