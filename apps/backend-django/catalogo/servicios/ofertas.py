"""Qué proveedor vende qué producto, y a cuánto.

Es lo que hace comparable el precio antes de reponer. Un producto puede tener
varios proveedores y como mucho **uno habitual**.
"""

from decimal import Decimal

from django.db import transaction

from catalogo.excepciones import ProveedorYaAsociado
from catalogo.models import ProductoProveedor
from catalogo.repositorios import ofertas as repositorio
from catalogo.selectores import obtener_producto, obtener_proveedor
from nucleo.excepciones import NoEncontradoEnEsteNegocio


@transaction.atomic
def asociar_proveedor_a_producto(
    *,
    producto_id: int,
    proveedor_id: int,
    negocio_id: int,
    precio_compra: Decimal,
    codigo_proveedor: str = "",
    es_principal: bool = False,
) -> ProductoProveedor:
    """Registra a cuánto le vende este proveedor este producto.

    Los dos se comprueban contra el mismo negocio: es lo que impide atar un
    producto propio al proveedor de otro mandando su id.

    Raises:
        NoEncontradoEnEsteNegocio: el producto o el proveedor no son de aquí.
        ProveedorYaAsociado: ese par ya está registrado.
    """
    producto = obtener_producto(producto_id=producto_id, negocio_id=negocio_id)
    proveedor = obtener_proveedor(proveedor_id=proveedor_id, negocio_id=negocio_id)
    if repositorio.existe(producto_id=producto.id, proveedor_id=proveedor.id):
        raise ProveedorYaAsociado

    if es_principal:
        # Antes de poner el nuevo hay que quitar el viejo, o la restricción
        # parcial `producto_con_un_solo_proveedor_principal` lo rechaza.
        repositorio.quitar_principal(producto_id=producto.id)

    return repositorio.crear(
        negocio_id=negocio_id,
        producto_id=producto.id,
        proveedor_id=proveedor.id,
        precio_compra=precio_compra,
        codigo_proveedor=codigo_proveedor.strip(),
        es_principal=es_principal,
    )


@transaction.atomic
def marcar_proveedor_principal(
    *, producto_id: int, proveedor_id: int, negocio_id: int
) -> ProductoProveedor:
    """Deja a este proveedor como el habitual del producto.

    Los dos pasos van en la misma transacción **a propósito**: la base solo
    admite un principal por producto, así que quitar el anterior y poner el
    nuevo tienen que pasar juntos o no pasar.

    Raises:
        NoEncontradoEnEsteNegocio: ese proveedor no está registrado para ese
            producto, o alguno de los dos es de otro negocio.
    """
    oferta = _obtener_oferta(
        producto_id=producto_id, proveedor_id=proveedor_id, negocio_id=negocio_id
    )
    if oferta.es_principal:
        return oferta

    repositorio.quitar_principal(producto_id=oferta.producto_id)
    oferta.es_principal = True
    oferta.save(update_fields=["es_principal", "actualizado_en"])
    return oferta


def desasociar_proveedor(*, producto_id: int, proveedor_id: int, negocio_id: int) -> None:
    """Quita el precio de ese proveedor para ese producto.

    Aquí sí se borra la fila, y es coherente con "nada se borra": esta tabla no
    es historia de ninguna compra —eso lo guarda el kardex— sino la lista de a
    quién se le puede comprar hoy.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    oferta = _obtener_oferta(
        producto_id=producto_id, proveedor_id=proveedor_id, negocio_id=negocio_id
    )
    oferta.delete()


def _obtener_oferta(*, producto_id: int, proveedor_id: int, negocio_id: int) -> ProductoProveedor:
    oferta = repositorio.obtener(
        producto_id=producto_id, proveedor_id=proveedor_id, negocio_id=negocio_id
    )
    if oferta is None:
        raise NoEncontradoEnEsteNegocio
    return oferta
