"""Pruebas de los casos de uso de identidad y acceso.

Aquí vive el negocio de este módulo, así que aquí está el grueso de las
pruebas: cada regla que impide entrar, cada enlace de un solo uso y el alta
por invitación.
"""

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from negocios.excepciones import NegocioNoEncontrado
from negocios.models import Negocio
from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.dtos import AceptacionDeInvitacionDTO
from usuarios.excepciones import (
    ContrasenaActualIncorrecta,
    ContrasenaInsegura,
    CorreoNoVerificado,
    CorreoYaRegistrado,
    CredencialesInvalidas,
    EnlaceInvalido,
    InvitacionNoEncontrada,
    InvitacionVencida,
    InvitacionYaAceptada,
    NegocioSuspendido,
    SesionInvalida,
    UsuarioInactivo,
    YaHayInvitacionPendiente,
)
from usuarios.models import Invitacion, Rol, Usuario
from usuarios.pruebas.fabricas import (
    CONTRASENA,
    FabricaDeAdministrador,
    FabricaDeInvitacion,
    FabricaDeStaffDePlataforma,
    FabricaDeUsuario,
)
from usuarios.servicios import (
    contrasenas,
    correos,
    invitaciones,
    sesiones,
    verificacion_correo,
)
from usuarios.tokens import codificar_id, token_de_recuperacion, token_de_verificacion

pytestmark = pytest.mark.django_db


# --------------------------------------------------------------------------- #
# Iniciar sesión
# --------------------------------------------------------------------------- #
def test_iniciar_sesion_entrega_los_dos_tokens():
    usuario = FabricaDeUsuario()

    sesion = sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)

    assert sesion.usuario == usuario
    assert sesion.token_de_acceso
    assert sesion.token_de_refresco


def test_iniciar_sesion_no_distingue_mayusculas_en_el_correo():
    usuario = FabricaDeUsuario(correo="ana@tapaso.test")

    sesion = sesiones.iniciar_sesion(correo="  ANA@Tapaso.test ", contrasena=CONTRASENA)

    assert sesion.usuario == usuario


def test_iniciar_sesion_falla_con_la_contrasena_equivocada():
    usuario = FabricaDeUsuario()

    with pytest.raises(CredencialesInvalidas):
        sesiones.iniciar_sesion(correo=usuario.correo, contrasena="otra-cosa-cualquiera")


def test_iniciar_sesion_falla_si_el_correo_no_existe():
    with pytest.raises(CredencialesInvalidas):
        sesiones.iniciar_sesion(correo="nadie@tapaso.test", contrasena=CONTRASENA)


def test_iniciar_sesion_falla_si_el_correo_no_esta_verificado():
    usuario = FabricaDeUsuario(correo_verificado_en=None)

    with pytest.raises(CorreoNoVerificado):
        sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)


def test_iniciar_sesion_falla_si_la_cuenta_esta_desactivada():
    usuario = FabricaDeUsuario(activo=False)

    with pytest.raises(UsuarioInactivo):
        sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)


def test_iniciar_sesion_falla_si_el_negocio_esta_suspendido():
    negocio = FabricaDeNegocio(estado=Negocio.Estado.SUSPENDIDO)
    usuario = FabricaDeUsuario(negocio=negocio)

    with pytest.raises(NegocioSuspendido):
        sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)


def test_el_estado_de_la_cuenta_no_se_revela_sin_la_contrasena_correcta():
    """Una cuenta sin verificar responde igual que una que no existe."""
    usuario = FabricaDeUsuario(correo_verificado_en=None)

    with pytest.raises(CredencialesInvalidas):
        sesiones.iniciar_sesion(correo=usuario.correo, contrasena="no-es-esta")


# --------------------------------------------------------------------------- #
# Renovar y cerrar
# --------------------------------------------------------------------------- #
def test_renovar_la_sesion_anula_el_refresco_anterior():
    usuario = FabricaDeUsuario()
    sesion = sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)

    acceso, refresco_nuevo = sesiones.renovar_sesion(token_de_refresco=sesion.token_de_refresco)

    assert acceso and refresco_nuevo != sesion.token_de_refresco
    with pytest.raises(SesionInvalida):
        sesiones.renovar_sesion(token_de_refresco=sesion.token_de_refresco)


def test_cerrar_sesion_deja_el_refresco_inservible():
    usuario = FabricaDeUsuario()
    sesion = sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)

    sesiones.cerrar_sesion(token_de_refresco=sesion.token_de_refresco)

    with pytest.raises(SesionInvalida):
        sesiones.renovar_sesion(token_de_refresco=sesion.token_de_refresco)


