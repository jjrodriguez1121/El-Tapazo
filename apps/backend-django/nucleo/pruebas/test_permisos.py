"""Pruebas de los permisos por rol.

Esta es la matriz de la decisión 6 del plan de negocio escrita como prueba: si
alguien cambia quién puede qué, se entera aquí y no en producción.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from nucleo.permisos import EsAdministrador, EsCajeroOAdministrador, EsDelEquipo
from usuarios.models import Usuario


def _peticion_de(usuario):
    peticion = APIRequestFactory().get("/")
    peticion.user = usuario
    return peticion


def _puede(permiso, usuario) -> bool:
    return permiso().has_permission(_peticion_de(usuario), view=None)


@pytest.mark.parametrize(
    ("rol_del_usuario", "admin", "cajero_o_admin", "equipo"),
    [
        ("administrador", True, True, True),
        ("cajero", False, True, True),
        ("mesero", False, False, True),
    ],
)
def test_cada_rol_pasa_solo_los_permisos_que_le_tocan(
    request, rol_del_usuario, admin, cajero_o_admin, equipo
):
    usuario = request.getfixturevalue(rol_del_usuario)

    assert _puede(EsAdministrador, usuario) is admin
    assert _puede(EsCajeroOAdministrador, usuario) is cajero_o_admin
    assert _puede(EsDelEquipo, usuario) is equipo


@pytest.mark.django_db
def test_el_staff_de_la_plataforma_no_opera_ningun_negocio():
    """No tiene negocio: da de alta negocios, no vende cerveza en ninguno."""
    staff = Usuario.objects.create_superuser(correo="staff@tapaso.test", password="x")

    assert _puede(EsAdministrador, staff) is False
    assert _puede(EsCajeroOAdministrador, staff) is False
    assert _puede(EsDelEquipo, staff) is False


def test_sin_iniciar_sesion_no_se_pasa_ningun_permiso():
    anonimo = AnonymousUser()

    assert _puede(EsAdministrador, anonimo) is False
    assert _puede(EsCajeroOAdministrador, anonimo) is False
    assert _puede(EsDelEquipo, anonimo) is False
