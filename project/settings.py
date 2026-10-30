import os
from pathlib import Path
import secrets
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("RESUME_DATA_DIR", str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ResumeBuilder"))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
secret_file = DATA_DIR / "secret.key"
if not os.environ.get("DJANGO_SECRET_KEY") and not secret_file.exists():
    try:
        with secret_file.open("x", encoding="utf-8") as stream:
            stream.write(secrets.token_urlsafe(64))
    except FileExistsError:
        pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or secret_file.read_text(encoding="utf-8")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
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

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "app" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
    }
}

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "app" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_TZ = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
