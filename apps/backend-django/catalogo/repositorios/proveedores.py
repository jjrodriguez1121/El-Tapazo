"""Consultas al ORM sobre `proveedores`."""

from django.db.models import QuerySet

from catalogo.models import Proveedor


def obtener_del_negocio(*, proveedor_id: int, negocio_id: int) -> Proveedor | None:
    return Proveedor.objects.filter(pk=proveedor_id, negocio_id=negocio_id).first()


def del_negocio(*, negocio_id: int) -> QuerySet[Proveedor]:
    return Proveedor.objects.filter(negocio_id=negocio_id)


def existe_nit(*, negocio_id: int, nit: str, excluyendo_id: int | None = None) -> bool:
    """Si ya hay un proveedor con ese NIT. Un NIT vacío nunca choca: es lo que
    permite registrar varios proveedores sin NIT, igual que la restricción
    parcial de la base."""
    if not nit:
        return False
    consulta = Proveedor.objects.filter(negocio_id=negocio_id, nit=nit)
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def crear(*, negocio_id: int, datos: dict) -> Proveedor:
    return Proveedor.objects.create(negocio_id=negocio_id, **datos)
