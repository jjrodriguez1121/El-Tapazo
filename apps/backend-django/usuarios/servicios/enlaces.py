"""Lectura de los enlaces firmados que se mandan por correo.

Lo usan la recuperación de contraseña y la verificación de correo. Está en un
solo sitio porque es la comprobación de la que depende que un enlace no se
pueda falsificar: duplicarla sería tener dos sitios donde equivocarse.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator

from usuarios.excepciones import EnlaceInvalido
from usuarios.models import Usuario
from usuarios.repositorios import usuarios as repositorio
from usuarios.tokens import decodificar_id


def usuario_del_enlace(*, uid: str, token: str, generador: PasswordResetTokenGenerator) -> Usuario:
    """Devuelve a quién pertenece el enlace, si el enlace es legítimo.

    Raises:
        EnlaceInvalido: el `uid` viene manipulado, el usuario ya no existe o
            el token está vencido, usado o inventado.
    """
    usuario_id = decodificar_id(uid)
    if usuario_id is None:
        raise EnlaceInvalido

    usuario = repositorio.obtener_por_id(usuario_id=usuario_id)
    if usuario is None or not generador.check_token(usuario, token):
        raise EnlaceInvalido
    return usuario
