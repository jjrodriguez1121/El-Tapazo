"""Lecturas del canal evento/bar."""

from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, QuerySet, Sum

from eventos.models import (
    AlertaConsumo,
    ClienteEvento,
    DetallePedidoEvento,
    Evento,
    GrupoEvento,
    PedidoEvento,
    PulseraNfc,
)
from eventos.repositorios import cuentas as repositorio_de_cuentas
from eventos.repositorios import eventos as repositorio
from eventos.repositorios import grupos as repositorio_de_grupos
from eventos.repositorios import pagos as repositorio_de_pagos
from eventos.repositorios import pedidos as repositorio_de_pedidos
from eventos.repositorios import pulseras as repositorio_de_pulseras
from eventos.selectores.saldos import TIPO_DEL_IMPORTE, consumo_de_una_cuenta
from nucleo.excepciones import NoEncontradoEnEsteNegocio

NO_CANCELADOS = ~Q(pedido_evento__estado=PedidoEvento.Estado.CANCELADO)


def eventos_del_negocio(*, negocio_id: int) -> QuerySet[Evento]:
    return repositorio.del_negocio(negocio_id=negocio_id).select_related("ubicacion")


def grupos_del_negocio(*, negocio_id: int) -> QuerySet[GrupoEvento]:
    return repositorio_de_grupos.del_negocio(negocio_id=negocio_id).select_related(
        "evento", "abierto_por"
    )


def cuentas_del_negocio(*, negocio_id: int) -> QuerySet[ClienteEvento]:
    """Las cuentas, con su persona y su pulsera ya cargadas."""
    return repositorio_de_cuentas.del_negocio(negocio_id=negocio_id).select_related(
        "cliente", "pulsera", "grupo_evento"
    )


def pedidos_del_negocio(*, negocio_id: int) -> QuerySet[PedidoEvento]:
    return repositorio_de_pedidos.del_negocio(negocio_id=negocio_id).select_related(
        "cliente_evento__cliente", "mesero", "evento"
    )


def pulseras_del_negocio(*, negocio_id: int) -> QuerySet[PulseraNfc]:
    return repositorio_de_pulseras.del_negocio(negocio_id=negocio_id)


def alertas_del_negocio(*, negocio_id: int) -> QuerySet[AlertaConsumo]:
    return repositorio_de_pagos.alertas_del_negocio(negocio_id=negocio_id).select_related(
        "cliente_evento__cliente", "atendida_por"
    )


def detalles_de_un_pedido(*, pedido_id: int, negocio_id: int) -> QuerySet[DetallePedidoEvento]:
    return repositorio_de_pedidos.detalles_de(pedido_id=pedido_id, negocio_id=negocio_id)


def informe_de_cierre(*, evento_id: int, negocio_id: int) -> dict:
    """Lo que se vendió, lo que se cobró y con qué se cobró.

    Las tres consultas las hace la base de datos. Es el informe por el que
    existe la jornada: el cierre es «todo lo que se vendió entre que se abrió y
    se cerró esto».
    """
    ventas = (
        DetallePedidoEvento.objects.filter(
            pedido_evento__evento_id=evento_id, negocio_id=negocio_id
        )
        .filter(NO_CANCELADOS)
        .values("producto_id", "producto__nombre", "producto__sku")
        .annotate(
            unidades=Sum("cantidad"),
            importe=Sum(F("cantidad") * F("precio_unitario"), output_field=TIPO_DEL_IMPORTE),
        )
        .order_by("-importe")
    )

    pagos = (
        repositorio_de_pagos.pagos_de_un_evento(evento_id=evento_id, negocio_id=negocio_id)
        .values("metodo")
        .annotate(
            total=Sum("monto", output_field=DecimalField(max_digits=24, decimal_places=2)),
            cuantos=Count("id"),
        )
        .order_by("metodo")
    )

    total_cobrado = repositorio_de_pagos.pagos_de_un_evento(
        evento_id=evento_id, negocio_id=negocio_id
    ).aggregate(total=Sum("monto"))["total"] or Decimal("0")

    cuentas_atendidas = ClienteEvento.objects.filter(
        grupo_evento__evento_id=evento_id, negocio_id=negocio_id
    ).count()

    return {
        "ventas_por_producto": list(ventas),
        "pagos_por_metodo": list(pagos),
        "total_cobrado": total_cobrado,
        "cuentas_atendidas": cuentas_atendidas,
    }


def consultar_punto_de_control(*, uid_tag: str, negocio_id: int) -> dict:
    """Lo que el lector de la puerta necesita saber, y **nada más**.

    Devuelve el nombre y el monto: ni documento, ni teléfono. Cualquiera con un
    lector de tres dólares puede acercarlo a una pulsera, así que lo que sale
    por aquí tiene que ser lo mínimo.

    Raises:
        NoEncontradoEnEsteNegocio: esa pulsera no está registrada aquí.
    """
    pulsera = repositorio_de_pulseras.obtener_por_uid(uid_tag=uid_tag, negocio_id=negocio_id)
    if pulsera is None:
        raise NoEncontradoEnEsteNegocio

    cuenta = (
        ClienteEvento.objects.select_related("cliente")
        .filter(pulsera_id=pulsera.id, negocio_id=negocio_id, liberada_en__isnull=True)
        .first()
    )
    if cuenta is None:
        return {"estado": "saldada", "cliente": "", "monto": Decimal("0.00")}

    consumido = consumo_de_una_cuenta(cliente_evento_id=cuenta.id, negocio_id=negocio_id)
    if consumido <= 0:
        return {
            "estado": "saldada",
            "cliente": cuenta.cliente.nombre_completo,
            "monto": Decimal("0.00"),
        }
    return {
        "estado": "con_saldo",
        "cliente": cuenta.cliente.nombre_completo,
        "monto": consumido,
    }
