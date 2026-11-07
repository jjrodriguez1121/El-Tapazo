"""Pruebas de los endpoints de identidad y acceso.

Se comprueba lo de siempre: el código de estado, la forma del JSON, los
permisos y —lo más importante de esta plataforma— que un negocio no vea ni
toque los datos de otro.
"""

import pytest
from django.urls import reverse

from negocios.models import Negocio
from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.models import Rol, Usuario
from usuarios.pruebas.fabricas import (
    CONTRASENA,
    FabricaDeAdministrador,
    FabricaDeInvitacion,
    FabricaDeUsuario,
)

pytestmark = pytest.mark.django_db

URL_SESIONES = reverse("usuarios:inicio-de-sesion")
URL_YO = reverse("usuarios:usuario-autenticado")
URL_INVITACIONES = reverse("usuarios:invitacion-list")
URL_RECUPERACION = reverse("usuarios:recuperacion-de-contrasena")
URL_ACEPTACION = reverse("usuarios:aceptacion-de-invitacion")
URL_PENDIENTE = reverse("usuarios:invitacion-pendiente")
URL_CAMBIO = reverse("usuarios:cambio-de-contrasena")


# --------------------------------------------------------------------------- #
# Sesión
# --------------------------------------------------------------------------- #
def test_iniciar_sesion_devuelve_201_con_los_tokens_y_el_usuario(cliente_api):
    usuario = FabricaDeUsuario()

    respuesta = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": CONTRASENA}, format="json"
    )

    assert respuesta.status_code == 201
    assert set(respuesta.data) == {"acceso", "refresco", "usuario"}
    assert respuesta.data["usuario"]["correo"] == usuario.correo
    assert "contrasena" not in respuesta.data["usuario"]
    assert "password" not in respuesta.data["usuario"]


def test_iniciar_sesion_con_credenciales_malas_devuelve_401_con_el_formato_de_error(
    cliente_api,
):
    usuario = FabricaDeUsuario()

    respuesta = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": "no-es-esta"}, format="json"
    )

    assert respuesta.status_code == 401
    assert respuesta.data["error"]["codigo"] == "credenciales_invalidas"
    assert respuesta.data["error"]["mensaje"]


def test_iniciar_sesion_sin_verificar_el_correo_devuelve_403_con_su_codigo(cliente_api):
    usuario = FabricaDeUsuario(correo_verificado_en=None)

    respuesta = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": CONTRASENA}, format="json"
    )

    assert respuesta.status_code == 403
    assert respuesta.data["error"]["codigo"] == "correo_no_verificado"


def test_iniciar_sesion_con_datos_incompletos_devuelve_400_con_los_campos(cliente_api):
    respuesta = cliente_api.post(URL_SESIONES, {"correo": "no-es-un-correo"}, format="json")

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "datos_invalidos"
    assert "contrasena" in respuesta.data["error"]["detalles"]


def test_el_token_devuelto_sirve_para_entrar(cliente_api):
    usuario = FabricaDeUsuario()
    acceso = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": CONTRASENA}, format="json"
    ).data["acceso"]

    respuesta = cliente_api.get(URL_YO, HTTP_AUTHORIZATION=f"Bearer {acceso}")

    assert respuesta.status_code == 200
    assert respuesta.data["correo"] == usuario.correo
    assert respuesta.data["negocio"]["nombre_comercial"] == usuario.negocio.nombre_comercial


def test_sin_token_no_se_puede_saber_quien_soy(cliente_api):
    respuesta = cliente_api.get(URL_YO)

    assert respuesta.status_code == 401
    assert respuesta.data["error"]["codigo"] == "no_autenticado"


def test_renovar_y_cerrar_la_sesion(cliente_api):
    usuario = FabricaDeUsuario()
    sesion = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": CONTRASENA}, format="json"
    ).data

    renovada = cliente_api.post(
        reverse("usuarios:renovacion-de-sesion"), {"refresco": sesion["refresco"]}, format="json"
    )
    assert renovada.status_code == 200
    assert set(renovada.data) == {"acceso", "refresco"}

    cliente_api.credentials(HTTP_AUTHORIZATION=f"Bearer {renovada.data['acceso']}")
    cerrada = cliente_api.post(
        reverse("usuarios:cierre-de-sesion"), {"refresco": renovada.data["refresco"]}, format="json"
    )
    assert cerrada.status_code == 204


# --------------------------------------------------------------------------- #
# Recuperación de contraseña
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("correo", ["existe@tapaso.test", "no-existe@tapaso.test"])
def test_la_recuperacion_responde_lo_mismo_exista_o_no_el_correo(cliente_api, correo):
    FabricaDeUsuario(correo="existe@tapaso.test")

    respuesta = cliente_api.post(URL_RECUPERACION, {"correo": correo}, format="json")

    assert respuesta.status_code == 202


