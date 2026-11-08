"""Validaciones de fechas de vencimiento para compras a crédito."""

from datetime import timedelta

import pytest
from django.utils import timezone

from compras.api.serializers import CompraCrearSerializer

DATOS_COMPRA = {
    "proveedor_id": 1,
    "condicion_pago": "CREDITO",
    "detalles": [
        {
            "producto_id": 1,
            "cantidad": 1,
            "costo_unitario": "1000.00",
        }
    ],
}


@pytest.mark.parametrize(
    "fecha",
    [
        timezone.localdate(),
        timezone.localdate() - timedelta(days=1),
    ],
)
def test_compra_a_credito_rechaza_vencimiento_hoy_o_pasado(fecha):
    serializer = CompraCrearSerializer(
        data=DATOS_COMPRA | {"fecha_vencimiento": fecha.isoformat()}
    )

    assert serializer.is_valid() is False
    assert "fecha_vencimiento" in serializer.errors


def test_compra_a_credito_acepta_vencimiento_futuro():
    fecha = timezone.localdate() + timedelta(days=1)
    serializer = CompraCrearSerializer(
        data=DATOS_COMPRA | {"fecha_vencimiento": fecha.isoformat()}
    )

    assert serializer.is_valid(), serializer.errors


def test_compra_a_credito_exige_fecha_de_vencimiento():
    serializer = CompraCrearSerializer(data=DATOS_COMPRA)

    assert serializer.is_valid() is False
    assert "fecha_vencimiento" in serializer.errors
