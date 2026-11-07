"""Pruebas de las restricciones de distribución que declara la base de datos."""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from distribucion.models import PedidoDistribucion
from distribucion.pruebas.fabricas import FabricaDePagoDistribucion, FabricaDePedidoDistribucion

pytestmark = pytest.mark.django_db


def test_un_pedido_no_entregado_tiene_que_decir_por_que():
    """Sin el motivo no se puede llamar a la tienda ni corregir la ruta."""
    with pytest.raises(IntegrityError), transaction.atomic():
        FabricaDePedidoDistribucion(
            estado=PedidoDistribucion.Estado.NO_ENTREGADO, motivo_no_entrega=""
        )


def test_un_pedido_no_entregado_con_motivo_se_guarda():
    pedido = FabricaDePedidoDistribucion(
        estado=PedidoDistribucion.Estado.NO_ENTREGADO,
        motivo_no_entrega="La tienda estaba cerrada.",
    )

    assert pedido.pk is not None


def test_los_demas_estados_no_necesitan_motivo():
    pedido = FabricaDePedidoDistribucion(estado=PedidoDistribucion.Estado.EN_RUTA)

    assert pedido.motivo_no_entrega == ""


def test_un_pedido_no_entregado_se_puede_volver_a_despachar():
    """Es la decisión 5: la mercancía volvió a la bodega y el pedido sigue vivo."""
    pedido = FabricaDePedidoDistribucion(
        estado=PedidoDistribucion.Estado.NO_ENTREGADO, motivo_no_entrega="Nadie recibió."
    )

    assert pedido.se_puede_despachar is True


def test_desde_en_ruta_no_se_puede_volver_a_despachar():
    pedido = FabricaDePedidoDistribucion(estado=PedidoDistribucion.Estado.EN_RUTA)

    assert pedido.se_puede_despachar is False


def test_un_pago_de_cero_no_es_un_pago():
    with pytest.raises(IntegrityError), transaction.atomic():
        FabricaDePagoDistribucion(monto=Decimal("0.00"))


def test_una_tienda_puede_abonar_varias_veces_contra_el_mismo_pedido():
    """Al revés que en el bar (decisión 3), aquí sí hay abonos: es a propósito."""
    pedido = FabricaDePedidoDistribucion()

    FabricaDePagoDistribucion(
        negocio=pedido.negocio, pedido_distribucion=pedido, monto=Decimal("30000.00")
    )
    FabricaDePagoDistribucion(
        negocio=pedido.negocio, pedido_distribucion=pedido, monto=Decimal("20000.00")
    )

    assert pedido.pagos.count() == 2
