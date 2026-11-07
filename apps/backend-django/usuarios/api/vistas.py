"""Capa HTTP de identidad y acceso.

Cada vista hace lo mismo: valida el formato con un serializer, llama a un
servicio y devuelve la respuesta. Ninguna decide nada — las reglas están en
`usuarios/servicios/`, y los errores los traduce el manejador global de
`nucleo/excepciones/`.

Los endpoints públicos llevan `AllowAny` escrito a mano: el proyecto exige
autenticación por defecto, así que abrir uno es una decisión consciente. Son
justo los que no pueden exigirla —quien va a iniciar sesión todavía no la
tiene— y por eso los que escriben van con freno de peticiones.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from nucleo.permisos import EsAdministrador
from usuarios.api import serializers
from usuarios.dtos import AceptacionDeInvitacionDTO
from usuarios.models import Invitacion
from usuarios.selectores import invitaciones as selector
from usuarios.servicios import contrasenas, sesiones, verificacion_correo
from usuarios.servicios import invitaciones as servicio


# --------------------------------------------------------------------------- #
# Sesión
# --------------------------------------------------------------------------- #
class InicioDeSesionView(APIView):
    """POST /api/v1/usuarios/sesiones/ — entrar al sistema."""

    permission_classes = [AllowAny]
    throttle_scope = "inicio_sesion"

    @extend_schema(
        summary="Iniciar sesión",
        request=serializers.InicioDeSesionInputSerializer,
        responses={201: serializers.SesionOutputSerializer},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.InicioDeSesionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        sesion = sesiones.iniciar_sesion(**entrada.validated_data)
        return Response(
            serializers.SesionOutputSerializer(sesion).data,
            status=status.HTTP_201_CREATED,
        )


class RenovacionDeSesionView(APIView):
    """POST /api/v1/usuarios/sesiones/renovacion/ — acceso nuevo con el refresco."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Renovar la sesión",
        request=serializers.RefrescoInputSerializer,
        responses={200: serializers.TokensOutputSerializer},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.RefrescoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        acceso, refresco = sesiones.renovar_sesion(
            token_de_refresco=entrada.validated_data["refresco"]
        )
        salida = serializers.TokensOutputSerializer({"acceso": acceso, "refresco": refresco})
        return Response(salida.data)


