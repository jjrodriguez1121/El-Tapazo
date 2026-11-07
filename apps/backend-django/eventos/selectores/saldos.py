"""Lo que ha consumido una cuenta o un grupo.

**Lo suma la base de datos, no Python.** Traerse las líneas para sumarlas es el
antipatrón explícito de las reglas, y aquí la lista crece con cada ronda de la
noche.

Hay un detalle que había que escribir bien a la primera porque es el número que
ve el cliente al pagar: sin `output_field` Django lanza `FieldError` en una
expresión mixta —la multiplicación de dos columnas no le dice de qué tipo es el
resultado— y el producto de dos `DecimalField(12, 2)` no cabe en 12 dígitos, de
ahí el 24. Se cuantiza a dos decimales al final.
"""

from decimal import Decimal

from django.db.models import DecimalField, F, Q, Sum

from eventos.models import DetallePedidoEvento, PedidoEvento

TIPO_DEL_IMPORTE = DecimalField(max_digits=24, decimal_places=4)
CENTAVOS = Decimal("0.01")

# Las comandas canceladas no se cobran: devolvieron el producto al inventario.
NO_CANCELADAS = ~Q(pedido_evento__estado=PedidoEvento.Estado.CANCELADO)


def consumo_de_una_cuenta(*, cliente_evento_id: int, negocio_id: int) -> Decimal:
    """Lo que lleva consumido una persona en su cuenta abierta."""
    return _sumar(Q(pedido_evento__cliente_evento_id=cliente_evento_id, negocio_id=negocio_id))


def consumo_de_un_grupo(*, grupo_id: int, negocio_id: int) -> Decimal:
    """Lo que llevan consumido todas las cuentas de la mesa."""
    return _sumar(Q(pedido_evento__cliente_evento__grupo_evento_id=grupo_id, negocio_id=negocio_id))


def consumo_de_un_pedido(*, pedido_id: int, negocio_id: int) -> Decimal:
    """Lo que cuesta una comanda suelta. Es lo que se cobra en el mostrador."""
    return _sumar(Q(pedido_evento_id=pedido_id, negocio_id=negocio_id))


def _sumar(filtro: Q) -> Decimal:
    total = (
        DetallePedidoEvento.objects.filter(filtro)
        .filter(NO_CANCELADAS)
        .aggregate(
            total=Sum(
                F("cantidad") * F("precio_unitario"),
                output_field=TIPO_DEL_IMPORTE,
            )
        )["total"]
    )
    return (total or Decimal("0")).quantize(CENTAVOS)
