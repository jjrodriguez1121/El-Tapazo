"""Consultas al ORM sobre `clientes`. Ningún otro sitio escribe `Cliente.objects`."""

from django.db.models import DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce

from clientes.models import Cliente
from ventas.models import CuentaPorCobrar, Venta


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
    return Cliente.objects.filter(negocio_id=negocio_id).annotate(
        saldo_pendiente=Coalesce(
            Sum(
                "ventas__cuenta_por_cobrar__saldo",
                filter=Q(
                    ventas__negocio_id=negocio_id,
                    ventas__estado__in=(Venta.Estado.PENDIENTE, Venta.Estado.PAGADA),
                    ventas__cuenta_por_cobrar__estado__in=(
                        CuentaPorCobrar.Estado.PENDIENTE,
                        CuentaPorCobrar.Estado.PARCIAL,
                        CuentaPorCobrar.Estado.VENCIDA,
                    ),
                ),
            ),
            Value(0),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )


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
