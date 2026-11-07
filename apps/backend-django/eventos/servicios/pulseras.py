"""El inventario de chips y los lectores de la puerta."""

from django.db import transaction

from eventos.excepciones import PulseraNoDisponible, UidDuplicado
from eventos.models import DispositivoNfc, PulseraNfc
from eventos.repositorios import pulseras as repositorio
from nucleo.excepciones import NoEncontradoEnEsteNegocio
from usuarios.tokens import generar_token_de_invitacion


def registrar_pulsera(*, negocio_id: int, uid_tag: str) -> PulseraNfc:
    """Da de alta un chip por el número de serie que trae de fábrica.

    En el chip no se escribe nada: lo único que aporta es su UID, y ese número
    lleva a la cuenta, que lleva al cliente. Por eso una pulsera perdida no
    filtra los datos de nadie.

    Raises:
        UidDuplicado.
    """
    uid_tag = uid_tag.strip().upper()
    if repositorio.existe_uid(uid_tag=uid_tag, negocio_id=negocio_id):
        raise UidDuplicado
    return repositorio.crear(negocio_id=negocio_id, uid_tag=uid_tag)


def cambiar_estado_de_pulsera(*, pulsera_id: int, negocio_id: int, estado: str) -> PulseraNfc:
    """Marca el chip como dañado, perdido o retirado.

    El estado es **solo la condición física**. A quién se le asignó vive en
    `clientes_evento`, que es una fila nueva cada vez.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    pulsera = obtener_pulsera(pulsera_id=pulsera_id, negocio_id=negocio_id)
    pulsera.estado = estado
    pulsera.save(update_fields=["estado", "actualizado_en"])
    return pulsera


def obtener_pulsera(*, pulsera_id: int, negocio_id: int) -> PulseraNfc:
    """Raises: NoEncontradoEnEsteNegocio."""
    pulsera = repositorio.obtener_del_negocio(pulsera_id=pulsera_id, negocio_id=negocio_id)
    if pulsera is None:
        raise NoEncontradoEnEsteNegocio
    return pulsera


def exigir_pulsera_disponible(*, pulsera_id: int, negocio_id: int) -> PulseraNfc:
    """Raises: NoEncontradoEnEsteNegocio, PulseraNoDisponible."""
    pulsera = obtener_pulsera(pulsera_id=pulsera_id, negocio_id=negocio_id)
    if not pulsera.se_puede_asignar:
        raise PulseraNoDisponible
    return pulsera


# --------------------------------------------------------------------------- #
# Dispositivos de puerta
# --------------------------------------------------------------------------- #
@transaction.atomic
def registrar_dispositivo(*, negocio_id: int, nombre: str) -> tuple[DispositivoNfc, str]:
    """Da de alta un lector y devuelve `(dispositivo, token en claro)`.

    **El token en claro se devuelve una sola vez**: en la base solo queda su
    hash, igual que en `invitaciones`. Quien lea la base de datos no puede
    autenticarse con lo que encuentre.
    """
    token, hash_token = generar_token_de_invitacion()
    dispositivo = repositorio.crear_dispositivo(
        negocio_id=negocio_id, nombre=nombre.strip(), hash_token=hash_token
    )
    return dispositivo, token


def revocar_dispositivo(*, dispositivo_id: int, negocio_id: int) -> DispositivoNfc:
    """Desactiva el lector sin perder de qué aparato era.

    Es lo que se hace cuando alguien abre la caja de la puerta y se lleva el
    token: se revoca ese y ya.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    dispositivo = repositorio.obtener_dispositivo_del_negocio(
        dispositivo_id=dispositivo_id, negocio_id=negocio_id
    )
    if dispositivo is None:
        raise NoEncontradoEnEsteNegocio
    dispositivo.activo = False
    dispositivo.save(update_fields=["activo", "actualizado_en"])
    return dispositivo
