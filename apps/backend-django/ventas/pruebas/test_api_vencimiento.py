"""Validaciones de fechas de vencimiento en la API de ventas."""

from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "fecha",
    [
        timezone.localdate().isoformat(),
        (timezone.localdate() - timedelta(days=1)).isoformat(),
    ],
)
def test_api_ventas_rechaza_vencimiento_no_futuro(
    cliente_api_autenticado, cajero, fecha
):
    respuesta = cliente_api_autenticado(cajero).post(
        "/api/v1/ventas/",
        {
            "lineas": [{"producto_id": 999999, "cantidad": "1"}],
            "tipo_pago": "credito",
            "cliente_id": 1,
            "fecha_vencimiento": fecha,
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert "fecha_vencimiento" in respuesta.data["error"]["detalles"]


def test_api_ventas_a_credito_exige_fecha_de_vencimiento(
    cliente_api_autenticado, cajero
):
    respuesta = cliente_api_autenticado(cajero).post(
        "/api/v1/ventas/",
        {
            "lineas": [{"producto_id": 999999, "cantidad": "1"}],
            "tipo_pago": "credito",
            "cliente_id": 1,
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert "fecha_vencimiento" in respuesta.data["error"]["detalles"]
