"""Consultas al ORM sobre `pulseras_nfc` y `dispositivos_nfc`."""

from django.db.models import QuerySet
from django.utils import timezone

from eventos.models import DispositivoNfc, PulseraNfc


def obtener_del_negocio(*, pulsera_id: int, negocio_id: int) -> PulseraNfc | None:
    return PulseraNfc.objects.filter(pk=pulsera_id, negocio_id=negocio_id).first()


def obtener_por_uid(*, uid_tag: str, negocio_id: int) -> PulseraNfc | None:
    return PulseraNfc.objects.filter(uid_tag=uid_tag, negocio_id=negocio_id).first()


def del_negocio(*, negocio_id: int) -> QuerySet[PulseraNfc]:
    return PulseraNfc.objects.filter(negocio_id=negocio_id)


def existe_uid(*, uid_tag: str, negocio_id: int) -> bool:
    return PulseraNfc.objects.filter(uid_tag=uid_tag, negocio_id=negocio_id).exists()


def crear(*, negocio_id: int, uid_tag: str) -> PulseraNfc:
    return PulseraNfc.objects.create(negocio_id=negocio_id, uid_tag=uid_tag)


# --------------------------------------------------------------------------- #
# Dispositivos: los lectores de la puerta
# --------------------------------------------------------------------------- #
def obtener_dispositivo_por_hash(*, hash_token: str) -> DispositivoNfc | None:
    """Se busca por el token y **no** por negocio: cuando llega la petición del
    lector todavía no se sabe de qué negocio es — se averigua justo por aquí."""
    return (
        DispositivoNfc.objects.select_related("negocio")
        .filter(hash_token=hash_token, activo=True)
        .first()
    )


def dispositivos_del_negocio(*, negocio_id: int) -> QuerySet[DispositivoNfc]:
    return DispositivoNfc.objects.filter(negocio_id=negocio_id)


def obtener_dispositivo_del_negocio(
    *, dispositivo_id: int, negocio_id: int
) -> DispositivoNfc | None:
    return DispositivoNfc.objects.filter(pk=dispositivo_id, negocio_id=negocio_id).first()


def crear_dispositivo(*, negocio_id: int, nombre: str, hash_token: str) -> DispositivoNfc:
    return DispositivoNfc.objects.create(
        negocio_id=negocio_id, nombre=nombre, hash_token=hash_token
    )


def marcar_uso(*, dispositivo_id: int) -> None:
    """`actualizado_en` va explícito: un `update()` no dispara `auto_now`."""
    DispositivoNfc.objects.filter(pk=dispositivo_id).update(
        ultimo_uso_en=timezone.now(), actualizado_en=timezone.now()
    )
