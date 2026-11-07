"""Lecturas de fichas de cliente."""

from django.db.models import QuerySet

from clientes.models import Cliente
from clientes.repositorios import clientes as repositorio
from nucleo.excepciones import NoEncontradoEnEsteNegocio


def clientes_del_negocio(*, negocio_id: int) -> QuerySet[Cliente]:
    """Las fichas de un negocio, por apellido.

    Aprovecha el índice `cliente_negocio_nombre_idx`, que es el que hace rápida
    la búsqueda de la barra: buscar a alguien por su nombre es el caso de uso
    diario.
    """
    return repositorio.del_negocio(negocio_id=negocio_id)


def obtener_cliente(*, cliente_id: int, negocio_id: int) -> Cliente:
    """Raises: NoEncontradoEnEsteNegocio: no existe, o es de otro negocio."""
    cliente = repositorio.obtener_del_negocio(cliente_id=cliente_id, negocio_id=negocio_id)
    if cliente is None:
        raise NoEncontradoEnEsteNegocio
    return cliente


def buscar_por_documento(*, negocio_id: int, tipo_documento: str, numero_documento: str) -> Cliente:
    """La ficha de quien enseña su documento en la barra.

    Es la consulta que evita el "Juan", "Juan P" y "Juan Perez" como tres
    personas: antes de crear una ficha nueva se busca por documento.

    Raises:
        NoEncontradoEnEsteNegocio: nadie con ese documento en este negocio.
    """
    cliente = repositorio.obtener_por_documento(
        negocio_id=negocio_id,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento.strip(),
    )
    if cliente is None:
        raise NoEncontradoEnEsteNegocio
    return cliente
