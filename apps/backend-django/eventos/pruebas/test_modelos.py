"""Pruebas de las restricciones de eventos que declara la base de datos."""

import pytest
from django.db import IntegrityError, transaction

from eventos.models import Evento
from eventos.pruebas.fabricas import FabricaDeDispositivoNfc, FabricaDeEvento
from inventario.pruebas.fabricas import FabricaDeUbicacion

pytestmark = pytest.mark.django_db


def test_una_ubicacion_no_puede_tener_dos_jornadas_abiertas():
    """Lo que hace segura la apertura automática.

    Sin esta restricción, dos peticiones simultáneas del primer pedido del día
    abrirían dos eventos y partirían el cierre de caja en dos informes.
    """
    abierta = FabricaDeEvento(estado=Evento.Estado.EN_CURSO)

    with pytest.raises(IntegrityError), transaction.atomic():
        FabricaDeEvento(
            negocio=abierta.negocio,
            ubicacion=abierta.ubicacion,
            estado=Evento.Estado.EN_CURSO,
        )


def test_dos_ubicaciones_distintas_pueden_tener_su_jornada_a_la_vez():
    abierta = FabricaDeEvento(estado=Evento.Estado.EN_CURSO)
    otra_barra = FabricaDeUbicacion(negocio=abierta.negocio)

    segunda = FabricaDeEvento(
        negocio=abierta.negocio, ubicacion=otra_barra, estado=Evento.Estado.EN_CURSO
    )

    assert segunda.pk is not None


def test_la_jornada_cerrada_deja_abrir_otra_en_la_misma_ubicacion():
    """Si no, una barra solo podría abrir una vez en su vida."""
    ayer = FabricaDeEvento(estado=Evento.Estado.CERRADO)

    hoy = FabricaDeEvento(
        negocio=ayer.negocio, ubicacion=ayer.ubicacion, estado=Evento.Estado.EN_CURSO
    )

    assert hoy.pk is not None


def test_varios_eventos_planeados_sin_ubicacion_no_se_estorban():
    """Un evento se puede planear antes de decidir dónde se monta la barra."""
    primero = FabricaDeEvento(ubicacion=None, estado=Evento.Estado.EN_CURSO)

    segundo = FabricaDeEvento(
        negocio=primero.negocio, ubicacion=None, estado=Evento.Estado.EN_CURSO
    )

    assert segundo.pk is not None


def test_el_token_de_un_dispositivo_es_unico_en_toda_la_plataforma():
    """Global y no por negocio: cuando llega la petición del lector todavía no
    se sabe de qué negocio es — se averigua justo por el token."""
    lector = FabricaDeDispositivoNfc()

    with pytest.raises(IntegrityError), transaction.atomic():
        FabricaDeDispositivoNfc(hash_token=lector.hash_token)


def test_del_dispositivo_solo_se_guarda_el_hash_del_token():
    lector = FabricaDeDispositivoNfc()

    assert lector.token_en_claro not in lector.hash_token
    assert len(lector.hash_token) == 64
