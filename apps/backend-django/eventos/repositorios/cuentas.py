"""Consultas al ORM sobre `clientes_evento`: las cuentas de las personas."""

from django.db.models import QuerySet

from eventos.models import ClienteEvento


def obtener_del_negocio(*, cuenta_id: int, negocio_id: int) -> ClienteEvento | None:
    return (
        ClienteEvento.objects.select_related("cliente", "pulsera", "grupo_evento__evento")
        .filter(pk=cuenta_id, negocio_id=negocio_id)
        .first()
    )


def bloquear(*, cuenta_id: int, negocio_id: int) -> ClienteEvento | None:
    """La cuenta, bloqueada hasta el final de la transacción.

    Es lo que impide el doble cobro: dos cajeros cobrando la misma pulsera
    generarían dos pagos y la caja del día cuadraría de más. La restricción
    `pulsera_con_una_sola_asignacion_activa` **no** lo impide, porque impide dos
    asignaciones activas, no dos cierres.
    """
    return (
        ClienteEvento.objects.select_for_update()
        .filter(pk=cuenta_id, negocio_id=negocio_id)
        .first()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[ClienteEvento]:
    return ClienteEvento.objects.filter(negocio_id=negocio_id)


def abiertas_de_un_grupo(*, grupo_id: int, negocio_id: int) -> QuerySet[ClienteEvento]:
    return ClienteEvento.objects.filter(
        grupo_evento_id=grupo_id, negocio_id=negocio_id, liberada_en__isnull=True
    )


def abiertas_de_un_evento(*, evento_id: int, negocio_id: int) -> QuerySet[ClienteEvento]:
    """Las que impiden cerrar la caja."""
    return ClienteEvento.objects.filter(
        grupo_evento__evento_id=evento_id, negocio_id=negocio_id, liberada_en__isnull=True
    ).select_related("cliente", "pulsera")


def hay_asignacion_activa(*, pulsera_id: int) -> bool:
    return ClienteEvento.objects.filter(pulsera_id=pulsera_id, liberada_en__isnull=True).exists()


def crear(
    *,
    negocio_id: int,
    grupo_evento_id: int,
    cliente_id: int,
    pulsera_id: int | None,
    limite_alerta,
    asignada_por_id: int,
) -> ClienteEvento:
    return ClienteEvento.objects.create(
        negocio_id=negocio_id,
        grupo_evento_id=grupo_evento_id,
        cliente_id=cliente_id,
        pulsera_id=pulsera_id,
        limite_alerta=limite_alerta,
        asignada_por_id=asignada_por_id,
    )