# --------------------------------------------------------------------------- #
# Invitaciones
# --------------------------------------------------------------------------- #
def test_un_administrador_invita_a_un_trabajador(cliente_api):
    administrador = FabricaDeAdministrador()
    cliente_api.force_authenticate(administrador)

    respuesta = cliente_api.post(
        URL_INVITACIONES, {"correo": "nuevo@tapaso.test", "rol": Rol.MESERO}, format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.data["correo"] == "nuevo@tapaso.test"
    assert "hash_token" not in respuesta.data


def test_un_mesero_no_puede_invitar(cliente_api):
    mesero = FabricaDeUsuario(rol=Rol.MESERO)
    cliente_api.force_authenticate(mesero)

    respuesta = cliente_api.post(
        URL_INVITACIONES, {"correo": "nuevo@tapaso.test", "rol": Rol.MESERO}, format="json"
    )

    assert respuesta.status_code == 403


def test_el_negocio_de_la_invitacion_sale_del_usuario_y_no_del_cuerpo(cliente_api):
    administrador = FabricaDeAdministrador()
    ajeno = FabricaDeNegocio()
    cliente_api.force_authenticate(administrador)

    respuesta = cliente_api.post(
        URL_INVITACIONES,
        {"correo": "nuevo@tapaso.test", "rol": Rol.MESERO, "negocio": ajeno.pk},
        format="json",
    )

    assert respuesta.status_code == 201
    assert administrador.negocio.invitaciones.filter(correo="nuevo@tapaso.test").exists()
    assert not ajeno.invitaciones.exists()


def test_no_se_ven_las_invitaciones_de_otro_negocio(cliente_api):
    administrador = FabricaDeAdministrador()
    FabricaDeInvitacion(negocio=administrador.negocio, creada_por=administrador)
    FabricaDeInvitacion()  # de otro negocio
    cliente_api.force_authenticate(administrador)

    respuesta = cliente_api.get(URL_INVITACIONES)

    assert respuesta.status_code == 200
    assert len(respuesta.data["results"]) == 1


def test_no_se_puede_cancelar_la_invitacion_de_otro_negocio(cliente_api):
    administrador = FabricaDeAdministrador()
    ajena = FabricaDeInvitacion()
    cliente_api.force_authenticate(administrador)

    respuesta = cliente_api.delete(reverse("usuarios:invitacion-detail", args=[ajena.pk]))

    assert respuesta.status_code == 404


# --------------------------------------------------------------------------- #
# Aceptar la invitación (público)
# --------------------------------------------------------------------------- #
def test_ver_una_invitacion_antes_de_aceptarla(cliente_api):
    invitacion = FabricaDeInvitacion()

    respuesta = cliente_api.get(URL_PENDIENTE, {"token": invitacion.token_en_claro})

    assert respuesta.status_code == 200
    assert respuesta.data["correo"] == invitacion.correo
    assert respuesta.data["negocio"] == invitacion.negocio.nombre_comercial


def test_aceptar_la_invitacion_crea_la_cuenta_y_deja_la_sesion_abierta(cliente_api):
    invitacion = FabricaDeInvitacion()

    respuesta = cliente_api.post(
        URL_ACEPTACION,
        {
            "token": invitacion.token_en_claro,
            "nombre": "Luis",
            "apellido": "Pérez",
            "telefono": "3001234567",
            "contrasena": CONTRASENA,
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["acceso"]
    assert Usuario.objects.filter(correo=invitacion.correo).exists()


def test_aceptar_con_una_contrasena_debil_devuelve_400_con_los_motivos(cliente_api):
    invitacion = FabricaDeInvitacion()

    respuesta = cliente_api.post(
        URL_ACEPTACION,
        {
            "token": invitacion.token_en_claro,
            "nombre": "Luis",
            "apellido": "Pérez",
            "telefono": "",
            "contrasena": "12345678",
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "contrasena_insegura"
    assert respuesta.data["error"]["detalles"]["errores"]


def test_un_negocio_suspendido_no_deja_entrar_a_su_gente(cliente_api):
    negocio = FabricaDeNegocio(estado=Negocio.Estado.SUSPENDIDO)
    usuario = FabricaDeUsuario(negocio=negocio)

    respuesta = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": CONTRASENA}, format="json"
    )

    assert respuesta.status_code == 403
    assert respuesta.data["error"]["codigo"] == "negocio_suspendido"


def test_sin_autenticar_las_invitaciones_devuelven_401_y_no_403(cliente_api):
    """401 dice "identifícate"; 403 diría "ya sé quién eres, pero no puedes"."""
    respuesta = cliente_api.get(URL_INVITACIONES)

    assert respuesta.status_code == 401
    assert respuesta.data["error"]["codigo"] == "no_autenticado"


def test_cambiar_la_contrasena_devuelve_tokens_nuevos_que_sirven(cliente_api):
    """Los viejos quedan anulados, así que la respuesta trae el reemplazo."""
    usuario = FabricaDeUsuario()
    sesion = cliente_api.post(
        URL_SESIONES, {"correo": usuario.correo, "contrasena": CONTRASENA}, format="json"
    ).data
    cliente_api.credentials(HTTP_AUTHORIZATION=f"Bearer {sesion['acceso']}")

    respuesta = cliente_api.post(
        URL_CAMBIO,
        {"contrasena_actual": CONTRASENA, "contrasena_nueva": "Otra.Clave.Tapaso.2026"},
        format="json",
    )

    assert respuesta.status_code == 200
    assert respuesta.data["acceso"] != sesion["acceso"]

    cliente_api.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['acceso']}")
    assert cliente_api.get(URL_YO).status_code == 200


def test_no_se_puede_cambiar_la_contrasena_sin_acertar_la_actual(cliente_api):
    usuario = FabricaDeUsuario()
    cliente_api.force_authenticate(usuario)

    respuesta = cliente_api.post(
        URL_CAMBIO,
        {"contrasena_actual": "no-es-esta", "contrasena_nueva": "Otra.Clave.Tapaso.2026"},
        format="json",
    )

    assert respuesta.status_code == 400
    assert respuesta.data["error"]["codigo"] == "contrasena_actual_incorrecta"
