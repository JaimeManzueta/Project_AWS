from pathlib import Path
import os

# --- Paths ---
# BASE_DIR points to the root of your Django project (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core Settings ---
# Secret key used for cryptographic signing (unsafe for production!)
SECRET_KEY = "dev-only-unsafe-key-change-me"

# Debug mode enabled for development and classroom demos
DEBUG = True

# --- Utility Function ---
def _split_csv(env_value: str):
    """
    Converts a comma-separated string like 'a,b,c' into a list ['a', 'b', 'c'],
    stripping whitespace and ignoring empty entries.
    """
    if not env_value:
        return []
    return [x.strip() for x in env_value.split(",") if x.strip()]

# --- Host Configuration ---
# Allowed hosts for serving the app. In production, set DJANGO_ALLOWED_HOSTS env variable.
# For demos, default to '*' to avoid DisallowedHost errors.
_env_hosts = _split_csv(os.getenv("DJANGO_ALLOWED_HOSTS", ""))
ALLOWED_HOSTS = _env_hosts or ["*"]

# --- CSRF Trusted Origins ---
# Builds a list of trusted origins for CSRF protection based on ALLOWED_HOSTS.
# Skips wildcard hosts and ports.
def _csrf_from_hosts(hosts):
    out = []
    for h in hosts:
        if not h or h == "*" or ":" in h:
            continue
        out.append(f"http://{h}")
        out.append(f"https://{h}")
    return out

CSRF_TRUSTED_ORIGINS = _csrf_from_hosts(ALLOWED_HOSTS)

# --- Installed Apps ---
# Core Django apps plus your custom app (photoapp)
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "photoapp",  # your image processing app
]

# --- Middleware Stack ---
# Middleware components that process requests/responses
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- URL and WSGI Configuration ---
# Root URL configuration and WSGI entrypoint
ROOT_URLCONF = "imageapp.urls"
WSGI_APPLICATION = "imageapp.wsgi.application"

# --- Templates ---
# Required for Django admin and any template rendering
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # No custom template directories used in this demo
        "APP_DIRS": True,  # Enables template discovery in installed apps
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database Configuration ---
# Using SQLite for simplicity and portability
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Password Validation ---
# Default validators to enforce password strength
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization and Timezone ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True  # Enable Django's translation system
USE_TZ = True    # Use timezone-aware datetimes

# --- Static and Media Files ---
# Static files (CSS, JS, etc.)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # Where collectstatic will store files

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Primary Key Field Type ---
# Default type for auto-generated primary keys
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Logging ---
# Logs to both console and a file in the user's home directory
LOG_FILE = os.path.expanduser("~/django.log")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

# --- AWS S3 Configuration ---
# These are used if your views interact with S3 via boto3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "myclass1-bucket")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-2"))

# --- Reverse Proxy SSL Header ---
# Uncomment if you're behind a proxy that handles HTTPS
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")