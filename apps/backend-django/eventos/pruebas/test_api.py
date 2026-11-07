"""Pruebas de los endpoints del evento/bar.

Lo propio de esta app es el reparto de permisos: el mesero opera la barra pero
no cobra, y no toca la caja. Aquí se comprueba esa matriz entera.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from catalogo.pruebas.fabricas import FabricaDeProducto
from clientes.pruebas.fabricas import FabricaDeCliente
from eventos.models import PagoEvento, PedidoEvento
from eventos.pruebas.fabricas import FabricaDeDispositivoNfc, FabricaDePulsera
from eventos.servicios import cuentas as servicio_de_cuentas
from eventos.servicios import jornadas as servicio_de_jornadas
from inventario.pruebas.fabricas import FabricaDeExistencia

pytestmark = pytest.mark.django_db

URL_JORNADAS = reverse("eventos:jornada-list")
URL_APERTURA = reverse("eventos:jornada-apertura")
URL_GRUPOS = reverse("eventos:grupo-list")
URL_CUENTAS = reverse("eventos:cuenta-list")
URL_PEDIDOS = reverse("eventos:pedido-list")
URL_PULSERAS = reverse("eventos:pulsera-list")
URL_DISPOSITIVOS = reverse("eventos:dispositivo-list")
URL_PUNTO_DE_CONTROL = reverse("eventos:punto-de-control")


@pytest.fixture
def barra(negocio):
    return FabricaDeExistencia(
        negocio=negocio,
        cantidad_disponible=Decimal("100.00"),
        producto=FabricaDeProducto(negocio=negocio, precio_evento=Decimal("5000.00")),
    )


@pytest.fixture
def jornada(negocio, barra):
    return servicio_de_jornadas.obtener_o_abrir_jornada(
        negocio_id=negocio.id, ubicacion_id=barra.ubicacion_id
    )


@pytest.fixture
def cuenta(negocio, jornada, mesero):
    grupo = servicio_de_cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    return servicio_de_cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
    )


def _tomar_comanda(cliente, jornada, barra, cuenta_id=None, cantidad="2.00"):
    return cliente.post(
        URL_PEDIDOS,
        {
            "evento_id": jornada.id,
            "cliente_evento_id": cuenta_id,
            "lineas": [{"producto_id": barra.producto_id, "cantidad": cantidad}],
        },
        format="json",
    )


# --------------------------------------------------------------------------- #
# Matriz de permisos
# --------------------------------------------------------------------------- #
def test_sin_iniciar_sesion_no_se_ve_nada(cliente_api):
    assert cliente_api.get(URL_JORNADAS).status_code == 401


def test_el_mesero_no_abre_la_caja(cliente_api_autenticado, mesero, barra):
    """Abrir y cerrar la jornada es del cajero."""
    respuesta = cliente_api_autenticado(mesero).post(
        URL_APERTURA, {"ubicacion_id": barra.ubicacion_id}, format="json"
    )

    assert respuesta.status_code == 403


def test_el_cajero_abre_la_caja(cliente_api_autenticado, cajero, barra):
    respuesta = cliente_api_autenticado(cajero).post(
        URL_APERTURA, {"ubicacion_id": barra.ubicacion_id}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["estado"] == "en_curso"


def test_el_mesero_si_abre_grupos_y_cuentas(cliente_api_autenticado, mesero, negocio, jornada):
    cliente = cliente_api_autenticado(mesero)
    grupo = cliente.post(
        URL_GRUPOS, {"evento_id": jornada.id, "mesa_zona": "Mesa 3"}, format="json"
    )

    cuenta = cliente.post(
        URL_CUENTAS,
        {"grupo_id": grupo.data["id"], "cliente_id": FabricaDeCliente(negocio=negocio).id},
        format="json",
    )

    assert grupo.status_code == 201
    assert cuenta.status_code == 201


def test_el_mesero_si_toma_y_entrega_comandas(
    cliente_api_autenticado, mesero, jornada, barra, cuenta
):
    cliente = cliente_api_autenticado(mesero)
    pedido = _tomar_comanda(cliente, jornada, barra, cuenta.id)

    entrega = cliente.post(reverse("eventos:pedido-entrega", args=[pedido.data["id"]]))

    assert pedido.status_code == 201
    assert entrega.status_code == 200
    assert entrega.data["estado"] == "entregado"


def test_el_mesero_no_cobra(cliente_api_autenticado, mesero, jornada, barra, cuenta):
    """Es la línea que separa al mesero del cajero."""
    _tomar_comanda(cliente_api_autenticado(mesero), jornada, barra, cuenta.id)

    respuesta = cliente_api_autenticado(mesero).post(
        reverse("eventos:cuenta-cobro", args=[cuenta.id]),
        {"monto": "10000.00", "metodo": "efectivo"},
        format="json",
    )

    assert respuesta.status_code == 403
    assert PagoEvento.objects.count() == 0


def test_el_mesero_no_cancela_una_comanda(cliente_api_autenticado, mesero, jornada, barra, cuenta):
    """Decisión 10: cancelar devuelve stock y es una corrección de caja."""
    pedido = _tomar_comanda(cliente_api_autenticado(mesero), jornada, barra, cuenta.id)

    respuesta = cliente_api_autenticado(mesero).post(
        reverse("eventos:pedido-cancelacion", args=[pedido.data["id"]]),
        {"motivo": "Me equivoqué."},
        format="json",
    )

    assert respuesta.status_code == 403


def test_el_cajero_si_cancela(cliente_api_autenticado, mesero, cajero, jornada, barra, cuenta):
    pedido = _tomar_comanda(cliente_api_autenticado(mesero), jornada, barra, cuenta.id)

    respuesta = cliente_api_autenticado(cajero).post(
        reverse("eventos:pedido-cancelacion", args=[pedido.data["id"]]),
        {"motivo": "Se equivocó de mesa."},
        format="json",
    )

    assert respuesta.status_code == 200
    barra.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("100.00")


def test_el_cajero_no_registra_pulseras(cliente_api_autenticado, cajero):
    """Dar de alta chips es de administrador."""
    respuesta = cliente_api_autenticado(cajero).post(
        URL_PULSERAS, {"uid_tag": "04A2B3C4"}, format="json"
    )

    assert respuesta.status_code == 403


def test_el_administrador_registra_pulseras(cliente_api_autenticado, administrador):
    respuesta = cliente_api_autenticado(administrador).post(
        URL_PULSERAS, {"uid_tag": "04a2b3c4"}, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["uid_tag"] == "04A2B3C4"


# --------------------------------------------------------------------------- #
# Aislamiento entre negocios
# --------------------------------------------------------------------------- #
def test_no_se_ven_las_jornadas_de_otro_negocio(cliente_api_autenticado, cajero, jornada):
    from eventos.pruebas.fabricas import FabricaDeEvento

    FabricaDeEvento()  # de otro negocio

    respuesta = cliente_api_autenticado(cajero).get(URL_JORNADAS)

    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["id"] == jornada.id


def test_cobrar_la_cuenta_de_otro_negocio_da_404(cliente_api_autenticado, cajero):
    from eventos.pruebas.fabricas import FabricaDeCuenta

    ajena = FabricaDeCuenta()

    respuesta = cliente_api_autenticado(cajero).post(
        reverse("eventos:cuenta-cobro", args=[ajena.id]),
        {"monto": "1000.00", "metodo": "efectivo"},
        format="json",
    )

    assert respuesta.status_code == 404


# --------------------------------------------------------------------------- #
# La venta de punta a punta
# --------------------------------------------------------------------------- #
def test_el_recorrido_del_bar(cliente_api_autenticado, mesero, cajero, negocio, barra):
    """Abrir caja → grupo → cuenta → comanda → cobrar → cerrar caja."""
    del_cajero = cliente_api_autenticado(cajero)
    jornada = del_cajero.post(
        URL_APERTURA, {"ubicacion_id": barra.ubicacion_id}, format="json"
    ).data

    del_mesero = cliente_api_autenticado(mesero)
    grupo = del_mesero.post(URL_GRUPOS, {"evento_id": jornada["id"]}, format="json").data
    cuenta = del_mesero.post(
        URL_CUENTAS,
        {"grupo_id": grupo["id"], "cliente_id": FabricaDeCliente(negocio=negocio).id},
        format="json",
    ).data
    del_mesero.post(
        URL_PEDIDOS,
        {
            "evento_id": jornada["id"],
            "cliente_evento_id": cuenta["id"],
            "lineas": [{"producto_id": barra.producto_id, "cantidad": "3.00"}],
        },
        format="json",
    )

    barra.refresh_from_db()
    assert barra.cantidad_disponible == Decimal("97.00")

    cobro = cliente_api_autenticado(cajero).post(
        reverse("eventos:cuenta-cobro", args=[cuenta["id"]]),
        {"monto": "15000.00", "metodo": "efectivo"},
        format="json",
    )
    assert cobro.status_code == 201
    assert cobro.data["consumido"] == "15000.00"

    cierre = cliente_api_autenticado(cajero).post(
        reverse("eventos:jornada-cierre", args=[jornada["id"]])
    )
    assert cierre.status_code == 200
    assert cierre.data["estado"] == "cerrado"


def test_cerrar_la_caja_con_cuentas_abiertas_devuelve_409_con_la_lista(
    cliente_api_autenticado, cajero, jornada, cuenta
):
    respuesta = cliente_api_autenticado(cajero).post(
        reverse("eventos:jornada-cierre", args=[jornada.id])
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "cuentas_sin_saldar"
    assert respuesta.data["error"]["detalles"]["cuentas"][0]["cuenta_id"] == cuenta.id


def test_vender_sin_stock_devuelve_409_y_no_deja_el_pedido(
    cliente_api_autenticado, mesero, jornada, barra, cuenta
):
    respuesta = _tomar_comanda(
        cliente_api_autenticado(mesero), jornada, barra, cuenta.id, cantidad="500.00"
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "existencias_insuficientes"
    assert PedidoEvento.objects.count() == 0


def test_un_pago_corto_devuelve_409(
    cliente_api_autenticado, mesero, cajero, jornada, barra, cuenta
):
    _tomar_comanda(cliente_api_autenticado(mesero), jornada, barra, cuenta.id)

    respuesta = cliente_api_autenticado(cajero).post(
        reverse("eventos:cuenta-cobro", args=[cuenta.id]),
        {"monto": "1000.00", "metodo": "efectivo"},
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["error"]["codigo"] == "pago_no_cubre_el_consumo"


# --------------------------------------------------------------------------- #
# Punto de control NFC
# --------------------------------------------------------------------------- #
def test_el_punto_de_control_responde_al_lector_con_su_token(
    cliente_api, negocio, jornada, mesero, barra
):
    pulsera = FabricaDePulsera(negocio=negocio)
    grupo = servicio_de_cuentas.abrir_grupo(
        evento_id=jornada.id, negocio_id=negocio.id, abierto_por_id=mesero.id
    )
    con_pulsera = servicio_de_cuentas.abrir_cuenta(
        grupo_id=grupo.id,
        cliente_id=FabricaDeCliente(negocio=negocio).id,
        negocio_id=negocio.id,
        asignada_por_id=mesero.id,
        pulsera_id=pulsera.id,
    )
    from eventos.dtos import LineaDePedidoDTO
    from eventos.servicios import pedidos as servicio_de_pedidos

    servicio_de_pedidos.registrar_pedido(
        evento_id=jornada.id,
        cliente_evento_id=con_pulsera.id,
        lineas=[LineaDePedidoDTO(producto_id=barra.producto_id, cantidad=Decimal("2.00"))],
        mesero_id=mesero.id,
        negocio_id=negocio.id,
    )
    lector = FabricaDeDispositivoNfc(negocio=negocio)

    respuesta = cliente_api.post(
        URL_PUNTO_DE_CONTROL,
        {"uid_tag": pulsera.uid_tag},
        format="json",
        HTTP_AUTHORIZATION=f"Dispositivo {lector.token_en_claro}",
    )

    assert respuesta.status_code == 200
    assert respuesta.data["estado"] == "con_saldo"
    assert respuesta.data["monto"] == "10000.00"
    # Lo mínimo: ni documento, ni teléfono.
    assert set(respuesta.data) == {"estado", "cliente", "monto"}


def test_sin_token_de_dispositivo_el_punto_de_control_no_contesta(cliente_api, negocio):
    pulsera = FabricaDePulsera(negocio=negocio)

    respuesta = cliente_api.post(URL_PUNTO_DE_CONTROL, {"uid_tag": pulsera.uid_tag}, format="json")

    assert respuesta.status_code in (401, 403)


def test_un_token_revocado_deja_de_servir(cliente_api, negocio, administrador):
    """Es para lo que existe: si alguien abre la caja, se revoca ese y ya."""
    pulsera = FabricaDePulsera(negocio=negocio)
    lector = FabricaDeDispositivoNfc(negocio=negocio)
    token = lector.token_en_claro
    lector.activo = False
    lector.save(update_fields=["activo"])

    respuesta = cliente_api.post(
        URL_PUNTO_DE_CONTROL,
        {"uid_tag": pulsera.uid_tag},
        format="json",
        HTTP_AUTHORIZATION=f"Dispositivo {token}",
    )

    assert respuesta.status_code == 401


def test_el_lector_no_ve_las_pulseras_de_otro_negocio(cliente_api, negocio):
    """El negocio sale del token del aparato, nunca de la petición."""
    ajena = FabricaDePulsera()
    lector = FabricaDeDispositivoNfc(negocio=negocio)

    respuesta = cliente_api.post(
        URL_PUNTO_DE_CONTROL,
        {"uid_tag": ajena.uid_tag},
        format="json",
        HTTP_AUTHORIZATION=f"Dispositivo {lector.token_en_claro}",
    )

    assert respuesta.status_code == 404


def test_dar_de_alta_un_lector_devuelve_el_token_una_sola_vez(
    cliente_api_autenticado, administrador
):
    respuesta = cliente_api_autenticado(administrador).post(
        URL_DISPOSITIVOS, {"nombre": "Puerta principal"}, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["token"]
    # En el listado ya no sale: en la base solo queda el hash.
    listado = cliente_api_autenticado(administrador).get(URL_DISPOSITIVOS)
    assert "token" not in listado.data["results"][0]
