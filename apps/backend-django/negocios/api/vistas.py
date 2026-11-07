"""Capa HTTP de los negocios.

Dos públicos distintos, y por eso dos sitios:

* **El staff de la plataforma** da de alta negocios, los corrige, los suspende
  y los reactiva. No pertenece a ninguno.
* **La gente de un negocio** solo ve el suyo, y su administrador ve además el
  resumen de ventas por canal.

Ningún endpoint deja elegir de qué negocio se habla: o eres staff y lo dices
por id, o eres del equipo y sale de tu propia cuenta.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from negocios.api import serializers
from negocios.models import Negocio
from negocios.permisos import EsStaffDePlataforma
from negocios.selectores import (
    negocio_del_usuario,
    negocios_de_la_plataforma,
    resumen_de_ventas,
)
from negocios.servicios import negocios as servicio
from nucleo.api.vistas import MixinDelNegocio
from nucleo.permisos import EsAdministrador, EsDelEquipo


class NegocioViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """/api/v1/negocios/ — la administración de la plataforma.

    No usa `MixinDelNegocio` a propósito: el staff no tiene negocio, y aquí el
    negocio es la fila que se administra, no el dueño de la fila.
    """

    serializer_class = serializers.NegocioOutputSerializer
    permission_classes = [EsStaffDePlataforma]
    lookup_value_regex = "[0-9]+"
    queryset = Negocio.objects.none()

    def get_queryset(self):
        return negocios_de_la_plataforma()

    @extend_schema(summary="Listar los negocios de la plataforma")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver un negocio")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Dar de alta un negocio",
        description=(
            "Nace vacío. A su primer administrador se le invita desde la "
            "terminal: `manage invitar_administrador --negocio <id> --correo <correo>`."
        ),
        request=serializers.NegocioInputSerializer,
        responses={201: serializers.NegocioOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(request)
        negocio = servicio.crear_negocio(**datos)
        return Response(
            serializers.NegocioOutputSerializer(negocio).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Corregir los datos de un negocio",
        request=serializers.NegocioInputSerializer,
        responses={200: serializers.NegocioOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        datos = self._validado(request)
        negocio = servicio.actualizar_datos(negocio_id=int(pk), **datos)
        return Response(serializers.NegocioOutputSerializer(negocio).data)

    @extend_schema(
        summary="Suspender un negocio",
        description="Su gente deja de poder entrar. Los datos siguen enteros.",
        request=None,
        responses={200: serializers.NegocioOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="suspension")
    def suspension(self, request: Request, pk: str) -> Response:
        negocio = servicio.suspender_negocio(negocio_id=int(pk))
        return Response(serializers.NegocioOutputSerializer(negocio).data)

    @extend_schema(
        summary="Reactivar un negocio",
        request=None,
        responses={200: serializers.NegocioOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reactivacion")
    def reactivacion(self, request: Request, pk: str) -> Response:
        negocio = servicio.reactivar_negocio(negocio_id=int(pk))
        return Response(serializers.NegocioOutputSerializer(negocio).data)

    def _validado(self, request: Request) -> dict:
        entrada = serializers.NegocioInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return entrada.validated_data


class MiNegocioView(APIView):
    """GET /api/v1/negocios/mio/ — el negocio de quien pregunta.

    Lo mira cualquiera del equipo: es lo que pinta el nombre del bar en la
    pantalla. Sale del usuario autenticado, nunca de la petición.
    """

    permission_classes = [EsDelEquipo]

    @extend_schema(
        summary="Ver mi negocio",
        responses={200: serializers.NegocioOutputSerializer},
    )
    def get(self, request: Request) -> Response:
        negocio = negocio_del_usuario(usuario_id=request.user.id)
        return Response(serializers.NegocioOutputSerializer(negocio).data)


class ResumenDeVentasView(MixinDelNegocio, APIView):
    """GET /api/v1/negocios/informes/ventas/ — cuánto puso cada canal.

    Es del administrador: es la cifra del negocio, no la de una noche.
    """

    permission_classes = [EsAdministrador]

    @extend_schema(
        summary="Ver el resumen de ventas por canal",
        description=(
            "Lo vendido y lo cobrado por la barra y por el mayoreo. Sin fechas, "
            "el mes en curso. `vendido` y `cobrado` no tienen por qué coincidir: "
            "el mayoreo vende a crédito."
        ),
        parameters=[serializers.RangoDeFechasSerializer],
        responses={200: serializers.ResumenDeVentasOutputSerializer},
    )
    def get(self, request: Request) -> Response:
        entrada = serializers.RangoDeFechasSerializer(data=request.query_params)
        entrada.is_valid(raise_exception=True)

        resumen = resumen_de_ventas(negocio_id=self.negocio_id, **entrada.validated_data)
        return Response(serializers.ResumenDeVentasOutputSerializer(resumen).data)
