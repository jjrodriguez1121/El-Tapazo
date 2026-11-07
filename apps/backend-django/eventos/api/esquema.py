"""Cómo se documenta en `/api/docs/` la autenticación del punto de control.

Sin esto, `drf-spectacular` no sabe qué es `AutenticacionDeDispositivo` y deja
el endpoint del lector sin decir cómo se autentica — justo el dato que necesita
quien programa el ESP32.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class EsquemaDeAutenticacionDeDispositivo(OpenApiAuthenticationExtension):
    target_class = "eventos.api.autenticacion.AutenticacionDeDispositivo"
    name = "TokenDeDispositivo"

    def get_security_definition(self, auto_schema) -> dict:
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Token propio del lector de puerta: `Dispositivo <token>`.",
        }
