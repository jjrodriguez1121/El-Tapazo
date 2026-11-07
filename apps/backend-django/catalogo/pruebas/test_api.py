"""Pruebas de los endpoints del catálogo.

Lo de siempre: código de estado, forma del JSON, permisos y —lo que más
importa en esta plataforma— que un negocio no vea ni toque los del otro.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from catalogo.pruebas.fabricas import FabricaDeCategoria, FabricaDeProducto, FabricaDeProveedor

pytestmark = pytest.mark.django_db

URL_PRODUCTOS = reverse("catalogo:producto-list")
URL_CATEGORIAS = reverse("catalogo:categoria-list")
URL_PROVEEDORES = reverse("catalogo:proveedor-list")


def _url_producto(producto_id: int) -> str:
    return reverse("catalogo:producto-detail", args=[producto_id])


# --------------------------------------------------------------------------- #
# Permisos
# --------------------------------------------------------------------------- #
def test_sin_iniciar_sesion_no_se_ve_el_catalogo(cliente_api):
    respuesta = cliente_api.get(URL_PRODUCTOS)

    assert respuesta.status_code == 401
    assert respuesta.data["error"]["codigo"] == "no_autenticado"


def test_un_mesero_no_entra_al_catalogo(cliente_api_autenticado, mesero):
    """El catálogo es de administrador: cambia lo que el resto del equipo ve."""
    respuesta = cliente_api_autenticado(mesero).get(URL_PRODUCTOS)

    assert respuesta.status_code == 403
    assert respuesta.data["error"]["codigo"] == "sin_permiso"


def test_un_cajero_tampoco(cliente_api_autenticado, cajero):
    respuesta = cliente_api_autenticado(cajero).get(URL_PRODUCTOS)

    assert respuesta.status_code == 403


# --------------------------------------------------------------------------- #
# Aislamiento entre negocios
# --------------------------------------------------------------------------- #
def test_el_listado_solo_trae_los_productos_del_negocio(
    cliente_api_autenticado, administrador, negocio
):
    FabricaDeProducto.create_batch(2, negocio=negocio)
    FabricaDeProducto()  # de otro negocio

    respuesta = cliente_api_autenticado(administrador).get(URL_PRODUCTOS)

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 2


def test_pedir_un_producto_de_otro_negocio_devuelve_404_y_no_403(
    cliente_api_autenticado, administrador
):
    """Decir «existe pero no es tuyo» ya sería contar de más."""
    ajeno = FabricaDeProducto()

    respuesta = cliente_api_autenticado(administrador).get(_url_producto(ajeno.id))

    assert respuesta.status_code == 404


def test_desactivar_un_producto_de_otro_negocio_devuelve_404(
    cliente_api_autenticado, administrador
):
    ajeno = FabricaDeProducto()

    respuesta = cliente_api_autenticado(administrador).post(
        reverse("catalogo:producto-desactivacion", args=[ajeno.id])
    )

    assert respuesta.status_code == 404
    ajeno.refresh_from_db()
    assert ajeno.activo is True


# --------------------------------------------------------------------------- #
# Productos
# --------------------------------------------------------------------------- #
def test_crear_un_producto_devuelve_201_con_su_categoria(
    cliente_api_autenticado, administrador, negocio
):
    categoria = FabricaDeCategoria(negocio=negocio)

    respuesta = cliente_api_autenticado(administrador).post(
        URL_PRODUCTOS,
        {
            "sku": "cer-001",
            "nombre": "Cerveza Águila",
            "categoria_id": categoria.id,
            "costo": "2000.00",
            "precio_evento": "5000.00",
            "precio_mayorista": "3500.00",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["sku"] == "CER-001"
    assert respuesta.data["categoria"]["nombre"] == categoria.nombre


def test_crear_un_producto_con_sku_mal_formado_devuelve_400(
    cliente_api_autenticado, administrador, negocio
):
    categoria = FabricaDeCategoria(negocio=negocio)

    respuesta = cliente_api_autenticado(administrador).post(
        URL_PRODUCTOS,
        {
            "sku": "CERVEZA",
            "nombre": "Cerveza",
            "categoria_id": categoria.id,
            "costo": "2000.00",
            "precio_evento": "5000.00",
            "precio_mayorista": "3500.00",
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "formato_sku_invalido"


def test_el_sku_repetido_devuelve_409(cliente_api_autenticado, administrador, negocio):
    categoria = FabricaDeCategoria(negocio=negocio)
    FabricaDeProducto(negocio=negocio, categoria=categoria, sku="CER-001")

    respuesta = cliente_api_autenticado(administrador).post(
        URL_PRODUCTOS,
        {
            "sku": "CER-001",
            "nombre": "Otra",
            "categoria_id": categoria.id,
            "costo": "2000.00",
            "precio_evento": "5000.00",
            "precio_mayorista": "3500.00",
        },
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "sku_duplicado"


def test_cambiar_el_precio_devuelve_el_producto_ya_cambiado(
    cliente_api_autenticado, administrador, negocio
):
    producto = FabricaDeProducto(negocio=negocio, precio_evento=Decimal("5000.00"))

    respuesta = cliente_api_autenticado(administrador).post(
        reverse("catalogo:producto-precio", args=[producto.id]),
        {"precio_evento": "6000.00"},
        format="json",
    )

    assert respuesta.status_code == 200
    assert respuesta.data["precio_evento"] == "6000.00"


def test_el_cuerpo_vacio_no_es_un_cambio_de_precio(cliente_api_autenticado, administrador, negocio):
    producto = FabricaDeProducto(negocio=negocio)

    respuesta = cliente_api_autenticado(administrador).post(
        reverse("catalogo:producto-precio", args=[producto.id]), {}, format="json"
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "datos_invalidos"


def test_el_margen_es_nulo_cuando_el_costo_es_cero(cliente_api_autenticado, administrador, negocio):
    """Sin costo no hay margen: contestar 0 % sería inventárselo."""
    producto = FabricaDeProducto(
        negocio=negocio, costo=Decimal("0.00"), precio_evento=Decimal("5000.00")
    )

    respuesta = cliente_api_autenticado(administrador).get(
        reverse("catalogo:producto-margen", args=[producto.id])
    )

    assert respuesta.status_code == 200
    assert respuesta.data["margen_evento"] is None


def test_el_margen_sale_en_porcentaje_sobre_el_costo(
    cliente_api_autenticado, administrador, negocio
):
    producto = FabricaDeProducto(
        negocio=negocio, costo=Decimal("2000.00"), precio_evento=Decimal("5000.00")
    )

    respuesta = cliente_api_autenticado(administrador).get(
        reverse("catalogo:producto-margen", args=[producto.id])
    )

    assert respuesta.data["margen_evento"] == "150.00"


def test_la_busqueda_mira_el_nombre_y_el_sku(cliente_api_autenticado, administrador, negocio):
    FabricaDeProducto(negocio=negocio, nombre="Cerveza Águila", sku="CER-001")
    FabricaDeProducto(negocio=negocio, nombre="Ron Viejo", sku="RON-001")

    respuesta = cliente_api_autenticado(administrador).get(URL_PRODUCTOS, {"busqueda": "RON"})

    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["nombre"] == "Ron Viejo"


def test_comparar_precios_de_proveedores_sale_del_mas_barato_al_mas_caro(
    cliente_api_autenticado, administrador, negocio
):
    producto = FabricaDeProducto(negocio=negocio)
    caro = FabricaDeProveedor(negocio=negocio)
    barato = FabricaDeProveedor(negocio=negocio)
    url = reverse("catalogo:producto-proveedores", args=[producto.id])
    cliente = cliente_api_autenticado(administrador)
    cliente.post(url, {"proveedor_id": caro.id, "precio_compra": "1900.00"}, format="json")
    cliente.post(url, {"proveedor_id": barato.id, "precio_compra": "1700.00"}, format="json")

    respuesta = cliente.get(url)

    assert respuesta.status_code == 200
    assert [oferta["precio_compra"] for oferta in respuesta.data] == ["1700.00", "1900.00"]


# --------------------------------------------------------------------------- #
# Categorías y proveedores
# --------------------------------------------------------------------------- #
def test_crear_una_categoria_devuelve_201(cliente_api_autenticado, administrador):
    respuesta = cliente_api_autenticado(administrador).post(
        URL_CATEGORIAS, {"nombre": "Cervezas"}, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["nombre"] == "Cervezas"


def test_la_categoria_repetida_devuelve_409(cliente_api_autenticado, administrador, negocio):
    FabricaDeCategoria(negocio=negocio, nombre="Cervezas")

    respuesta = cliente_api_autenticado(administrador).post(
        URL_CATEGORIAS, {"nombre": "Cervezas"}, format="json"
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "categoria_duplicada"


def test_registrar_un_proveedor_devuelve_201(cliente_api_autenticado, administrador):
    respuesta = cliente_api_autenticado(administrador).post(
        URL_PROVEEDORES, {"razon_social": "Distribuidora S.A.S.", "nit": "900123456"}, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["razon_social"] == "Distribuidora S.A.S."
