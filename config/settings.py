"""Réglages Sceau. Les secrets viennent de l'environnement (.env), jamais du code."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env(path):
    """Lit un .env minimal (CLE=valeur). Une variable déjà définie garde sa valeur."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env(BASE_DIR / ".env")

DEBUG = os.environ.get("SCEAU_DEBUG") == "1"
SECRET_KEY = os.environ.get("SCEAU_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("SCEAU_SECRET_KEY est absente : voir le fichier .env.")
ALLOWED_HOSTS = [h for h in os.environ.get("SCEAU_ALLOWED_HOSTS", "").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "vault",
    "certificates",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/connexion"
LOGIN_REDIRECT_URL = "/coffre"
LOGOUT_REDIRECT_URL = "/connexion"

# --- Uploads : jamais en mémoire, toujours en fichier temporaire, taille limitée
SCEAU_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.TemporaryFileUploadHandler"]
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024

# --- Sessions et cookies
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000

# --- Clé de signature des certificats (hors base de données, hors dépôt Git)
SCEAU_KEY_ID = os.environ.get("SCEAU_KEY_ID", "sceau-2026-1")
SCEAU_PRIVATE_KEY_PATH = Path(os.environ.get(
    "SCEAU_PRIVATE_KEY_PATH", BASE_DIR / "keys" / "sceau-private.pem"))
SCEAU_PUBLIC_KEY_PATH = Path(os.environ.get(
    "SCEAU_PUBLIC_KEY_PATH", BASE_DIR / "keys" / "sceau-public.pem"))
