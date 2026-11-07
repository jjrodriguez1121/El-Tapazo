"""Consultas al ORM sobre `clientes_distribucion`.

Aquí vive también la consulta de la mora, que es la que justifica que
`dias_credito` exista: qué tiendas se pasaron del plazo y cuánto deben.
"""

from datetime import timedelta

from django.db.models import (
    DateTimeField,
    DurationField,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, Now

from distribucion.models import (
    ClienteDistribucion,
    DetallePedidoDistribucion,
    PagoDistribucion,
    PedidoDistribucion,
)
from distribucion.repositorios.pedidos import SIN_IMPORTE, TIPO_DEL_IMPORTE

UN_DIA = Value(timedelta(days=1), output_field=DurationField())

# Desde una línea o desde un pago se llega al pedido por el mismo camino.
EL_PEDIDO = "pedido_distribucion__"


def obtener_del_negocio(*, cliente_id: int, negocio_id: int) -> ClienteDistribucion | None:
    return ClienteDistribucion.objects.filter(pk=cliente_id, negocio_id=negocio_id).first()


def del_negocio(*, negocio_id: int) -> QuerySet[ClienteDistribucion]:
    return ClienteDistribucion.objects.filter(negocio_id=negocio_id)


def existe_nit(*, negocio_id: int, nit: str, excluyendo_id: int | None = None) -> bool:
    consulta = ClienteDistribucion.objects.filter(negocio_id=negocio_id, nit=nit)
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def crear(*, negocio_id: int, datos: dict) -> ClienteDistribucion:
    return ClienteDistribucion.objects.create(negocio_id=negocio_id, **datos)


def en_mora(*, negocio_id: int) -> QuerySet[ClienteDistribucion]:
    """Tiendas cuyo plazo ya venció y todavía deben, con su `deuda_vencida`.

    Los dos importes se traen con **una subconsulta cada uno y no con dos
    `Sum` en la misma consulta**: sumar por dos caminos a la vez —las líneas y
    los pagos— multiplica las filas del `JOIN` y cada total sale inflado por
    las filas del otro. Es el clásico *fan-out*, y da un número que parece
    razonable, que es lo peor que puede dar.
    """
    facturado = _por_cliente(
        DetallePedidoDistribucion.objects,
        importe=Sum(F("cantidad") * F("precio_unitario"), output_field=TIPO_DEL_IMPORTE),
    )
    pagado = _por_cliente(PagoDistribucion.objects, importe=Sum("monto"))
    return (
        ClienteDistribucion.objects.filter(negocio_id=negocio_id)
        .annotate(
            deuda_vencida=Coalesce(facturado, Value(SIN_IMPORTE), output_field=TIPO_DEL_IMPORTE)
            - Coalesce(pagado, Value(SIN_IMPORTE), output_field=TIPO_DEL_IMPORTE)
        )
        .filter(deuda_vencida__gt=0)
    )


def _por_cliente(manager, *, importe) -> Subquery:
    """Suma ese importe sobre los pedidos vencidos de **la tienda de fuera**."""
    return Subquery(
        manager.filter(
            _vencimiento_pasado(),
            negocio_id=OuterRef("negocio_id"),
            **{
                f"{EL_PEDIDO}cliente_distribucion_id": OuterRef("pk"),
                f"{EL_PEDIDO}estado": PedidoDistribucion.Estado.ENTREGADO,
            },
        )
        .values(f"{EL_PEDIDO}cliente_distribucion")
        .annotate(total=importe)
        .values("total"),
        output_field=TIPO_DEL_IMPORTE,
    )


def _vencimiento_pasado() -> Q:
    """El plazo de crédito de ese pedido ya se acabó.

    Se escribe como `fecha_entrega < ahora − plazo` y no como
    `fecha_entrega + plazo < ahora` a propósito: la segunda forma obliga a
    anotar la suma para poder filtrarla, y esa anotación de más se cuela en el
    `GROUP BY` de la subconsulta y la parte en una fila por pedido.

    Un pedido sin entregar no vence nunca —`fecha_entrega` es nula y la
    comparación lo deja fuera—, que es justo lo que se quiere: el plazo corre
    desde que la tienda recibe.
    """
    plazo = ExpressionWrapper(
        UN_DIA * F(f"{EL_PEDIDO}cliente_distribucion__dias_credito"),
        output_field=DurationField(),
    )
    limite = ExpressionWrapper(Now() - plazo, output_field=DateTimeField())
    return Q(**{f"{EL_PEDIDO}fecha_entrega__lt": limite})
