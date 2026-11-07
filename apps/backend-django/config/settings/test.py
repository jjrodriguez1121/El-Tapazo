"""Configuración usada al correr las pruebas."""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK  # noqa: F401

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# El correo se guarda en memoria (`django.core.mail.outbox`) en vez de salir.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Sin límite de peticiones: si no, una prueba que pruebe diez contraseñas malas
# se choca con el freno de fuerza bruta en vez de con lo que quería probar.
# Se apagan todos los que declara base.py: cada scope tiene que seguir existiendo
# (DRF falla si una vista pide uno que no está), solo que sin tasa.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": dict.fromkeys(REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]),
}
