"""Pruebas de los endpoints del canal mayorista.

Lo propio de esta app son dos cosas: que **todo sea de administrador** —el
mayoreo mueve crédito y bodega, no la operación de una noche— y el recorrido
completo de un pedido, que es donde se ve que el stock sale al despachar y
vuelve al no poder entregar.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from catalogo.pruebas.fabricas import FabricaDeProducto
from distribucion.models import PedidoDistribucion
from distribucion.pruebas.fabricas import FabricaDeClienteDistribucion
from inventario.models import Existencia
from inventario.pruebas.fabricas import FabricaDeExistencia

pytestmark = pytest.mark.django_db

URL_CLIENTES = reverse("distribucion:cliente-list")
URL_MORA = reverse("distribucion:cliente-mora")
URL_PEDIDOS = reverse("distribucion:pedido-list")

DATOS_DE_TIENDA = {
    "razon_social": "Tienda La Esquina",
    "nit": "900123456",
    "ciudad": "Medellín",
    "dias_credito": 30,
}


@pytest.fixture
def bodega(negocio):
    return FabricaDeExistencia(
        negocio=negocio,
        cantidad_disponible=Decimal("100.00"),
        producto=FabricaDeProducto(negocio=negocio, precio_mayorista=Decimal("3500.00")),
    )


@pytest.fixture
def tienda(negocio):
    return FabricaDeClienteDistribucion(negocio=negocio, dias_credito=30)


def _url(nombre: str, pedido_id: int) -> str:
    return reverse(f"distribucion:pedido-{nombre}", args=[pedido_id])


def _tomar_pedido(cliente, tienda, bodega, cantidad="10.00"):
    return cliente.post(
        URL_PEDIDOS,
        {
            "cliente_distribucion_id": tienda.id,
            "lineas": [{"producto_id": bodega.producto_id, "cantidad": cantidad}],
        },
        format="json",
    )


def _disponible(bodega) -> Decimal:
    return Existencia.objects.get(pk=bodega.pk).cantidad_disponible


# --------------------------------------------------------------------------- #
# Permisos: el mayoreo es de administrador
# --------------------------------------------------------------------------- #
def test_sin_autenticar_no_se_ve_nada(cliente_api):
    assert cliente_api.get(URL_CLIENTES).status_code == 401
    assert cliente_api.get(URL_PEDIDOS).status_code == 401


def test_el_cajero_no_entra_al_mayoreo(cliente_api_autenticado, cajero):
    respuesta = cliente_api_autenticado(cajero).get(URL_CLIENTES)

    assert respuesta.status_code == 403


def test_el_mesero_no_toma_pedidos_mayoristas(cliente_api_autenticado, mesero, tienda, bodega):
    respuesta = _tomar_pedido(cliente_api_autenticado(mesero), tienda, bodega)

    assert respuesta.status_code == 403


def test_el_administrador_lista_las_tiendas(cliente_api_autenticado, administrador, tienda):
    respuesta = cliente_api_autenticado(administrador).get(URL_CLIENTES)

    assert respuesta.status_code == 200
    assert len(respuesta.data["results"]) == 1


# --------------------------------------------------------------------------- #
# Tiendas cliente
# --------------------------------------------------------------------------- #
def test_dar_de_alta_una_tienda(cliente_api_autenticado, administrador):
    respuesta = cliente_api_autenticado(administrador).post(
        URL_CLIENTES, DATOS_DE_TIENDA, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["nit"] == "900123456"
    assert respuesta.data["paga_de_contado"] is False


def test_repetir_el_nit_devuelve_409(cliente_api_autenticado, administrador):
    cliente = cliente_api_autenticado(administrador)
    cliente.post(URL_CLIENTES, DATOS_DE_TIENDA, format="json")

    respuesta = cliente.post(URL_CLIENTES, DATOS_DE_TIENDA, format="json")

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "nit_duplicado"


def test_no_se_ve_la_tienda_de_otro_negocio(cliente_api_autenticado, administrador):
    ajena = FabricaDeClienteDistribucion()

    respuesta = cliente_api_autenticado(administrador).get(
        reverse("distribucion:cliente-detail", args=[ajena.id])
    )

    assert respuesta.status_code == 404


# --------------------------------------------------------------------------- #
# El recorrido mayorista completo
# --------------------------------------------------------------------------- #
def test_el_recorrido_mayorista(cliente_api_autenticado, administrador, tienda, bodega):
    """Pedir → despachar → no entregar → volver a despachar → entregar → abonar."""
    cliente = cliente_api_autenticado(administrador)

    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]
    assert _disponible(bodega) == Decimal("100.00")

    cliente.post(_url("despacho", pedido_id), {"ubicacion_id": bodega.ubicacion_id})
    assert _disponible(bodega) == Decimal("90.00")

    cliente.post(_url("no-entrega", pedido_id), {"motivo": "La tienda estaba cerrada."})
    assert _disponible(bodega) == Decimal("100.00")

    cliente.post(_url("despacho", pedido_id), {"ubicacion_id": bodega.ubicacion_id})
    assert _disponible(bodega) == Decimal("90.00")

    entrega = cliente.post(_url("entrega", pedido_id))
    assert entrega.data["estado"] == PedidoDistribucion.Estado.ENTREGADO

    primero = cliente.post(_url("abonos", pedido_id), {"monto": "20000.00", "metodo": "nequi"})
    segundo = cliente.post(_url("abonos", pedido_id), {"monto": "15000.00", "metodo": "efectivo"})

    assert primero.status_code == 201
    assert primero.data["saldo"] == "15000.00"
    assert segundo.data["saldo"] == "0.00"


def test_despachar_sin_stock_devuelve_409_y_no_mueve_el_pedido(
    cliente_api_autenticado, administrador, tienda, bodega
):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega, cantidad="500.00").data["id"]

    respuesta = cliente.post(_url("despacho", pedido_id), {"ubicacion_id": bodega.ubicacion_id})

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "existencias_insuficientes"
    assert PedidoDistribucion.objects.get(pk=pedido_id).estado == (
        PedidoDistribucion.Estado.PENDIENTE
    )


def test_no_entregar_sin_motivo_devuelve_400(
    cliente_api_autenticado, administrador, tienda, bodega
):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]
    cliente.post(_url("despacho", pedido_id), {"ubicacion_id": bodega.ubicacion_id})

    respuesta = cliente.post(_url("no-entrega", pedido_id), {})

    assert respuesta.status_code == 400


def test_cancelar_en_ruta_devuelve_409_y_dice_que_hacer(
    cliente_api_autenticado, administrador, tienda, bodega
):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]
    cliente.post(_url("despacho", pedido_id), {"ubicacion_id": bodega.ubicacion_id})

    respuesta = cliente.post(_url("cancelacion", pedido_id))

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "pedido_no_cancelable"
    assert "no entregado" in respuesta.data["error"]["mensaje"]


def test_un_abono_de_mas_devuelve_409(cliente_api_autenticado, administrador, tienda, bodega):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]

    respuesta = cliente.post(_url("abonos", pedido_id), {"monto": "40000.00", "metodo": "efectivo"})

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "pago_supera_el_total"


def test_el_saldo_del_pedido_se_consulta(cliente_api_autenticado, administrador, tienda, bodega):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]
    cliente.post(_url("abonos", pedido_id), {"monto": "10000.00", "metodo": "efectivo"})

    respuesta = cliente.get(_url("saldo", pedido_id))

    assert respuesta.status_code == 200
    assert respuesta.data["total"] == "35000.00"
    assert respuesta.data["saldo"] == "25000.00"


def test_los_pedidos_se_filtran_por_estado(cliente_api_autenticado, administrador, tienda, bodega):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]
    _tomar_pedido(cliente, tienda, bodega)
    cliente.post(_url("despacho", pedido_id), {"ubicacion_id": bodega.ubicacion_id})

    respuesta = cliente.get(URL_PEDIDOS, {"estado": PedidoDistribucion.Estado.EN_RUTA})

    assert [pedido["id"] for pedido in respuesta.data["results"]] == [pedido_id]


# --------------------------------------------------------------------------- #
# Mora y aislamiento
# --------------------------------------------------------------------------- #
def test_la_mora_lista_a_quien_se_le_paso_el_plazo(
    cliente_api_autenticado, administrador, tienda, bodega
):
    cliente = cliente_api_autenticado(administrador)
    pedido_id = _tomar_pedido(cliente, tienda, bodega).data["id"]
    hace = timezone.now() - timedelta(days=40)
    PedidoDistribucion.objects.filter(pk=pedido_id).update(
        estado=PedidoDistribucion.Estado.ENTREGADO, fecha_pedido=hace, fecha_entrega=hace
    )

    respuesta = cliente.get(URL_MORA)

    assert respuesta.status_code == 200
    assert respuesta.data["results"][0]["deuda_vencida"] == "35000.00"


def test_no_se_despacha_el_pedido_de_otro_negocio(cliente_api_autenticado, administrador, bodega):
    ajena = FabricaDeClienteDistribucion()
    ajeno = PedidoDistribucion.objects.create(
        negocio=ajena.negocio, cliente_distribucion=ajena, usuario=administrador
    )

    respuesta = cliente_api_autenticado(administrador).post(
        _url("despacho", ajeno.id), {"ubicacion_id": bodega.ubicacion_id}
    )

    assert respuesta.status_code == 404
