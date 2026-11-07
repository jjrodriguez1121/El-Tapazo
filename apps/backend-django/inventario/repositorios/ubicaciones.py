"""Consultas al ORM sobre `ubicaciones`."""

from django.db.models import QuerySet

from inventario.models import Ubicacion


def obtener_del_negocio(*, ubicacion_id: int, negocio_id: int) -> Ubicacion | None:
    return Ubicacion.objects.filter(pk=ubicacion_id, negocio_id=negocio_id).first()


def del_negocio(*, negocio_id: int) -> QuerySet[Ubicacion]:
    return Ubicacion.objects.filter(negocio_id=negocio_id)


def existe_nombre(*, negocio_id: int, nombre: str, excluyendo_id: int | None = None) -> bool:
    consulta = Ubicacion.objects.filter(negocio_id=negocio_id, nombre__iexact=nombre)
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def todas_son_del_negocio(*, ubicacion_ids: set[int], negocio_id: int) -> bool:
    """Una sola consulta para varios ids: comprobarlos de uno en uno sería N+1."""
    return Ubicacion.objects.filter(pk__in=ubicacion_ids, negocio_id=negocio_id).count() == len(
        ubicacion_ids
    )


def crear(*, negocio_id: int, nombre: str, tipo: str, direccion: str) -> Ubicacion:
    return Ubicacion.objects.create(
        negocio_id=negocio_id, nombre=nombre, tipo=tipo, direccion=direccion
    )
