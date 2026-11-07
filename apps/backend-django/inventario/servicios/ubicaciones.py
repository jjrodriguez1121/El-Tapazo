"""Alta y cambio de ubicaciones, y el punto de reposición de cada existencia."""

from decimal import Decimal

from inventario.excepciones import CantidadInvalida
from inventario.models import Existencia, Ubicacion
from inventario.repositorios import existencias as repositorio_de_existencias
from inventario.repositorios import ubicaciones as repositorio
from nucleo.excepciones import NoEncontradoEnEsteNegocio


def crear_ubicacion(*, negocio_id: int, nombre: str, tipo: str, direccion: str = "") -> Ubicacion:
    """Registra una bodega o un punto de venta.

    Raises:
        CantidadInvalida: ya hay una ubicación con ese nombre.
    """
    nombre = nombre.strip()
    if repositorio.existe_nombre(negocio_id=negocio_id, nombre=nombre):
        raise CantidadInvalida("Ya existe una ubicación con ese nombre en este negocio.")
    return repositorio.crear(
        negocio_id=negocio_id, nombre=nombre, tipo=tipo, direccion=direccion.strip()
    )


def actualizar_ubicacion(
    *, ubicacion_id: int, negocio_id: int, nombre: str, tipo: str, direccion: str = ""
) -> Ubicacion:
    """Raises: NoEncontradoEnEsteNegocio, CantidadInvalida."""
    ubicacion = obtener_ubicacion(ubicacion_id=ubicacion_id, negocio_id=negocio_id)
    nombre = nombre.strip()
    if repositorio.existe_nombre(negocio_id=negocio_id, nombre=nombre, excluyendo_id=ubicacion_id):
        raise CantidadInvalida("Ya existe una ubicación con ese nombre en este negocio.")

    ubicacion.nombre = nombre
    ubicacion.tipo = tipo
    ubicacion.direccion = direccion.strip()
    ubicacion.save(update_fields=["nombre", "tipo", "direccion", "actualizado_en"])
    return ubicacion


def desactivar_ubicacion(*, ubicacion_id: int, negocio_id: int) -> Ubicacion:
    """Deja de aparecer para mover mercancía, sin borrar el kardex que la nombra.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    ubicacion = obtener_ubicacion(ubicacion_id=ubicacion_id, negocio_id=negocio_id)
    ubicacion.activa = False
    ubicacion.save(update_fields=["activa", "actualizado_en"])
    return ubicacion


def fijar_cantidad_minima(
    *, producto_id: int, ubicacion_id: int, negocio_id: int, cantidad_minima: Decimal
) -> Existencia:
    """Pone el punto de reposición de un producto **en un sitio concreto**.

    Es por ubicación y no por producto porque el punto real es distinto en cada
    sitio: veinte cervezas en la barra es alerta y en la bodega no. Un cero
    significa "sin alerta", no "alerta siempre".

    Raises:
        CantidadInvalida: la cantidad es negativa.
        NoEncontradoEnEsteNegocio: ese producto no tiene existencias ahí.
    """
    if cantidad_minima < 0:
        raise CantidadInvalida("La cantidad mínima no puede ser negativa.")

    existencia = repositorio_de_existencias.obtener(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    )
    if existencia is None:
        raise NoEncontradoEnEsteNegocio
    repositorio_de_existencias.fijar_cantidad_minima(
        existencia_id=existencia.id, cantidad_minima=cantidad_minima
    )
    existencia.refresh_from_db()
    return existencia


def obtener_ubicacion(*, ubicacion_id: int, negocio_id: int) -> Ubicacion:
    """Raises: NoEncontradoEnEsteNegocio."""
    ubicacion = repositorio.obtener_del_negocio(ubicacion_id=ubicacion_id, negocio_id=negocio_id)
    if ubicacion is None:
        raise NoEncontradoEnEsteNegocio
    return ubicacion
