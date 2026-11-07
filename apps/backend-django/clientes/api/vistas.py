"""Capa HTTP de las fichas de cliente.

Los permisos no son los mismos para todo, y es la decisión 6 del plan: el
mesero y el cajero **registran y buscan** clientes, porque eso es lo que hacen
en la barra toda la noche; **desactivar** una ficha es de administrador.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from clientes.api import filtros, serializers
from clientes.dtos import DatosDeClienteDTO
from clientes.models import Cliente
from clientes.selectores import clientes as selector
from clientes.selectores import historial_de_consumo
from clientes.servicios import clientes as servicio
from nucleo.api.vistas import MixinDelNegocio
from nucleo.permisos import EsAdministrador, EsDelEquipo

# Lo que solo puede hacer el administrador. Lo demás lo hace cualquiera del
# equipo: quien registra al cliente es quien está en la barra.
ACCIONES_DE_ADMINISTRADOR = frozenset({"desactivacion"})


class ClienteViewSet(
    MixinDelNegocio, mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    """/api/v1/clientes/"""

    serializer_class = serializers.ClienteOutputSerializer
    filterset_class = filtros.ClienteFiltro
    lookup_value_regex = "[0-9]+"
    # Solo para que drf-spectacular sepa de qué modelo es el listado: el
    # queryset de verdad lo arma `get_queryset` con el negocio del usuario.
    queryset = Cliente.objects.none()

    def get_permissions(self):
        if self.action in ACCIONES_DE_ADMINISTRADOR:
            return [EsAdministrador()]
        return [EsDelEquipo()]

    def get_queryset(self):
        return selector.clientes_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar los clientes del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una ficha de cliente")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar un cliente",
        description=(
            "Ser menor de edad **no impide** crear la ficha: la respuesta trae "
            "`es_menor_de_edad` para que la pantalla lo avise."
        ),
        request=serializers.ClienteInputSerializer,
        responses={201: serializers.ClienteOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        entrada = serializers.ClienteInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        cliente = servicio.registrar_cliente(
            negocio_id=self.negocio_id,
            datos=DatosDeClienteDTO(**entrada.validated_data),
        )
        return Response(
            serializers.ClienteOutputSerializer(cliente).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Corregir una ficha de cliente",
        request=serializers.ClienteInputSerializer,
        responses={200: serializers.ClienteOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        entrada = serializers.ClienteInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        cliente = servicio.actualizar_cliente(
            cliente_id=int(pk),
            negocio_id=self.negocio_id,
            datos=DatosDeClienteDTO(**entrada.validated_data),
        )
        return Response(serializers.ClienteOutputSerializer(cliente).data)

    @extend_schema(
        summary="Desactivar una ficha",
        description="No se borra: sus cuentas y comandas la siguen necesitando.",
        request=None,
        responses={200: serializers.ClienteOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="desactivacion")
    def desactivacion(self, request: Request, pk: str) -> Response:
        cliente = servicio.desactivar_cliente(cliente_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.ClienteOutputSerializer(cliente).data)

    @extend_schema(
        summary="Buscar por documento",
        description=(
            "Lo que se hace en la barra antes de abrir una cuenta: si la persona "
            "ya vino, es la misma ficha con su historial."
        ),
        parameters=[serializers.BusquedaPorDocumentoSerializer],
        responses={200: serializers.ClienteOutputSerializer},
    )
    @action(detail=False, methods=["get"], url_path="por-documento")
    def por_documento(self, request: Request) -> Response:
        entrada = serializers.BusquedaPorDocumentoSerializer(data=request.query_params)
        entrada.is_valid(raise_exception=True)

        cliente = selector.buscar_por_documento(
            negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(serializers.ClienteOutputSerializer(cliente).data)

    @extend_schema(
        summary="Ver el historial de consumo",
        description="Las cuentas que ha tenido y cuánto consumió en cada una.",
        responses={200: serializers.CuentaDelHistorialSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="historial")
    def historial(self, request: Request, pk: str) -> Response:
        cuentas = historial_de_consumo(cliente_id=int(pk), negocio_id=self.negocio_id)
        pagina = self.paginate_queryset(cuentas)
        salida = serializers.CuentaDelHistorialSerializer(pagina, many=True)
        return self.get_paginated_response(salida.data)
