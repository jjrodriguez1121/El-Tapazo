"""Consultas al ORM sobre `categorias`. Ningún otro sitio escribe `Categoria.objects`."""

from django.db.models import QuerySet

from catalogo.models import Categoria


def obtener_del_negocio(*, categoria_id: int, negocio_id: int) -> Categoria | None:
    """Una categoría, siempre acotada al negocio de quien pregunta.

    Filtrar también por `negocio_id` es lo que evita que alguien lea o toque
    la categoría de otro negocio cambiando el id de la URL.
    """
    return Categoria.objects.filter(pk=categoria_id, negocio_id=negocio_id).first()


def del_negocio(*, negocio_id: int) -> QuerySet[Categoria]:
    return Categoria.objects.filter(negocio_id=negocio_id)


def existe_nombre(*, negocio_id: int, nombre: str, excluyendo_id: int | None = None) -> bool:
    """Si ya hay una categoría con ese nombre. `excluyendo_id` es para el renombrado."""
    consulta = Categoria.objects.filter(negocio_id=negocio_id, nombre__iexact=nombre)
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def crear(*, negocio_id: int, nombre: str, descripcion: str) -> Categoria:
    return Categoria.objects.create(negocio_id=negocio_id, nombre=nombre, descripcion=descripcion)
