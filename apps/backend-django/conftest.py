"""Fixtures compartidas por las pruebas de todas las apps.

Las de datos crean **una persona de cada rol en el mismo negocio**. Que
compartan negocio es lo que las hace útiles: casi toda prueba de API necesita
comprobar dos cosas —que el rol correcto puede, y que un negocio no ve lo del
otro—, y para lo segundo basta con que una fábrica cree su propio negocio
aparte (`FabricaDeProducto()` sin argumentos ya es de otro negocio).

`staff` es la excepción: no pertenece a ningún negocio, y por eso ninguno de
los permisos por rol le sirve.
"""

from collections.abc import Callable

import pytest
from rest_framework.test import APIClient

from negocios.models import Negocio
from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.models import Rol, Usuario
from usuarios.pruebas.fabricas import FabricaDeStaffDePlataforma, FabricaDeUsuario


@pytest.fixture
def cliente_api() -> APIClient:
    """Cliente HTTP para las pruebas de API."""
    return APIClient()


@pytest.fixture
def negocio(db) -> Negocio:
    """El negocio al que pertenecen `administrador`, `cajero` y `mesero`."""
    return FabricaDeNegocio()


@pytest.fixture
def administrador(negocio) -> Usuario:
    """Puede todo: catálogo, inventario, distribución y la operación del bar."""
    return FabricaDeUsuario(negocio=negocio, rol=Rol.ADMINISTRADOR)


@pytest.fixture
def cajero(negocio) -> Usuario:
    """Opera la barra y además cobra, cierra cuentas y abre y cierra la caja."""
    return FabricaDeUsuario(negocio=negocio, rol=Rol.CAJERO)


@pytest.fixture
def mesero(negocio) -> Usuario:
    """Opera la barra: abre cuentas, asigna pulseras y toma comandas. No cobra."""
    return FabricaDeUsuario(negocio=negocio, rol=Rol.MESERO)


@pytest.fixture
def staff(db) -> Usuario:
    """El staff de la plataforma: da de alta negocios y no pertenece a ninguno."""
    return FabricaDeStaffDePlataforma()


@pytest.fixture
def cliente_api_autenticado(cliente_api) -> Callable[[Usuario], APIClient]:
    """Devuelve el cliente ya autenticado como esa persona.

        respuesta = cliente_api_autenticado(mesero).get("/api/v1/...")

    Es una función y no un cliente ya hecho porque la mitad de las pruebas que
    importan comparan dos roles distintos contra el mismo endpoint.
    """

    def autenticar(usuario: Usuario) -> APIClient:
        cliente_api.force_authenticate(usuario)
        return cliente_api

    return autenticar
