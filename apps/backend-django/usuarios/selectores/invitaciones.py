"""Lecturas de invitaciones."""

from django.db.models import QuerySet

from usuarios.excepciones import InvitacionNoEncontrada, InvitacionVencida, InvitacionYaAceptada
from usuarios.models import Invitacion
from usuarios.repositorios import invitaciones as repositorio
from usuarios.tokens import calcular_hash


def invitaciones_del_negocio(*, negocio_id: int) -> QuerySet[Invitacion]:
    """Invitaciones de un negocio, la más reciente primero.

    Trae de una vez a quien la envió y a quien la aceptó: sin esto, un listado
    de veinte invitaciones son cuarenta consultas de más.
    """
    return repositorio.del_negocio(negocio_id=negocio_id).select_related(
        "creada_por", "aceptada_por"
    )


def obtener_pendiente_por_token(*, token: str) -> Invitacion:
    """La invitación que abre ese enlace, si todavía se puede usar.

    Del token solo se guardó el hash, así que se busca por el hash de lo que
    llega. Comparar hashes también evita que una invitación se filtre en un
    log o en el historial del navegador de quien administra.

    Raises:
        InvitacionNoEncontrada: el token no corresponde a ninguna.
        InvitacionYaAceptada, InvitacionVencida: existe, pero ya no sirve.
    """
    invitacion = repositorio.obtener_por_hash(hash_token=calcular_hash(token))
    if invitacion is None:
        raise InvitacionNoEncontrada
    if invitacion.aceptada_en is not None:
        raise InvitacionYaAceptada
    if invitacion.esta_vencida:
        raise InvitacionVencida
    return invitacion
