"""Lecturas de negocios."""

from django.db.models import QuerySet

from negocios.excepciones import NegocioNoEncontrado
from negocios.models import Negocio
from negocios.repositorios import negocios as repositorio
from usuarios.repositorios import usuarios as repositorio_de_usuarios


def negocios_de_la_plataforma() -> QuerySet[Negocio]:
    """Todos los negocios. Solo lo mira el staff de la plataforma."""
    return repositorio.todos()


def obtener_negocio(*, negocio_id: int) -> Negocio:
    """Raises: NegocioNoEncontrado."""
    negocio = repositorio.obtener(negocio_id=negocio_id)
    if negocio is None:
        raise NegocioNoEncontrado
    return negocio


def negocio_del_usuario(*, usuario_id: int) -> Negocio:
    """El negocio de quien está preguntando.

    Sale del usuario autenticado y **nunca de la petición**, igual que el
    `negocio_id` del `MixinDelNegocio`: si el cliente manda un id, se ignora.
    Es lo que contesta la pantalla de "mi negocio" del administrador.

    Raises:
        NegocioNoEncontrado: quien pregunta no pertenece a ningún negocio. Le
            pasa al staff de la plataforma, que existe por encima de todos.
    """
    usuario = repositorio_de_usuarios.obtener_por_id(usuario_id=usuario_id)
    if usuario is None or usuario.negocio_id is None:
        raise NegocioNoEncontrado("Tu cuenta no pertenece a ningún negocio.")
    return usuario.negocio
