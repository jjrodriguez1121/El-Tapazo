"""Avisos de consumo: cuándo una cuenta cruzó su límite y qué se hizo."""

from django.db import transaction
from django.utils import timezone

from eventos.models import AlertaConsumo
from eventos.repositorios import cuentas as repositorio_de_cuentas
from eventos.repositorios import pagos as repositorio
from eventos.selectores.saldos import consumo_de_una_cuenta
from nucleo.excepciones import NoEncontradoEnEsteNegocio


def revisar_limite_de_consumo(*, cliente_evento_id: int, negocio_id: int) -> AlertaConsumo | None:
    """Crea la alerta si el acumulado cruzó el límite de la cuenta.

    Se llama desde `registrar_pedido` y **dentro de su misma transacción**: si
    la comanda se deshace, la alerta que provocó tampoco queda.

    El umbral se copia en la fila, no se referencia: cambiar el límite mañana
    no puede reescribir la historia de por qué saltó esta alerta.

    Devuelve `None` si la cuenta no tiene límite, si no lo ha cruzado o si ya
    hay una alerta por ese umbral — sin esto, cada comanda posterior al cruce
    dispararía otra y la pantalla del cajero se llenaría de avisos de lo mismo.
    """
    cuenta = repositorio_de_cuentas.obtener_del_negocio(
        cuenta_id=cliente_evento_id, negocio_id=negocio_id
    )
    if cuenta is None or cuenta.limite_alerta is None:
        return None

    acumulado = consumo_de_una_cuenta(cliente_evento_id=cliente_evento_id, negocio_id=negocio_id)
    if acumulado < cuenta.limite_alerta:
        return None
    if repositorio.hay_alerta_por_encima(
        cliente_evento_id=cliente_evento_id, umbral=cuenta.limite_alerta
    ):
        return None

    return repositorio.crear_alerta(
        negocio_id=negocio_id,
        cliente_evento_id=cliente_evento_id,
        monto_acumulado=acumulado,
        umbral=cuenta.limite_alerta,
    )


@transaction.atomic
def atender_alerta(
    *, alerta_id: int, negocio_id: int, atendida_por_id: int, accion_tomada: str
) -> AlertaConsumo:
    """Deja constancia de qué se hizo con el aviso.

    Los tres datos van juntos porque la restricción
    `alerta_atencion_coherente` obliga a que la fecha y el autor estén o falten
    a la vez: una alerta atendida sin saber por quién no sirve de nada.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    alerta = repositorio.obtener_alerta_del_negocio(alerta_id=alerta_id, negocio_id=negocio_id)
    if alerta is None:
        raise NoEncontradoEnEsteNegocio

    alerta.atendida_por_id = atendida_por_id
    alerta.accion_tomada = accion_tomada.strip()
    alerta.atendida_en = timezone.now()
    alerta.save(update_fields=["atendida_por", "accion_tomada", "atendida_en", "actualizado_en"])
    return alerta