def test_cerrar_sesion_con_un_token_invalido_no_falla():
    """Cerrar sesión es idempotente: el objetivo ya está cumplido."""
    sesiones.cerrar_sesion(token_de_refresco="esto-no-es-un-token")


# --------------------------------------------------------------------------- #
# Recuperar contraseña
# --------------------------------------------------------------------------- #
def test_solicitar_recuperacion_manda_el_enlace():
    usuario = FabricaDeUsuario()

    contrasenas.solicitar_recuperacion(correo=usuario.correo)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [usuario.correo]


def test_solicitar_recuperacion_de_un_correo_inexistente_no_manda_nada():
    contrasenas.solicitar_recuperacion(correo="nadie@tapaso.test")

    assert mail.outbox == []


def test_restablecer_contrasena_la_cambia_y_el_enlace_no_sirve_dos_veces():
    usuario = FabricaDeUsuario()
    uid = codificar_id(usuario.pk)
    token = token_de_recuperacion.make_token(usuario)

    contrasenas.restablecer_contrasena(uid=uid, token=token, contrasena_nueva="Otra.Clave.2026")

    usuario.refresh_from_db()
    assert usuario.check_password("Otra.Clave.2026")
    with pytest.raises(EnlaceInvalido):
        contrasenas.restablecer_contrasena(
            uid=uid, token=token, contrasena_nueva="Tercera.Clave.2026"
        )


def test_restablecer_contrasena_rechaza_una_contrasena_debil():
    usuario = FabricaDeUsuario()

    with pytest.raises(ContrasenaInsegura):
        contrasenas.restablecer_contrasena(
            uid=codificar_id(usuario.pk),
            token=token_de_recuperacion.make_token(usuario),
            contrasena_nueva="12345678",
        )


def test_restablecer_contrasena_con_un_enlace_inventado_falla():
    usuario = FabricaDeUsuario()

    with pytest.raises(EnlaceInvalido):
        contrasenas.restablecer_contrasena(
            uid=codificar_id(usuario.pk),
            token="token-inventado",
            contrasena_nueva="Otra.Clave.2026",
        )


def test_cambiar_la_contrasena_cierra_las_sesiones_abiertas():
    usuario = FabricaDeUsuario()
    sesion_vieja = sesiones.iniciar_sesion(correo=usuario.correo, contrasena=CONTRASENA)

    sesion_nueva = contrasenas.cambiar_contrasena(
        usuario=usuario, contrasena_actual=CONTRASENA, contrasena_nueva="Otra.Clave.2026"
    )

    assert sesion_nueva.token_de_refresco != sesion_vieja.token_de_refresco
    with pytest.raises(SesionInvalida):
        sesiones.renovar_sesion(token_de_refresco=sesion_vieja.token_de_refresco)


def test_cambiar_la_contrasena_exige_acertar_la_actual():
    usuario = FabricaDeUsuario()

    with pytest.raises(ContrasenaActualIncorrecta):
        contrasenas.cambiar_contrasena(
            usuario=usuario,
            contrasena_actual="no-es-esta",
            contrasena_nueva="Otra.Clave.2026",
        )


# --------------------------------------------------------------------------- #
# Verificar el correo
# --------------------------------------------------------------------------- #
def test_confirmar_la_verificacion_marca_la_fecha_y_el_enlace_muere():
    usuario = FabricaDeUsuario(correo_verificado_en=None)
    uid = codificar_id(usuario.pk)
    token = token_de_verificacion.make_token(usuario)

    verificacion_correo.confirmar_verificacion(uid=uid, token=token)

    usuario.refresh_from_db()
    assert usuario.correo_esta_verificado
    with pytest.raises(EnlaceInvalido):
        verificacion_correo.confirmar_verificacion(uid=uid, token=token)


def test_solicitar_verificacion_no_manda_nada_si_ya_esta_verificado():
    usuario = FabricaDeUsuario()

    verificacion_correo.solicitar_verificacion(correo=usuario.correo)

    assert mail.outbox == []


def test_un_token_de_recuperacion_no_sirve_para_verificar_el_correo():
    usuario = FabricaDeUsuario(correo_verificado_en=None)

    with pytest.raises(EnlaceInvalido):
        verificacion_correo.confirmar_verificacion(
            uid=codificar_id(usuario.pk),
            token=token_de_recuperacion.make_token(usuario),
        )


