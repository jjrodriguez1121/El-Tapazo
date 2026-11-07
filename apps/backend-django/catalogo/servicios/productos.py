"""Alta, cambio de precio y baja de productos."""

import logging
from decimal import Decimal

from django.db import transaction

from catalogo.dtos import DatosDeProductoDTO
from catalogo.excepciones import SkuDuplicado
from catalogo.models import Producto
from catalogo.repositorios import productos as repositorio
from catalogo.selectores import obtener_categoria, obtener_producto
from catalogo.validadores import normalizar_sku, validar_formato_sku

logger = logging.getLogger(__name__)


@transaction.atomic
def crear_producto(*, negocio_id: int, datos: DatosDeProductoDTO) -> Producto:
    """Registra un producto en el catálogo del negocio.

    La categoría se comprueba contra el mismo negocio: sin eso, mandando el id
    de una categoría ajena se colaría un producto atado al catálogo de otro.

    Raises:
        FormatoSkuInvalido, SkuDuplicado.
        NoEncontradoEnEsteNegocio: la categoría no es de este negocio.
    """
    sku = normalizar_sku(datos.sku)
    validar_formato_sku(sku)
    if repositorio.existe_sku(negocio_id=negocio_id, sku=sku):
        raise SkuDuplicado(sku=sku)

    categoria = obtener_categoria(categoria_id=datos.categoria_id, negocio_id=negocio_id)
    return repositorio.crear(
        negocio_id=negocio_id,
        sku=sku,
        nombre=datos.nombre.strip(),
        categoria_id=categoria.id,
        costo=datos.costo,
        precio_evento=datos.precio_evento,
        precio_mayorista=datos.precio_mayorista,
    )


@transaction.atomic
def actualizar_producto(
    *, producto_id: int, negocio_id: int, datos: DatosDeProductoDTO
) -> Producto:
    """Cambia todos los datos del producto, precios incluidos.

    Raises:
        NoEncontradoEnEsteNegocio, FormatoSkuInvalido, SkuDuplicado.
    """
    producto = obtener_producto(producto_id=producto_id, negocio_id=negocio_id)
    sku = normalizar_sku(datos.sku)
    validar_formato_sku(sku)
    if repositorio.existe_sku(negocio_id=negocio_id, sku=sku, excluyendo_id=producto_id):
        raise SkuDuplicado(sku=sku)

    categoria = obtener_categoria(categoria_id=datos.categoria_id, negocio_id=negocio_id)
    producto.sku = sku
    producto.nombre = datos.nombre.strip()
    producto.categoria = categoria
    producto.costo = datos.costo
    producto.precio_evento = datos.precio_evento
    producto.precio_mayorista = datos.precio_mayorista
    producto.save(
        update_fields=[
            "sku",
            "nombre",
            "categoria",
            "costo",
            "precio_evento",
            "precio_mayorista",
            "actualizado_en",
        ]
    )
    return producto


def cambiar_precio(
    *,
    producto_id: int,
    negocio_id: int,
    usuario_id: int,
    precio_evento: Decimal | None = None,
    precio_mayorista: Decimal | None = None,
) -> Producto:
    """Cambia uno de los dos precios de venta, o los dos, dejando rastro de quién.

    Es un servicio aparte de `actualizar_producto` porque cambiar un precio es
    otra cosa que corregir un nombre: es lo que se revisa cuando la caja no
    cuadra, y por eso lleva autoría.

    **La autoría queda en el log, no en la base.** `productos` no tiene columna
    de quién tocó el precio, y añadirla no bastaría: guardaría solo el último
    cambio, no la historia. Lo que hace falta es la bitácora de auditoría que
    `diseno_base_datos.md` §6.4 deja pendiente. Mientras tanto, esto deja el
    rastro en los logs del servidor, que **no es consultable desde la
    aplicación**.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    producto = obtener_producto(producto_id=producto_id, negocio_id=negocio_id)
    cambios: dict[str, Decimal] = {}
    if precio_evento is not None:
        cambios["precio_evento"] = precio_evento
    if precio_mayorista is not None:
        cambios["precio_mayorista"] = precio_mayorista
    if not cambios:
        return producto

    anteriores = {campo: getattr(producto, campo) for campo in cambios}
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)
    producto.save(update_fields=[*cambios, "actualizado_en"])

    logger.info(
        "Cambio de precio · producto=%s negocio=%s usuario=%s antes=%s despues=%s",
        producto.sku,
        negocio_id,
        usuario_id,
        anteriores,
        cambios,
    )
    return producto


def desactivar_producto(*, producto_id: int, negocio_id: int) -> Producto:
    """Lo saca del catálogo sin borrarlo: los pedidos viejos lo siguen nombrando.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    producto = obtener_producto(producto_id=producto_id, negocio_id=negocio_id)
    producto.activo = False
    producto.save(update_fields=["activo", "actualizado_en"])
    return producto
