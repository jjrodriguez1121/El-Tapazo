"""Alta, cambio y baja de categorías."""

from catalogo.excepciones import CategoriaDuplicada
from catalogo.models import Categoria
from catalogo.repositorios import categorias as repositorio
from catalogo.selectores import obtener_categoria


def crear_categoria(*, negocio_id: int, nombre: str, descripcion: str = "") -> Categoria:
    """Registra una clasificación de productos.

    Raises:
        CategoriaDuplicada: ya hay una con ese nombre en el negocio.
    """
    nombre = nombre.strip()
    if repositorio.existe_nombre(negocio_id=negocio_id, nombre=nombre):
        raise CategoriaDuplicada
    return repositorio.crear(negocio_id=negocio_id, nombre=nombre, descripcion=descripcion.strip())


def actualizar_categoria(
    *, categoria_id: int, negocio_id: int, nombre: str, descripcion: str = ""
) -> Categoria:
    """Renombra una categoría. El nombre nuevo tampoco puede chocar.

    Raises:
        NoEncontradoEnEsteNegocio, CategoriaDuplicada.
    """
    categoria = obtener_categoria(categoria_id=categoria_id, negocio_id=negocio_id)
    nombre = nombre.strip()
    if repositorio.existe_nombre(negocio_id=negocio_id, nombre=nombre, excluyendo_id=categoria_id):
        raise CategoriaDuplicada

    categoria.nombre = nombre
    categoria.descripcion = descripcion.strip()
    categoria.save(update_fields=["nombre", "descripcion", "actualizado_en"])
    return categoria


def desactivar_categoria(*, categoria_id: int, negocio_id: int) -> Categoria:
    """La saca del catálogo sin borrarla: los productos viejos la siguen usando.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    categoria = obtener_categoria(categoria_id=categoria_id, negocio_id=negocio_id)
    categoria.activa = False
    categoria.save(update_fields=["activa", "actualizado_en"])
    return categoria
