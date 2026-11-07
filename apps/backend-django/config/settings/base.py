"""Configuración común a todos los entornos.

Los valores sensibles se leen de variables de entorno (archivo .env).
No poner credenciales reales en este archivo.
"""

from datetime import timedelta
from pathlib import Path

import environ

# apps/backend-django/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173"]),
)

# Lee el .env si existe (en Docker las variables llegan por el entorno).
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# --------------------------------------------------------------------------- #
# Apps
# --------------------------------------------------------------------------- #
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Guarda los refresh anulados al cerrar sesión. Sus tablas empiezan por
    # `token_blacklist_` y, como las de `auth_` y `django_`, no son nuestras.
    "rest_framework_simplejwt.token_blacklist",
]

LOCAL_APPS = [
    "nucleo",
    "negocios",
    "usuarios",
    "clientes",
    "catalogo",
    "inventario",
    "eventos",
    "distribucion",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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

# --------------------------------------------------------------------------- #
# Base de datos
# --------------------------------------------------------------------------- #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="el_tapaso"),
        "USER": env("POSTGRES_USER", default="el_tapaso"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="el_tapaso"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env.int("POSTGRES_PORT", default=5432),
        "CONN_MAX_AGE": env.int("DJANGO_CONN_MAX_AGE", default=60),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Identidad propia: el correo es el nombre de usuario (ver usuarios/models.py).
AUTH_USER_MODEL = "usuarios.Usuario"

# `AllowAllUsers...` deja que la comprobación de la contraseña ocurra incluso si
# el usuario está inactivo o sin verificar. No es un descuido: así el servicio de
# inicio de sesión solo revela el estado de la cuenta DESPUÉS de acertar la
# contraseña, y nadie puede averiguar qué correos existen probando el formulario.
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]

# Vigencia de los enlaces de recuperación de contraseña y de verificación de
# correo. Django lo usa para firmar y comprobar esos tokens.
PASSWORD_RESET_TIMEOUT = env.int("VIGENCIA_ENLACES_HORAS", default=24) * 60 * 60

# Seis caracteres con letras y números, y nada más: es la regla que decidió el
# equipo. El formulario del frontend enseña las mismas tres condiciones antes de
# enviar (`modulos/autenticacion/utilidades/reglasDeContrasena.js`): si cambia
# una, cambia la otra.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
    {"NAME": "usuarios.validadores.contrasenas.ValidadorDeLetrasYNumeros"},
]

# --------------------------------------------------------------------------- #
# Internacionalización
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# --------------------------------------------------------------------------- #
# Archivos estáticos y media
# --------------------------------------------------------------------------- #
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------------------------------- #
# DRF
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    # JWT para el frontend. La de sesión se queda para poder probar los
    # endpoints desde /api/docs/ estando logueado en el admin.
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Todos los errores salen con la misma forma (ver nucleo/excepciones/).
    "EXCEPTION_HANDLER": "nucleo.excepciones.manejador_de_excepciones",
    # Freno a la fuerza bruta en los endpoints públicos. Cada uno declara su
    # `throttle_scope`; lo que no lo declara no se limita.
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {
        "inicio_sesion": env("LIMITE_INICIO_SESION", default="10/min"),
        "correos_salientes": env("LIMITE_CORREOS_SALIENTES", default="5/hour"),
        # Sin freno, cualquiera con un lector de tres dólares puede ir
        # preguntándole al sistema cuánto debe cada persona del bar.
        "punto_de_control": env("LIMITE_PUNTO_DE_CONTROL", default="60/min"),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "El Tapaso API",
    "DESCRIPTION": "API del sistema de inventario El Tapaso.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Varios campos se llaman `tipo` y sus listas de valores no son la misma.
    # Sin estos nombres, el esquema los bautiza `Tipo34fEnum`, que no le dice
    # nada a quien genera el cliente del frontend.
    "ENUM_NAME_OVERRIDES": {
        "TipoDeUbicacion": "inventario.models.TIPOS_DE_UBICACION",
        "TipoDeMovimiento": "inventario.models.TIPOS_DE_MOVIMIENTO",
        "EstadoDeEvento": "eventos.models.ESTADOS_DE_EVENTO",
        "EstadoDeGrupo": "eventos.models.ESTADOS_DE_GRUPO",
        "EstadoDePedidoEvento": "eventos.models.ESTADOS_DE_PEDIDO_EVENTO",
        "EstadoDePulsera": "eventos.models.ESTADOS_DE_PULSERA",
        "EstadoDePedidoDistribucion": "distribucion.models.ESTADOS_DE_PEDIDO_DISTRIBUCION",
        "EstadoDeNegocio": "negocios.models.ESTADOS_DE_NEGOCIO",
    },
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")


SIMPLE_JWT = {
    # Corto a propósito: si roban el access, caduca solo en 15 minutos.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("MINUTOS_TOKEN_ACCESO", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("DIAS_TOKEN_REFRESCO", default=7)),
    # Cada renovación entrega un refresh nuevo y anula el anterior: si alguien
    # copió uno, deja de servir en cuanto la persona legítima lo usa.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": SECRET_KEY,
}

# --------------------------------------------------------------------------- #
# Correo
#
# El proveedor da igual (Brevo, Resend, Gmail…): todos hablan SMTP y todos se
# configuran con estas mismas variables en el .env. Cambiar de proveedor es
# cambiar el .env, no el código.
# --------------------------------------------------------------------------- #
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="El Tapaso <no-responder@el-tapaso.com>")

# --------------------------------------------------------------------------- #
# Enlaces que se mandan por correo
#
# El backend no sirve esas pantallas: las pinta el frontend. Aquí solo se arma
# la URL, así que si el frontend cambia de dominio se cambia esta variable.
# --------------------------------------------------------------------------- #
URL_FRONTEND = env("URL_FRONTEND", default="http://localhost:5173")

# Cuánto dura una invitación antes de vencerse.
VIGENCIA_INVITACION_DIAS = env.int("VIGENCIA_INVITACION_DIAS", default=7)
