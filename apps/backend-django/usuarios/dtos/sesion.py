"""Datos que devuelve el inicio de sesión."""

from dataclasses import dataclass

from usuarios.models import Usuario


@dataclass(frozen=True)
class SesionDTO:
    """Una sesión recién abierta: quién entró y con qué tokens."""

    usuario: Usuario
    token_de_acceso: str
    token_de_refresco: str
