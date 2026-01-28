from pathlib import Path
import mongoengine

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'aip-django-fastapi-mongodb-secure-key-2026-!@#$%^&*()'
DEBUG = False
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'ninja',
    'mongoengine',

    'auth_app',
    'processing_app',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ REQUIRED

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ninja.compatibility.files.fix_request_files_middleware",
]




CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

ROOT_URLCONF = 'aip_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aip_project.wsgi.application'
ASGI_APPLICATION = 'aip_project.asgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =========================
# STATIC FILES CONFIG
# =========================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# where your project static files live (DEV)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


SECRET_KEY_JWT = 'akin-777'

NINJA_PAGINATION_CLASS = 'ninja.pagination.PageNumberPagination'
NINJA_PAGINATION_PER_PAGE = 100
NINJA_MAX_PER_PAGE_SIZE = 1000
NINJA_PAGINATION_MAX_LIMIT = 10000
NINJA_NUM_PROXIES = 1
NINJA_DEFAULT_THROTTLE_RATES = {}
NINJA_FIX_REQUEST_FILES_METHODS = ['POST', 'PUT', 'PATCH']

mongoengine.connect(
    db='aip_database',
    host='localhost',
    port=27017,
    username='',
    password='',
    authentication_source='admin'
)
