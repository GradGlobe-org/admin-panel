import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Load .env
load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
IS_PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_DRIVE_FOLDER_ID_PUBLIC = os.getenv("GOOGLE_DRIVE_FOLDER_ID_PUBLIC")
GOOGLE_DRIVE_FOLDER_ID_PRIVATE = os.getenv("GOOGLE_DRIVE_FOLDER_ID_PRIVATE")
GOOGLE_DRIVE_FOLDER_ID_PROFILE = os.getenv("GOOGLE_DRIVE_FOLDER_ID_PROFILE")
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# WhatsApp secrets
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not IS_PRODUCTION

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
# Application definition

INSTALLED_APPS = [
    "authentication",
    "blogs",
    "seo",
    "tasks",
    "events",
    "jazzmin",
    "corsheaders",
    "university",
    "schema_viewer",
    "scholarship",
    "course",
    "student",
    # "student.apps.StudentConfig",
    "search",
    "exams",
    "core",  # This contains robots.txt for crawlers
    "django_prometheus",
    "nested_admin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    # "authentication.middleware.RateLimitMiddleware",
    # "authentication.middleware.TelegramErrorLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "website.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "website.wsgi.application"


# if IS_PRODUCTION:
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require="supabase.co" in (os.getenv("DATABASE_URL") or ""),
    )
}
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "gradglobe",
#         "USER": "postgres",
#         "PASSWORD": "",
#         "HOST": "localhost",
#         "PORT": "5432",
#     }
# }


if IS_PRODUCTION:
    print("Warning Running with prod settings")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
else:
    print("Safe environment")
    # Optional: explicitly disable them in dev to avoid surprises
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_PRELOAD = False
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",  # just needs to be unique per project
    }
}

# Cors Settings
CORS_ALLOW_HEADERS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Enable Gzip compression
WHITENOISE_USE_FINDERS = True

# Enable WhiteNoise's built-in static file compression (for .gzip, .br files)
WHITENOISE_MANIFEST_STRICT = False
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

JAZZMIN_SETTINGS = {
    "site_title": "Admin",
    "site_header": " Dashboard",
    "site_brand": "GradGlobe Admin ",
    "site_icon": "images/logo/favicon.png",
    "site_logo": "images/logo/favicon.png",
    "login_logo": "images/logo/gradglobe.jpg",
    "welcome_sign": "Welcome to the GradGlobe Admin Panel",
    "copyright": "GradGlobe © 2025",
    "user_avatar": None,
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "show_ui_builder": True
}


SCHEMA_VIEWER = {
    "exclude": {
        "auth": ["User"],
    },
}

PROMETHEUS_LATENCY_BUCKETS = (
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    25.0,
    50.0,
    75.0,
    float("inf"),
)

LOG_LEVEL = "DEBUG" if os.getenv("PRODUCTION", "False").lower() != "true" else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}:{lineno} - {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",  # DEBUG if you want SQL in dev
            "propagate": False,
        },
    },
}
