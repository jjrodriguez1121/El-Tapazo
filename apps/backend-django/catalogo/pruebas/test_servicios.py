"""Pruebas de las reglas del catálogo.

Aquí vive el negocio, así que es lo primero que se prueba. Se comprueba el
camino feliz **y** el que falla, porque es en el segundo donde están los bugs.
"""

from decimal import Decimal

import pytest

from catalogo.dtos import DatosDeProductoDTO
from catalogo.excepciones import (
    CategoriaDuplicada,
    FormatoSkuInvalido,
    NitDeProveedorDuplicado,
    ProveedorYaAsociado,
    SkuDuplicado,
)
from catalogo.pruebas.fabricas import FabricaDeCategoria, FabricaDeProducto, FabricaDeProveedor
from catalogo.servicios import categorias as servicio_de_categorias
from catalogo.servicios import ofertas as servicio_de_ofertas
from catalogo.servicios import productos as servicio
from catalogo.servicios import proveedores as servicio_de_proveedores
from nucleo.excepciones import NoEncontradoEnEsteNegocio

pytestmark = pytest.mark.django_db


def _datos(categoria, sku: str = "CER-001") -> DatosDeProductoDTO:
    return DatosDeProductoDTO(
        sku=sku,
        nombre="Cerveza Águila",
        categoria_id=categoria.id,
        costo=Decimal("2000.00"),
        precio_evento=Decimal("5000.00"),
        precio_mayorista=Decimal("3500.00"),
    )


# --------------------------------------------------------------------------- #
# Productos
# --------------------------------------------------------------------------- #
def test_crear_producto_normaliza_el_sku(negocio):
    categoria = FabricaDeCategoria(negocio=negocio)

    producto = servicio.crear_producto(
        negocio_id=negocio.id, datos=_datos(categoria, sku="  cer-001 ")
    )

    assert producto.sku == "CER-001"


def test_crear_producto_con_un_sku_que_no_cumple_el_formato_falla(negocio):
    categoria = FabricaDeCategoria(negocio=negocio)

    with pytest.raises(FormatoSkuInvalido):
        servicio.crear_producto(negocio_id=negocio.id, datos=_datos(categoria, sku="CERVEZA1"))


def test_no_se_repite_el_sku_dentro_del_mismo_negocio(negocio):
    categoria = FabricaDeCategoria(negocio=negocio)
    servicio.crear_producto(negocio_id=negocio.id, datos=_datos(categoria))

    with pytest.raises(SkuDuplicado):
        servicio.crear_producto(negocio_id=negocio.id, datos=_datos(categoria))


def test_dos_negocios_distintos_si_pueden_usar_el_mismo_sku(negocio):
    """ "CER-001" es de cada bar, no del mundo."""
    categoria_propia = FabricaDeCategoria(negocio=negocio)
    categoria_ajena = FabricaDeCategoria()

    servicio.crear_producto(negocio_id=negocio.id, datos=_datos(categoria_propia))
    ajeno = servicio.crear_producto(
        negocio_id=categoria_ajena.negocio_id, datos=_datos(categoria_ajena)
    )

    assert ajeno.sku == "CER-001"


def test_no_se_puede_colgar_un_producto_de_la_categoria_de_otro_negocio(negocio):
    """Mandando el id de una categoría ajena se colaría un producto atado a otro
    catálogo. La comprobación es la que lo impide."""
    categoria_ajena = FabricaDeCategoria()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        servicio.crear_producto(negocio_id=negocio.id, datos=_datos(categoria_ajena))


def test_actualizar_un_producto_deja_conservar_su_propio_sku(negocio):
    categoria = FabricaDeCategoria(negocio=negocio)
    producto = servicio.crear_producto(negocio_id=negocio.id, datos=_datos(categoria))

    actualizado = servicio.actualizar_producto(
        producto_id=producto.id, negocio_id=negocio.id, datos=_datos(categoria)
    )

    assert actualizado.sku == "CER-001"


def test_cambiar_precio_toca_solo_el_precio_que_se_manda(negocio, administrador):
    producto = FabricaDeProducto(
        negocio=negocio, precio_evento=Decimal("5000.00"), precio_mayorista=Decimal("3500.00")
    )

    servicio.cambiar_precio(
        producto_id=producto.id,
        negocio_id=negocio.id,
        usuario_id=administrador.id,
        precio_evento=Decimal("6000.00"),
    )

    producto.refresh_from_db()
    assert producto.precio_evento == Decimal("6000.00")
    assert producto.precio_mayorista == Decimal("3500.00")


def test_desactivar_un_producto_no_lo_borra(negocio):
    """Los pedidos históricos lo siguen nombrando."""
    producto = FabricaDeProducto(negocio=negocio)

    servicio.desactivar_producto(producto_id=producto.id, negocio_id=negocio.id)

    producto.refresh_from_db()
    assert producto.activo is False


def test_no_se_puede_tocar_un_producto_de_otro_negocio(negocio):
    ajeno = FabricaDeProducto()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        servicio.desactivar_producto(producto_id=ajeno.id, negocio_id=negocio.id)