class CierreDeSesionView(APIView):
    """POST /api/v1/usuarios/sesiones/cierre/ — anular el refresco."""

    @extend_schema(
        summary="Cerrar sesión",
        request=serializers.RefrescoInputSerializer,
        responses={204: None},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.RefrescoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        sesiones.cerrar_sesion(token_de_refresco=entrada.validated_data["refresco"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class UsuarioAutenticadoView(APIView):
    """GET /api/v1/usuarios/yo/ — quién soy, según el token que mandé."""

    @extend_schema(
        summary="Datos del usuario autenticado",
        responses={200: serializers.UsuarioOutputSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(serializers.UsuarioOutputSerializer(request.user).data)


# --------------------------------------------------------------------------- #
# Contraseña
# --------------------------------------------------------------------------- #
class SolicitudDeRecuperacionView(APIView):
    """POST /api/v1/usuarios/contrasena/recuperacion/ — "olvidé mi contraseña"."""

    permission_classes = [AllowAny]
    throttle_scope = "correos_salientes"

    @extend_schema(
        summary="Pedir el enlace para recuperar la contraseña",
        description=(
            "Responde 202 exista o no ese correo, y a propósito: si contestara "
            "distinto, serviría para averiguar qué correos tienen cuenta."
        ),
        request=serializers.CorreoInputSerializer,
        responses={202: None},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.CorreoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        contrasenas.solicitar_recuperacion(**entrada.validated_data)
        return Response(status=status.HTTP_202_ACCEPTED)


class NuevaContrasenaView(APIView):
    """POST /api/v1/usuarios/contrasena/restablecimiento/ — con el enlace del correo."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Elegir una contraseña nueva desde el enlace",
        request=serializers.NuevaContrasenaInputSerializer,
        responses={204: None},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.NuevaContrasenaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        contrasenas.restablecer_contrasena(
            uid=entrada.validated_data["uid"],
            token=entrada.validated_data["token"],
            contrasena_nueva=entrada.validated_data["contrasena"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CambioDeContrasenaView(APIView):
    """POST /api/v1/usuarios/contrasena/cambio/ — estando ya dentro."""

    @extend_schema(
        summary="Cambiar la contraseña",
        description=(
            "Cierra todas las sesiones abiertas y devuelve tokens nuevos: "
            "guárdalos y descarta los anteriores."
        ),
        request=serializers.CambioDeContrasenaInputSerializer,
        responses={200: serializers.SesionOutputSerializer},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.CambioDeContrasenaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        sesion = contrasenas.cambiar_contrasena(usuario=request.user, **entrada.validated_data)
        return Response(serializers.SesionOutputSerializer(sesion).data)


# --------------------------------------------------------------------------- #
# Verificación de correo
# --------------------------------------------------------------------------- #
class SolicitudDeVerificacionView(APIView):
    """POST /api/v1/usuarios/verificacion-correo/solicitud/ — reenviar el enlace."""

    permission_classes = [AllowAny]
    throttle_scope = "correos_salientes"

    @extend_schema(
        summary="Pedir otro enlace de verificación",
        description="Responde 202 exista o no ese correo, por el mismo motivo que la recuperación.",
        request=serializers.CorreoInputSerializer,
        responses={202: None},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.CorreoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        verificacion_correo.solicitar_verificacion(**entrada.validated_data)
        return Response(status=status.HTTP_202_ACCEPTED)


class ConfirmacionDeVerificacionView(APIView):
    """POST /api/v1/usuarios/verificacion-correo/confirmacion/ — con el enlace."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Confirmar el correo",
        description=(
            "El enlace sirve una sola vez. Abrirlo dos veces devuelve "
            "`enlace_invalido`: si ya se verificó, solo queda iniciar sesión."
        ),
        request=serializers.EnlaceInputSerializer,
        responses={204: None},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.EnlaceInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        verificacion_correo.confirmar_verificacion(**entrada.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Invitaciones
# --------------------------------------------------------------------------- #
class InvitacionViewSet(mixins.ListModelMixin, GenericViewSet):
    """Las invitaciones **del negocio de quien pregunta**.

    El `negocio_id` sale siempre del usuario autenticado, nunca de la URL ni
    del cuerpo: es lo que evita que un administrador vea o cancele las
    invitaciones de otro negocio.
    """

    permission_classes = [EsAdministrador]
    serializer_class = serializers.InvitacionOutputSerializer
    lookup_value_regex = "[0-9]+"
    # Solo para que drf-spectacular sepa de qué modelo es el listado: el
    # queryset de verdad lo arma `get_queryset` con el negocio del usuario.
    queryset = Invitacion.objects.none()

    def get_queryset(self):
        return selector.invitaciones_del_negocio(negocio_id=self.request.user.negocio_id)

    @extend_schema(summary="Listar las invitaciones del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Invitar a un trabajador",
        request=serializers.InvitacionInputSerializer,
        responses={201: serializers.InvitacionOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        entrada = serializers.InvitacionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        invitacion = servicio.crear_invitacion(
            negocio_id=request.user.negocio_id,
            invitada_por_id=request.user.id,
            **entrada.validated_data,
        )
        return Response(
            serializers.InvitacionOutputSerializer(invitacion).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="Cancelar una invitación pendiente", responses={204: None})
    def destroy(self, request: Request, pk: str) -> Response:
        servicio.revocar_invitacion(invitacion_id=int(pk), negocio_id=request.user.negocio_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Reenviar una invitación",
        description="Genera un enlace nuevo y anula el anterior.",
        request=None,
        responses={200: serializers.InvitacionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reenvio")
    def reenvio(self, request: Request, pk: str) -> Response:
        invitacion = servicio.reenviar_invitacion(
            invitacion_id=int(pk), negocio_id=request.user.negocio_id
        )
        return Response(serializers.InvitacionOutputSerializer(invitacion).data)


class InvitacionPendienteView(APIView):
    """GET /api/v1/usuarios/invitaciones/pendiente/?token=… — antes de aceptar."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Ver de qué es una invitación",
        description="Para pintar «te invitaron a X como mesero» antes de pedir la contraseña.",
        parameters=[serializers.TokenInputSerializer],
        responses={200: serializers.InvitacionPendienteOutputSerializer},
    )
    def get(self, request: Request) -> Response:
        entrada = serializers.TokenInputSerializer(data=request.query_params)
        entrada.is_valid(raise_exception=True)

        invitacion = selector.obtener_pendiente_por_token(**entrada.validated_data)
        return Response(serializers.InvitacionPendienteOutputSerializer(invitacion).data)


class AceptacionDeInvitacionView(APIView):
    """POST /api/v1/usuarios/invitaciones/aceptacion/ — crear la cuenta."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Aceptar la invitación y crear la cuenta",
        description="Devuelve la sesión ya abierta: no hace falta volver a iniciar sesión.",
        request=serializers.AceptacionDeInvitacionInputSerializer,
        responses={201: serializers.SesionOutputSerializer},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.AceptacionDeInvitacionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        sesion = servicio.aceptar_invitacion(
            datos=AceptacionDeInvitacionDTO(**entrada.validated_data)
        )
        return Response(
            serializers.SesionOutputSerializer(sesion).data,
            status=status.HTTP_201_CREATED,
        )
