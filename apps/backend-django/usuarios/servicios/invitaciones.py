"""Alta de trabajadores: invitar, reenviar, revocar y aceptar.

No hay registro público. Si lo hubiera, cualquiera podría darse de alta en un
negocio ajeno; y como el rol lo pone quien invita y no quien acepta, tampoco
puede nadie concederse el rol de administrador a sí mismo.
"""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from negocios.excepciones import NegocioNoEncontrado
from negocios.repositorios import negocios as repositorio_de_negocios
from usuarios.dtos import AceptacionDeInvitacionDTO, SesionDTO
from usuarios.excepciones import (
    CorreoYaRegistrado,
    InvitacionNoEncontrada,
    InvitacionYaAceptada,
    YaHayInvitacionPendiente,
)
from usuarios.models import Invitacion
from usuarios.repositorios import invitaciones as repositorio
from usuarios.repositorios import usuarios as repositorio_de_usuarios
from usuarios.selectores.invitaciones import obtener_pendiente_por_token
from usuarios.servicios import correos, sesiones
from usuarios.tokens import generar_token_de_invitacion
from usuarios.validadores.contrasenas import validar_contrasena


@transaction.atomic
def crear_invitacion(*, negocio_id: int, correo: str, rol: str, invitada_por_id: int) -> Invitacion:
    """Invita a alguien a trabajar en un negocio y le manda el enlace.

    Raises:
        NegocioNoEncontrado: no hay ningún negocio con ese id.
        CorreoYaRegistrado: ese correo ya tiene cuenta.
        YaHayInvitacionPendiente: ya se le invitó y no ha aceptado.
    """
    # Desde la API el negocio sale del administrador autenticado y siempre
    # existe; desde `invitar_administrador` lo escribe una persona. Sin esta
    # comprobación, la clave foránea —diferida hasta el commit— reventaría como
    # un IntegrityError en vez de decir qué pasó.
    if repositorio_de_negocios.obtener(negocio_id=negocio_id) is None:
        raise NegocioNoEncontrado
    correo = correo.strip().lower()
    if repositorio_de_usuarios.existe_con_correo(correo=correo):
        raise CorreoYaRegistrado
    if repositorio.hay_pendiente(negocio_id=negocio_id, correo=correo):
        raise YaHayInvitacionPendiente

    token, hash_token = generar_token_de_invitacion()
    invitacion = repositorio.crear(
        negocio_id=negocio_id,
        correo=correo,
        rol=rol,
        hash_token=hash_token,
        creada_por_id=invitada_por_id,
        expira_en=_vencimiento(),
    )
    transaction.on_commit(lambda: correos.enviar_invitacion(invitacion=invitacion, token=token))
    return invitacion


@transaction.atomic
def reenviar_invitacion(*, invitacion_id: int, negocio_id: int) -> Invitacion:
    """Manda otro enlace y **anula el anterior**.

    Se genera un token nuevo en vez de reenviar el mismo: si el primer correo
    acabó en la bandeja equivocada, reenviarlo no arreglaría nada.
    """
    invitacion = _obtener_pendiente_del_negocio(invitacion_id=invitacion_id, negocio_id=negocio_id)
    token, invitacion.hash_token = generar_token_de_invitacion()
    invitacion.expira_en = _vencimiento()
    invitacion.save(update_fields=["hash_token", "expira_en", "actualizado_en"])

    transaction.on_commit(lambda: correos.enviar_invitacion(invitacion=invitacion, token=token))
    return invitacion


def revocar_invitacion(*, invitacion_id: int, negocio_id: int) -> None:
    """Cancela una invitación que todavía nadie usó.

    Aquí sí se borra la fila, y es la excepción a "nada se borra": una
    invitación pendiente no es historia de nadie —no hay usuario, no hay
    movimiento— y dejarla marcada como vencida bloquearía la restricción de
    "una sola invitación pendiente por correo", que es justo lo que impediría
    volver a invitar a esa persona.

    Las ya aceptadas no se tocan: esas sí son el registro de quién dio de alta
    a quién.
    """
    invitacion = _obtener_pendiente_del_negocio(invitacion_id=invitacion_id, negocio_id=negocio_id)
    invitacion.delete()


@transaction.atomic
def aceptar_invitacion(*, datos: AceptacionDeInvitacionDTO) -> SesionDTO:
    """Crea el usuario a partir de la invitación y lo deja dentro.

    El correo y el rol salen de la invitación, nunca del formulario.

    Devuelve la sesión abierta en vez de mandar a la pantalla de acceso:
    quien llega hasta aquí acaba de demostrar que el correo es suyo y de
    elegir su contraseña: pedirle que la escriba otra vez no comprueba nada.

    Raises:
        InvitacionNoEncontrada, InvitacionVencida, InvitacionYaAceptada.
        CorreoYaRegistrado: alguien creó esa cuenta mientras tanto.
        ContrasenaInsegura: la contraseña elegida no pasa los validadores.
    """
    invitacion = obtener_pendiente_por_token(token=datos.token)
    if repositorio_de_usuarios.existe_con_correo(correo=invitacion.correo):
        raise CorreoYaRegistrado

    validar_contrasena(contrasena=datos.contrasena)
    usuario = repositorio_de_usuarios.crear_verificado(
        correo=invitacion.correo,
        contrasena=datos.contrasena,
        negocio_id=invitacion.negocio_id,
        rol=invitacion.rol,
        datos_personales={
            "nombre": datos.nombre,
            "apellido": datos.apellido,
            "telefono": datos.telefono,
        },
    )

    invitacion.aceptada_en = timezone.now()
    invitacion.aceptada_por = usuario
    invitacion.save(update_fields=["aceptada_en", "aceptada_por", "actualizado_en"])
    return sesiones.abrir_sesion(usuario=usuario)


def _obtener_pendiente_del_negocio(*, invitacion_id: int, negocio_id: int) -> Invitacion:
    invitacion = repositorio.obtener_del_negocio(invitacion_id=invitacion_id, negocio_id=negocio_id)
    if invitacion is None:
        raise InvitacionNoEncontrada
    if invitacion.aceptada_en is not None:
        raise InvitacionYaAceptada
    return invitacion


def _vencimiento():
    return timezone.now() + timedelta(days=settings.VIGENCIA_INVITACION_DIAS)
