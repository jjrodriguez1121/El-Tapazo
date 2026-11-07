"""Pruebas de `crear_datos_iniciales`, el negocio y administrador de desarrollo."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from negocios.models import Negocio
from usuarios.models import Rol, Usuario
from usuarios.servicios import sesiones

pytestmark = pytest.mark.django_db


def crear_datos() -> None:
    call_command("crear_datos_iniciales", stdout=StringIO())


@override_settings(DEBUG=True)
def test_crea_el_negocio_y_un_administrador_que_puede_iniciar_sesion():
    crear_datos()

    usuario = Usuario.objects.get(correo="admin@gmail.com")
    assert usuario.negocio.nombre_comercial == "El Tapaso"
    assert usuario.rol == Rol.ADMINISTRADOR
    assert sesiones.iniciar_sesion(correo="admin@gmail.com", contrasena="admin123")


@override_settings(DEBUG=True)
def test_correrlo_dos_veces_no_duplica_ni_cambia_la_contrasena():
    crear_datos()
    usuario = Usuario.objects.get(correo="admin@gmail.com")
    usuario.set_password("otra-clave-123")
    usuario.save()

    crear_datos()

    assert Negocio.objects.count() == 1
    assert Usuario.objects.count() == 1
    usuario.refresh_from_db()
    assert usuario.check_password("otra-clave-123")


@override_settings(DEBUG=False)
def test_sin_debug_se_niega_para_no_llevar_la_clave_a_produccion():
    with pytest.raises(CommandError, match="DEBUG"):
        crear_datos()

    assert not Usuario.objects.exists()
