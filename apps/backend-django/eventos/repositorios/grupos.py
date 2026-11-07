"""Consultas al ORM sobre `grupos_evento`."""

from django.db.models import QuerySet

from eventos.models import GrupoEvento


def obtener_del_negocio(*, grupo_id: int, negocio_id: int) -> GrupoEvento | None:
    return (
        GrupoEvento.objects.select_related("evento")
        .filter(pk=grupo_id, negocio_id=negocio_id)
        .first()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[GrupoEvento]:
    return GrupoEvento.objects.filter(negocio_id=negocio_id)


def crear(
    *,
    negocio_id: int,
    evento_id: int,
    nombre_referencia: str,
    mesa_zona: str,
    abierto_por_id: int,
) -> GrupoEvento:
    return GrupoEvento.objects.create(
        negocio_id=negocio_id,
        evento_id=evento_id,
        nombre_referencia=nombre_referencia,
        mesa_zona=mesa_zona,
        abierto_por_id=abierto_por_id,
    )
