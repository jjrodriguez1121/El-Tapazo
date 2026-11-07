"""Pruebas de las restricciones de inventario que declara la base de datos.

Se prueban con `IntegrityError` y no con `full_clean()` a propósito: lo que
interesa es que la base las cumpla **entre por donde entre** el dato — la API,
el admin de Django, un script o `psql`.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from inventario.pruebas.fabricas import FabricaDeExistencia

pytestmark = pytest.mark.django_db


def test_la_cantidad_minima_no_puede_ser_negativa():
    with pytest.raises(IntegrityError), transaction.atomic():
        FabricaDeExistencia(cantidad_minima=Decimal("-1.00"))


def test_con_la_minima_en_cero_nunca_esta_bajo_minimo():
    """Cero significa «sin alerta», no «alerta siempre». Es el valor por defecto."""
    existencia = FabricaDeExistencia(
        cantidad_disponible=Decimal("0.00"), cantidad_minima=Decimal("0.00")
    )

    assert existencia.esta_bajo_minimo is False


def test_esta_bajo_minimo_cuando_el_saldo_baja_del_punto_de_reposicion():
    existencia = FabricaDeExistencia(
        cantidad_disponible=Decimal("5.00"), cantidad_minima=Decimal("20.00")
    )

    assert existencia.esta_bajo_minimo is True


def test_estar_justo_en_el_minimo_todavia_no_es_alerta():
    existencia = FabricaDeExistencia(
        cantidad_disponible=Decimal("20.00"), cantidad_minima=Decimal("20.00")
    )

    assert existencia.esta_bajo_minimo is False