# --------------------------------------------------------------------------- #
# Invitaciones
# --------------------------------------------------------------------------- #
def test_crear_una_invitacion_manda_el_correo_y_guarda_solo_el_hash(
    django_capture_on_commit_callbacks,
):
    administrador = FabricaDeAdministrador()

    # El correo sale en `on_commit`, y en una prueba la transacción no se
    # confirma nunca: sin esto el buzón quedaría vacío por el motivo equivocado.
    with django_capture_on_commit_callbacks(execute=True):
        invitacion = invitaciones.crear_invitacion(
            negocio_id=administrador.negocio_id,
            correo="Nuevo@Tapaso.test",
            rol=Rol.CAJERO,
            invitada_por_id=administrador.pk,
        )

    assert invitacion.correo == "nuevo@tapaso.test"
    assert len(invitacion.hash_token) == 64
    assert len(mail.outbox) == 1


def test_no_se_puede_invitar_dos_veces_al_mismo_correo():
    administrador = FabricaDeAdministrador()
    FabricaDeInvitacion(negocio=administrador.negocio, correo="repetido@tapaso.test")

    with pytest.raises(YaHayInvitacionPendiente):
        invitaciones.crear_invitacion(
            negocio_id=administrador.negocio_id,
            correo="repetido@tapaso.test",
            rol=Rol.MESERO,
            invitada_por_id=administrador.pk,
        )


def test_no_se_puede_invitar_a_alguien_que_ya_tiene_cuenta():
    administrador = FabricaDeAdministrador()
    existente = FabricaDeUsuario()

    with pytest.raises(CorreoYaRegistrado):
        invitaciones.crear_invitacion(
            negocio_id=administrador.negocio_id,
            correo=existente.correo,
            rol=Rol.MESERO,
            invitada_por_id=administrador.pk,
        )


def test_no_se_puede_invitar_a_un_negocio_que_no_existe():
    # En una prueba la transacción nunca se confirma, así que sin la
    # comprobación del servicio la clave foránea diferida no saltaría y la
    # invitación huérfana quedaría creada.
    staff = FabricaDeStaffDePlataforma()

    with pytest.raises(NegocioNoEncontrado):
        invitaciones.crear_invitacion(
            negocio_id=999_999,
            correo="nadie@tapaso.test",
            rol=Rol.ADMINISTRADOR,
            invitada_por_id=staff.pk,
        )

    assert not Invitacion.objects.exists()


def test_aceptar_la_invitacion_crea_al_usuario_ya_verificado():
    invitacion = FabricaDeInvitacion(rol=Rol.CAJERO)

    sesion = invitaciones.aceptar_invitacion(
        datos=AceptacionDeInvitacionDTO(
            token=invitacion.token_en_claro,
            nombre="Luis",
            apellido="Pérez",
            telefono="3001234567",
            contrasena=CONTRASENA,
        )
    )

    usuario = sesion.usuario
    assert usuario.correo == invitacion.correo
    assert usuario.rol == Rol.CAJERO
    assert usuario.negocio_id == invitacion.negocio_id
    assert usuario.correo_esta_verificado
    assert sesion.token_de_acceso


def test_aceptar_la_invitacion_la_marca_como_usada():
    invitacion = FabricaDeInvitacion()

    sesion = invitaciones.aceptar_invitacion(
        datos=AceptacionDeInvitacionDTO(
            token=invitacion.token_en_claro,
            nombre="Luis",
            apellido="Pérez",
            telefono="",
            contrasena=CONTRASENA,
        )
    )

    invitacion.refresh_from_db()
    assert invitacion.aceptada_en is not None
    assert invitacion.aceptada_por == sesion.usuario


def test_la_misma_invitacion_no_se_puede_usar_dos_veces():
    invitacion = FabricaDeInvitacion()
    datos = AceptacionDeInvitacionDTO(
        token=invitacion.token_en_claro,
        nombre="Luis",
        apellido="Pérez",
        telefono="",
        contrasena=CONTRASENA,
    )
    invitaciones.aceptar_invitacion(datos=datos)

    with pytest.raises(InvitacionYaAceptada):
        invitaciones.aceptar_invitacion(datos=datos)


def test_no_se_puede_aceptar_una_invitacion_vencida():
    invitacion = FabricaDeInvitacion(expira_en=timezone.now() - timedelta(minutes=1))

    with pytest.raises(InvitacionVencida):
        invitaciones.aceptar_invitacion(
            datos=AceptacionDeInvitacionDTO(
                token=invitacion.token_en_claro,
                nombre="Luis",
                apellido="Pérez",
                telefono="",
                contrasena=CONTRASENA,
            )
        )


