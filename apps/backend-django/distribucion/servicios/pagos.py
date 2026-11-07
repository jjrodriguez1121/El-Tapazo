"""Los abonos.

**Aquí sí hay abonos**, justo al revés que en el bar: una cuenta de la barra se
salda con un solo pago que cubre el total (decisión 3), y una tienda a 30 días
paga en varias veces.

Que la suma de los abonos no pase del total del pedido **no está declarado en
la base**: es un agregado, y una restricción de fila no puede mirar las otras
filas. Lo comprueba este servicio, bloqueando el pedido antes de sumar. Es la
única grieta del canal respecto a "si la regla cabe en la base, va en la base",
y es una limitación de SQL, no una decisión de diseño.
"""

from decimal import Decimal

from django.db import transaction

from distribucion.dtos import ResultadoDeAbonoDTO
from distribucion.excepciones import PagoSuperaElTotal, PedidoNoCobrable
from distribucion.models import PedidoDistribucion
from distribucion.repositorios import pagos as repositorio
from distribucion.repositorios import pedidos as repositorio_de_pedidos
from distribucion.selectores import saldo_de_un_pedido
from nucleo.excepciones import NoEncontradoEnEsteNegocio


@transaction.atomic
def registrar_pago(
    *,
    pedido_id: int,
    negocio_id: int,
    monto: Decimal,
    metodo: str,
    recibido_por_id: int,
    referencia_transaccion: str = "",
) -> ResultadoDeAbonoDTO:
    """Anota lo que la tienda abona contra un pedido y devuelve lo que falta.

    **Bloquea el pedido antes de sumar.** Dos cajeros registrando el último
    abono a la vez leerían los dos el mismo "ya pagado", los dos pasarían la
    comprobación y el pedido acabaría cobrado de más. El bloqueo es lo único
    que lo impide: la regla es un agregado y no cabe en una restricción de fila.

    Un abono de menos sí se acepta: eso es exactamente un abono.

    Raises:
        NoEncontradoEnEsteNegocio, PedidoNoCobrable, PagoSuperaElTotal.
    """
    pedido = repositorio_de_pedidos.bloquear(pedido_id=pedido_id, negocio_id=negocio_id)
    if pedido is None:
        raise NoEncontradoEnEsteNegocio
    if pedido.estado == PedidoDistribucion.Estado.CANCELADO:
        raise PedidoNoCobrable

    saldo = saldo_de_un_pedido(pedido_id=pedido.id, negocio_id=negocio_id)
    if monto > saldo.saldo:
        raise PagoSuperaElTotal(
            total=str(saldo.total), pagado=str(saldo.pagado), falta=str(saldo.saldo)
        )

    pago = repositorio.crear_pago(
        negocio_id=negocio_id,
        pedido_distribucion_id=pedido.id,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion.strip(),
        recibido_por_id=recibido_por_id,
    )
    return ResultadoDeAbonoDTO(
        pago_id=pago.id,
        total=saldo.total,
        pagado=saldo.pagado + monto,
        saldo=saldo.saldo - monto,
    )
