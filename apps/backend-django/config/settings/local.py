"""Configuración para desarrollo local (Docker Compose)."""

from .base import *  # noqa: F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Por defecto el correo se imprime en los logs del contenedor (`./dev.sh logs
# backend`): sale el enlace completo y se pueden probar la invitación, la
# recuperación y la verificación sin contratar nada.
#
# Para probar el envío de verdad, en el .env:
#   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#   EMAIL_HOST=...  EMAIL_HOST_USER=...  EMAIL_HOST_PASSWORD=...
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# En desarrollo se aceptan todos los orígenes para no pelear con CORS.
CORS_ALLOW_ALL_ORIGINS = True
