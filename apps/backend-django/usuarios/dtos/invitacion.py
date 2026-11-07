"""Datos que llegan al aceptar una invitación."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AceptacionDeInvitacionDTO:
    """Lo que escribe el trabajador en el formulario del enlace.

    El correo y el rol no vienen de aquí: los puso el administrador al invitar
    y viajan dentro de la invitación. Si vinieran del formulario, cualquiera
    podría darse a sí mismo el rol de administrador.
    """

    token: str
    nombre: str
    apellido: str
    telefono: str
    contrasena: str
