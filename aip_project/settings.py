from pathlib import Path
import os

# ======================================================
# BASE DIR
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent


# ======================================================
# SECURITY
# ======================================================
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "aip-django-fastapi-secure-key"
)

SECRET_KEY_JWT = os.getenv(
    "SECRET_KEY_JWT",
    "akin-777"
)

DEBUG = True

ALLOWED_HOSTS = ["*"]


# ======================================================
# APPLICATIONS
# ======================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "ninja",

    "auth_app",
    "processing_app",
]


# ======================================================
# MIDDLEWARE
# ======================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================================================
# CORS
# ======================================================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# ======================================================
# URL / ASGI / WSGI
# ======================================================
ROOT_URLCONF = "aip_project.urls"

WSGI_APPLICATION = "aip_project.wsgi.application"
ASGI_APPLICATION = "aip_project.asgi.application"


# ======================================================
# TEMPLATES
# ======================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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


# ======================================================
# DATABASE (NO DATABASE REQUIRED)
# ======================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ======================================================
# INTERNATIONALIZATION
# ======================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ======================================================
# STATIC FILES (RENDER / DOCKER)
# ======================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ======================================================
# DEFAULT AUTO FIELD
# ======================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ======================================================
# DJANGO-NINJA
# ======================================================
NINJA_PAGINATION_CLASS = "ninja.pagination.PageNumberPagination"
NINJA_PAGINATION_PER_PAGE = 100
NINJA_MAX_PER_PAGE_SIZE = 1000
