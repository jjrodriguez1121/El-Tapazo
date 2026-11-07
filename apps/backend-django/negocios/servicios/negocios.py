"""Alta, cambio, suspensión y reactivación de negocios."""

from negocios.excepciones import (
    NegocioYaActivo,
    NegocioYaSuspendido,
    NitDeNegocioDuplicado,
)
from negocios.models import Negocio
from negocios.repositorios import negocios as repositorio
from negocios.selectores import obtener_negocio


def crear_negocio(*, nombre_comercial: str, nit: str) -> Negocio:
    """Da de alta un negocio en la plataforma.

    Nace **sin nadie dentro**: quien lo crea invita después a su primer
    administrador desde la terminal (`manage invitar_administrador`), y a
    partir de ahí ese administrador invita a su equipo. Es el huevo y la
    gallina del modelo, y se resuelve así a propósito — no hay registro
    público.

    Raises:
        NitDeNegocioDuplicado.
    """
    nombre_comercial, nit = nombre_comercial.strip(), nit.strip()
    if repositorio.existe_nit(nit=nit):
        raise NitDeNegocioDuplicado
    return repositorio.crear(nombre_comercial=nombre_comercial, nit=nit)


def actualizar_datos(*, negocio_id: int, nombre_comercial: str, nit: str) -> Negocio:
    """Corrige el nombre comercial o el NIT de un negocio.

    Raises:
        NegocioNoEncontrado, NitDeNegocioDuplicado.
    """
    negocio = obtener_negocio(negocio_id=negocio_id)
    if repositorio.existe_nit(nit=nit.strip(), excluyendo_id=negocio_id):
        raise NitDeNegocioDuplicado

    negocio.nombre_comercial = nombre_comercial.strip()
    negocio.nit = nit.strip()
    negocio.save(update_fields=["nombre_comercial", "nit", "actualizado_en"])
    return negocio


def suspender_negocio(*, negocio_id: int) -> Negocio:
    """Deja al negocio sin poder operar, sin borrarle nada.

    A partir de aquí **su gente no puede entrar**: el inicio de sesión lo
    comprueba y responde `negocio_suspendido`. Los datos siguen ahí enteros,
    que es la diferencia entre suspender y dar de baja.

    Raises:
        NegocioNoEncontrado, NegocioYaSuspendido.
    """
    negocio = obtener_negocio(negocio_id=negocio_id)
    if not negocio.esta_operativo:
        raise NegocioYaSuspendido

    negocio.estado = Negocio.Estado.SUSPENDIDO
    negocio.save(update_fields=["estado", "actualizado_en"])
    return negocio


def reactivar_negocio(*, negocio_id: int) -> Negocio:
    """Devuelve al negocio a la operación. Su gente vuelve a poder entrar.

    Raises:
        NegocioNoEncontrado, NegocioYaActivo.
    """
    negocio = obtener_negocio(negocio_id=negocio_id)
    if negocio.esta_operativo:
        raise NegocioYaActivo

    negocio.estado = Negocio.Estado.ACTIVO
    negocio.save(update_fields=["estado", "actualizado_en"])
    return negocio