def test_el_rol_lo_pone_quien_invita_y_no_quien_acepta():
    """El formulario de aceptación no tiene campo `rol`, y por eso no se puede subir de rango."""
    invitacion = FabricaDeInvitacion(rol=Rol.MESERO)

    sesion = invitaciones.aceptar_invitacion(
        datos=AceptacionDeInvitacionDTO(
            token=invitacion.token_en_claro,
            nombre="Luis",
            apellido="Pérez",
            telefono="",
            contrasena=CONTRASENA,
        )
    )

    assert sesion.usuario.rol == Rol.MESERO
    assert not sesion.usuario.es_administrador


def test_reenviar_una_invitacion_anula_el_enlace_anterior():
    administrador = FabricaDeAdministrador()
    invitacion = FabricaDeInvitacion(negocio=administrador.negocio, creada_por=administrador)
    token_viejo = invitacion.token_en_claro

    invitaciones.reenviar_invitacion(
        invitacion_id=invitacion.pk, negocio_id=administrador.negocio_id
    )

    with pytest.raises(InvitacionNoEncontrada):
        invitaciones.aceptar_invitacion(
            datos=AceptacionDeInvitacionDTO(
                token=token_viejo,
                nombre="Luis",
                apellido="Pérez",
                telefono="",
                contrasena=CONTRASENA,
            )
        )


def test_revocar_una_invitacion_permite_volver_a_invitar_a_ese_correo():
    administrador = FabricaDeAdministrador()
    invitacion = FabricaDeInvitacion(
        negocio=administrador.negocio, creada_por=administrador, correo="otra@tapaso.test"
    )

    invitaciones.revocar_invitacion(
        invitacion_id=invitacion.pk, negocio_id=administrador.negocio_id
    )

    assert not Invitacion.objects.filter(pk=invitacion.pk).exists()
    invitaciones.crear_invitacion(
        negocio_id=administrador.negocio_id,
        correo="otra@tapaso.test",
        rol=Rol.MESERO,
        invitada_por_id=administrador.pk,
    )


def test_un_negocio_no_puede_revocar_la_invitacion_de_otro():
    administrador = FabricaDeAdministrador()
    ajena = FabricaDeInvitacion()

    with pytest.raises(InvitacionNoEncontrada):
        invitaciones.revocar_invitacion(invitacion_id=ajena.pk, negocio_id=administrador.negocio_id)

    assert Invitacion.objects.filter(pk=ajena.pk).exists()


def test_el_superusuario_nace_con_el_correo_verificado():
    staff = Usuario.objects.create_superuser(correo="staff@tapaso.test", password=CONTRASENA)

    assert staff.correo_esta_verificado
    assert staff.negocio is None


# --------------------------------------------------------------------------- #
# Los enlaces de los correos
# --------------------------------------------------------------------------- #
def test_el_enlace_del_correo_no_lleva_el_ampersand_escapado():
    """Regresión: el autoescape de Django rompía la URL convirtiendo & en &amp;.

    El enlace llegaba con un parámetro llamado `amp;token` y el frontend no
    encontraba el token.
    """
    usuario = FabricaDeUsuario()

    contrasenas.solicitar_recuperacion(correo=usuario.correo)

    cuerpo = mail.outbox[0].body
    assert "&amp;" not in cuerpo
    assert "uid=" in cuerpo and "&token=" in cuerpo


def test_el_correo_de_invitacion_no_lleva_plantilla_sin_renderizar():
    invitacion = FabricaDeInvitacion()

    correos.enviar_invitacion(invitacion=invitacion, token=invitacion.token_en_claro)

    cuerpo = mail.outbox[0].body
    assert "{{" not in cuerpo and "{%" not in cuerpo
    assert invitacion.negocio.nombre_comercial in cuerpo
    assert cuerpo.startswith("Hola")


def test_el_correo_de_invitacion_se_entiende_aunque_quien_invita_no_tenga_nombre():
    """Regresión: el staff de plataforma puede no tener nombre cargado.

    El correo empezaba con un hueco: « te invitó a trabajar en...».
    """
    quien_invita = FabricaDeAdministrador(nombre="", apellido="")
    invitacion = FabricaDeInvitacion(creada_por=quien_invita)

    correos.enviar_invitacion(invitacion=invitacion, token=invitacion.token_en_claro)

    cuerpo = mail.outbox[0].body
    assert "Te invitaron a trabajar en" in cuerpo
    assert not any(linea.startswith(" te invitó") for linea in cuerpo.splitlines())
