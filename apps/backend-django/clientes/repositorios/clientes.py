"""Consultas al ORM sobre `clientes`. Ningún otro sitio escribe `Cliente.objects`."""

from django.db.models import QuerySet

from clientes.models import Cliente


def obtener_del_negocio(*, cliente_id: int, negocio_id: int) -> Cliente | None:
    """Una ficha, siempre acotada al negocio de quien pregunta."""
    return Cliente.objects.filter(pk=cliente_id, negocio_id=negocio_id).first()


def obtener_por_documento(
    *, negocio_id: int, tipo_documento: str, numero_documento: str
) -> Cliente | None:
    return Cliente.objects.filter(
        negocio_id=negocio_id,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
    ).first()


def del_negocio(*, negocio_id: int) -> QuerySet[Cliente]:
    return Cliente.objects.filter(negocio_id=negocio_id)


def existe_documento(
    *,
    negocio_id: int,
    tipo_documento: str,
    numero_documento: str,
    excluyendo_id: int | None = None,
) -> bool:
    consulta = Cliente.objects.filter(
        negocio_id=negocio_id,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
    )
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def crear(*, negocio_id: int, datos: dict) -> Cliente:
    return Cliente.objects.create(negocio_id=negocio_id, **datos)
