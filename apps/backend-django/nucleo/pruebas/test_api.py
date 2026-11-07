"""Pruebas de las piezas compartidas de la capa HTTP."""

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from nucleo.api.vistas import MixinDelNegocio
from usuarios.models import Usuario


class VistaDePrueba(MixinDelNegocio):
    def __init__(self, usuario):
        self.request = APIRequestFactory().get("/")
        self.request.user = usuario


def test_el_negocio_sale_del_usuario_autenticado(mesero):
    assert VistaDePrueba(mesero).negocio_id == mesero.negocio_id


@pytest.mark.django_db
def test_sin_negocio_es_403_y_no_un_error_del_servidor():
    """El staff de la plataforma no tiene negocio. Que no reviente con un 500."""
    staff = Usuario.objects.create_superuser(correo="staff@tapaso.test", password="x")

    with pytest.raises(PermissionDenied):
        _ = VistaDePrueba(staff).negocio_id