# --------------------------------------------------------------------------- #
# Categorías y proveedores
# --------------------------------------------------------------------------- #
def test_no_se_repite_el_nombre_de_categoria_en_el_mismo_negocio(negocio):
    servicio_de_categorias.crear_categoria(negocio_id=negocio.id, nombre="Cervezas")

    with pytest.raises(CategoriaDuplicada):
        servicio_de_categorias.crear_categoria(negocio_id=negocio.id, nombre="cervezas")


def test_varios_proveedores_pueden_ir_sin_nit(negocio):
    """El NIT es opcional, y la restricción de la base es parcial por eso mismo."""
    servicio_de_proveedores.crear_proveedor(negocio_id=negocio.id, razon_social="Don Pepe")
    segundo = servicio_de_proveedores.crear_proveedor(
        negocio_id=negocio.id, razon_social="La Esquina"
    )

    assert segundo.nit == ""


def test_no_se_repite_el_nit_de_proveedor_en_el_mismo_negocio(negocio):
    servicio_de_proveedores.crear_proveedor(
        negocio_id=negocio.id, razon_social="Distribuidora", nit="900123456"
    )

    with pytest.raises(NitDeProveedorDuplicado):
        servicio_de_proveedores.crear_proveedor(
            negocio_id=negocio.id, razon_social="Otra", nit="900123456"
        )


# --------------------------------------------------------------------------- #
# Precios por proveedor
# --------------------------------------------------------------------------- #
def test_no_se_puede_asociar_el_proveedor_de_otro_negocio(negocio):
    producto = FabricaDeProducto(negocio=negocio)
    proveedor_ajeno = FabricaDeProveedor()

    with pytest.raises(NoEncontradoEnEsteNegocio):
        servicio_de_ofertas.asociar_proveedor_a_producto(
            producto_id=producto.id,
            proveedor_id=proveedor_ajeno.id,
            negocio_id=negocio.id,
            precio_compra=Decimal("1800.00"),
        )


def test_el_mismo_proveedor_no_se_registra_dos_veces_para_el_mismo_producto(negocio):
    producto = FabricaDeProducto(negocio=negocio)
    proveedor = FabricaDeProveedor(negocio=negocio)
    servicio_de_ofertas.asociar_proveedor_a_producto(
        producto_id=producto.id,
        proveedor_id=proveedor.id,
        negocio_id=negocio.id,
        precio_compra=Decimal("1800.00"),
    )

    with pytest.raises(ProveedorYaAsociado):
        servicio_de_ofertas.asociar_proveedor_a_producto(
            producto_id=producto.id,
            proveedor_id=proveedor.id,
            negocio_id=negocio.id,
            precio_compra=Decimal("1700.00"),
        )


def test_marcar_un_proveedor_principal_le_quita_el_puesto_al_anterior(negocio):
    """El caso con truco: la base solo admite un principal por producto, así que
    quitar el viejo y poner el nuevo tienen que pasar en la misma transacción."""
    producto = FabricaDeProducto(negocio=negocio)
    habitual = FabricaDeProveedor(negocio=negocio)
    nuevo = FabricaDeProveedor(negocio=negocio)

    primera = servicio_de_ofertas.asociar_proveedor_a_producto(
        producto_id=producto.id,
        proveedor_id=habitual.id,
        negocio_id=negocio.id,
        precio_compra=Decimal("1800.00"),
        es_principal=True,
    )
    servicio_de_ofertas.asociar_proveedor_a_producto(
        producto_id=producto.id,
        proveedor_id=nuevo.id,
        negocio_id=negocio.id,
        precio_compra=Decimal("1700.00"),
    )

    segunda = servicio_de_ofertas.marcar_proveedor_principal(
        producto_id=producto.id, proveedor_id=nuevo.id, negocio_id=negocio.id
    )

    primera.refresh_from_db()
    assert segunda.es_principal is True
    assert primera.es_principal is False


def test_asociar_un_principal_nuevo_destrona_al_anterior(negocio):
    producto = FabricaDeProducto(negocio=negocio)
    habitual = FabricaDeProveedor(negocio=negocio)
    otro = FabricaDeProveedor(negocio=negocio)

    primera = servicio_de_ofertas.asociar_proveedor_a_producto(
        producto_id=producto.id,
        proveedor_id=habitual.id,
        negocio_id=negocio.id,
        precio_compra=Decimal("1800.00"),
        es_principal=True,
    )
    servicio_de_ofertas.asociar_proveedor_a_producto(
        producto_id=producto.id,
        proveedor_id=otro.id,
        negocio_id=negocio.id,
        precio_compra=Decimal("1700.00"),
        es_principal=True,
    )

    primera.refresh_from_db()
    assert primera.es_principal is False


def test_desasociar_quita_el_precio_de_ese_proveedor(negocio):
    producto = FabricaDeProducto(negocio=negocio)
    proveedor = FabricaDeProveedor(negocio=negocio)
    servicio_de_ofertas.asociar_proveedor_a_producto(
        producto_id=producto.id,
        proveedor_id=proveedor.id,
        negocio_id=negocio.id,
        precio_compra=Decimal("1800.00"),
    )

    servicio_de_ofertas.desasociar_proveedor(
        producto_id=producto.id, proveedor_id=proveedor.id, negocio_id=negocio.id
    )

    assert producto.ofertas_de_proveedor.count() == 0
