"""Consultas al ORM sobre `pagos_evento` y `alertas_consumo`."""

from datetime import date
from decimal import Decimal

from django.db.models import QuerySet, Sum
from django.utils import timezone

from eventos.models import AlertaConsumo, PagoEvento


def crear_pago(
    *,
    negocio_id: int,
    evento_id: int,
    grupo_evento_id: int | None,
    cliente_evento_id: int | None,
    pedido_evento_id: int | None,
    monto: Decimal,
    metodo: str,
    referencia_transaccion: str,
    recibido_por_id: int,
) -> PagoEvento:
    return PagoEvento.objects.create(
        negocio_id=negocio_id,
        evento_id=evento_id,
        grupo_evento_id=grupo_evento_id,
        cliente_evento_id=cliente_evento_id,
        pedido_evento_id=pedido_evento_id,
        monto=monto,
        metodo=metodo,
        referencia_transaccion=referencia_transaccion,
        recibido_por_id=recibido_por_id,
    )


def pagos_de_un_evento(*, evento_id: int, negocio_id: int) -> QuerySet[PagoEvento]:
    return PagoEvento.objects.filter(evento_id=evento_id, negocio_id=negocio_id)


def cobrado_entre(*, negocio_id: int, desde: date, hasta: date) -> Decimal:
    """El dinero que entró por la barra entre dos fechas, las dos incluidas."""
    total = PagoEvento.objects.filter(
        negocio_id=negocio_id, fecha__date__gte=desde, fecha__date__lte=hasta
    ).aggregate(total=Sum("monto"))["total"]
    return total if total is not None else Decimal("0")


# --------------------------------------------------------------------------- #
# Alertas de consumo
# --------------------------------------------------------------------------- #
def crear_alerta(
    *, negocio_id: int, cliente_evento_id: int, monto_acumulado: Decimal, umbral: Decimal
) -> AlertaConsumo:
    return AlertaConsumo.objects.create(
        negocio_id=negocio_id,
        cliente_evento_id=cliente_evento_id,
        monto_acumulado=monto_acumulado,
        # Se copia el umbral **del momento**: cambiar el límite mañana no puede
        # reescribir la historia de por qué saltó esta alerta.
        umbral_superado=umbral,
        fecha=timezone.now(),
    )


def obtener_alerta_del_negocio(*, alerta_id: int, negocio_id: int) -> AlertaConsumo | None:
    return (
        AlertaConsumo.objects.select_related("cliente_evento__cliente")
        .filter(pk=alerta_id, negocio_id=negocio_id)
        .first()
    )


def alertas_del_negocio(*, negocio_id: int) -> QuerySet[AlertaConsumo]:
    return AlertaConsumo.objects.filter(negocio_id=negocio_id)


def hay_alerta_por_encima(*, cliente_evento_id: int, umbral: Decimal) -> bool:
    """Si esa cuenta ya tiene una alerta con ese umbral o mayor.

    Sin esto, cada comanda posterior al cruce dispararía una alerta nueva y la
    pantalla del cajero se llenaría de avisos de lo mismo.
    """
    return AlertaConsumo.objects.filter(
        cliente_evento_id=cliente_evento_id, umbral_superado__gte=umbral
    ).exists()
