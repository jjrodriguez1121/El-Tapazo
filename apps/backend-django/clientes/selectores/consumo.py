"""Qué ha consumido un cliente, evento por evento.

Este módulo mira tablas de `eventos`, y esa dirección es la segura: `eventos`
apunta a `clientes` por nombre (`"clientes.Cliente"`), nunca con un `import`,
así que leer al revés no crea un ciclo.

Nota para la fase de `eventos`: la suma de más abajo es la misma que necesitará
`eventos/selectores/saldos.py` para cobrar una cuenta. Cuando exista la
segunda, se extrae a un solo sitio; hoy hay una y extraerla sería inventarse el
futuro.
"""

from decimal import Decimal

from django.db.models import DecimalField, F, Q, QuerySet, Sum
from django.db.models.functions import Coalesce

from clientes.selectores.clientes import obtener_cliente
from eventos.models import ClienteEvento, PedidoEvento

# El producto de dos DecimalField(12, 2) no cabe en 12 dígitos, de ahí el 24.
# Y sin `output_field` Django lanza `FieldError` en una expresión mixta: la
# multiplicación de dos columnas no le dice de qué tipo es el resultado.
TIPO_DEL_IMPORTE = DecimalField(max_digits=24, decimal_places=4)

IMPORTE_CONSUMIDO = Coalesce(
    Sum(
        F("pedidos__detalles__cantidad") * F("pedidos__detalles__precio_unitario"),
        filter=~Q(pedidos__estado=PedidoEvento.Estado.CANCELADO),
        output_field=TIPO_DEL_IMPORTE,
    ),
    Decimal("0"),
    output_field=TIPO_DEL_IMPORTE,
)


def historial_de_consumo(*, cliente_id: int, negocio_id: int) -> QuerySet[ClienteEvento]:
    """Las cuentas que ha tenido esa persona y cuánto consumió en cada una.

    Lo suma la base de datos, no Python: traerse las líneas para sumarlas es el
    antipatrón explícito de las reglas, y aquí la lista crece con cada noche.

    Las comandas canceladas no cuentan — devolvieron el producto al inventario,
    así que tampoco se le cobraron.

    Raises:
        NoEncontradoEnEsteNegocio: la ficha no existe o es de otro negocio.
    """
    obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    return (
        ClienteEvento.objects.filter(cliente_id=cliente_id, negocio_id=negocio_id)
        .select_related("grupo_evento__evento")
        .annotate(consumido=IMPORTE_CONSUMIDO)
        .order_by("-creado_en")
    )
