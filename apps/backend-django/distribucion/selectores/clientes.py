"""Lecturas de las tiendas cliente."""

from django.db.models import QuerySet

from distribucion.models import ClienteDistribucion
from distribucion.repositorios import clientes as repositorio
from nucleo.excepciones import NoEncontradoEnEsteNegocio


def clientes_del_negocio(*, negocio_id: int) -> QuerySet[ClienteDistribucion]:
    """Las tiendas a las que este negocio le vende al por mayor."""
    return repositorio.del_negocio(negocio_id=negocio_id)


def obtener_cliente(*, cliente_id: int, negocio_id: int) -> ClienteDistribucion:
    """Raises: NoEncontradoEnEsteNegocio: no existe, o es de otro negocio."""
    cliente = repositorio.obtener_del_negocio(cliente_id=cliente_id, negocio_id=negocio_id)
    if cliente is None:
        raise NoEncontradoEnEsteNegocio
    return cliente


def clientes_en_mora(*, negocio_id: int) -> QuerySet[ClienteDistribucion]:
    """A quién hay que cobrarle: se le pasó el plazo y todavía debe.

    Es el caso de uso por el que existe `dias_credito`. Cada fila trae
    `deuda_vencida`, que es lo vencido **y no lo que la tienda debe en total**:
    un pedido de ayer a 30 días no es mora, es crédito corriente.
    """
    return repositorio.en_mora(negocio_id=negocio_id).order_by("razon_social")
