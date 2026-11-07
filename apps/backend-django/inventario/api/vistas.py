"""Capa HTTP del inventario.

El reparto de permisos sale del plan de negocio: **mover mercancía es de
administrador**, pero el equipo entero **lee** las existencias — un mesero tiene
que poder mirar si queda cerveza sin poder tocar el kardex. Las existencias no
se mueven a mano al vender: se mueven solas, desde `servicios/consumo.py`.
"""

from decimal import Decimal

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from inventario.api import filtros, serializers
from inventario.dtos import LineaDeProductoDTO
from inventario.models import Existencia, MovimientoInventario, Ubicacion
from inventario.selectores import existencias as selector
from inventario.servicios import ajustes as servicio_de_ajustes
from inventario.servicios import operaciones
from inventario.servicios import ubicaciones as servicio_de_ubicaciones
from nucleo.api.vistas import MixinDelNegocio
from nucleo.permisos import EsAdministrador, EsDelEquipo

# Lo que puede hacer cualquiera del equipo. Todo lo demás es de administrador.
SOLO_LECTURA = frozenset({"list", "retrieve", "bajo_minimo"})


class _ViewSetDeLectura(MixinDelNegocio, mixins.ListModelMixin, GenericViewSet):
    """Lee cualquiera del equipo; escribe solo el administrador."""

    lookup_value_regex = "[0-9]+"

    def get_permissions(self):
        if self.action in SOLO_LECTURA:
            return [EsDelEquipo()]
        return [EsAdministrador()]

    def _lineas(self, datos: list[dict]) -> list[LineaDeProductoDTO]:
        return [
            LineaDeProductoDTO(producto_id=linea["producto_id"], cantidad=linea["cantidad"])
            for linea in datos
        ]


# --------------------------------------------------------------------------- #
# Ubicaciones
# --------------------------------------------------------------------------- #
class UbicacionViewSet(_ViewSetDeLectura, mixins.RetrieveModelMixin):
    """/api/v1/inventario/ubicaciones/"""

    serializer_class = serializers.UbicacionOutputSerializer
    filterset_class = filtros.UbicacionFiltro
    # Solo para que drf-spectacular sepa de qué modelo es el listado: el
    # queryset de verdad lo arma `get_queryset` con el negocio del usuario.
    queryset = Ubicacion.objects.none()

    def get_queryset(self):
        return selector.ubicaciones_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las ubicaciones del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una ubicación")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Crear una ubicación",
        request=serializers.UbicacionInputSerializer,
        responses={201: serializers.UbicacionOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        entrada = serializers.UbicacionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        ubicacion = servicio_de_ubicaciones.crear_ubicacion(
            negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(
            serializers.UbicacionOutputSerializer(ubicacion).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Cambiar una ubicación",
        request=serializers.UbicacionInputSerializer,
        responses={200: serializers.UbicacionOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        entrada = serializers.UbicacionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        ubicacion = servicio_de_ubicaciones.actualizar_ubicacion(
            ubicacion_id=int(pk), negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(serializers.UbicacionOutputSerializer(ubicacion).data)

    @extend_schema(
        summary="Desactivar una ubicación",
        description="No se borra: el kardex histórico la sigue nombrando.",
        request=None,
        responses={200: serializers.UbicacionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="desactivacion")
    def desactivacion(self, request: Request, pk: str) -> Response:
        ubicacion = servicio_de_ubicaciones.desactivar_ubicacion(
            ubicacion_id=int(pk), negocio_id=self.negocio_id
        )
        return Response(serializers.UbicacionOutputSerializer(ubicacion).data)


# --------------------------------------------------------------------------- #
# Existencias
# --------------------------------------------------------------------------- #
class ExistenciaViewSet(_ViewSetDeLectura):
    """/api/v1/inventario/existencias/ — lo que hay, y dónde.

    Se lee, no se escribe: las existencias las mueve el kardex. Lo único que se
    fija a mano es el punto de reposición.
    """

    serializer_class = serializers.ExistenciaOutputSerializer
    filterset_class = filtros.ExistenciaFiltro
    queryset = Existencia.objects.none()

    def get_queryset(self):
        return (
            Existencia.objects.filter(negocio_id=self.negocio_id)
            .select_related("producto", "ubicacion")
            .order_by("ubicacion__nombre", "producto__nombre")
        )

    @extend_schema(summary="Ver las existencias del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Ver qué hay que reponer",
        description="Solo lo que tiene mínimo puesto: un cero es «sin alerta».",
        responses={200: serializers.ExistenciaOutputSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="bajo-minimo")
    def bajo_minimo(self, request: Request) -> Response:
        pagina = self.paginate_queryset(selector.productos_bajo_minimo(negocio_id=self.negocio_id))
        salida = serializers.ExistenciaOutputSerializer(pagina, many=True)
        return self.get_paginated_response(salida.data)

    @extend_schema(
        summary="Fijar el punto de reposición",
        description=(
            "Es por ubicación y no por producto: veinte cervezas en la barra es "
            "alerta y en la bodega no."
        ),
        request=serializers.CantidadMinimaInputSerializer,
        responses={200: serializers.ExistenciaOutputSerializer},
    )
    @action(detail=False, methods=["post"], url_path="minimo")
    def minimo(self, request: Request) -> Response:
        entrada = serializers.CantidadMinimaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        existencia = servicio_de_ubicaciones.fijar_cantidad_minima(
            negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(serializers.ExistenciaOutputSerializer(existencia).data)


# --------------------------------------------------------------------------- #
# Movimientos
# --------------------------------------------------------------------------- #
class MovimientoViewSet(_ViewSetDeLectura):
    """/api/v1/inventario/movimientos/ — el kardex y las operaciones que lo escriben.

    Todo aquí es de administrador, lectura incluida: el kardex es lo que dice
    dónde se perdieron doce cervezas, y esa conversación no es de la barra.
    """

    serializer_class = serializers.MovimientoOutputSerializer
    filterset_class = filtros.MovimientoFiltro
    queryset = MovimientoInventario.objects.none()
    permission_classes = [EsAdministrador]

    def get_permissions(self):
        return [EsAdministrador()]

    def get_queryset(self):
        return MovimientoInventario.objects.filter(negocio_id=self.negocio_id).select_related(
            "producto", "ubicacion", "usuario"
        )

    @extend_schema(
        summary="Ver el kardex",
        description="Filtrando por `producto` sale la historia de un producto.",
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar entrada de mercancía",
        request=serializers.OperacionInputSerializer,
        responses={201: serializers.MovimientoOutputSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="entradas")
    def entradas(self, request: Request) -> Response:
        datos = self._validar(serializers.OperacionInputSerializer, request)
        movimientos = operaciones.registrar_entrada_de_mercancia(
            ubicacion_id=datos["ubicacion_id"],
            lineas=self._lineas(datos["lineas"]),
            usuario_id=request.user.id,
            negocio_id=self.negocio_id,
            nota=datos["nota"],
        )
        return self._creados(movimientos)

    @extend_schema(
        summary="Registrar una salida a mano",
        description="Las ventas no pasan por aquí: descuentan solas al crear la comanda.",
        request=serializers.OperacionInputSerializer,
        responses={201: serializers.MovimientoOutputSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="salidas")
    def salidas(self, request: Request) -> Response:
        datos = self._validar(serializers.OperacionInputSerializer, request)
        movimientos = operaciones.registrar_salida(
            ubicacion_id=datos["ubicacion_id"],
            lineas=self._lineas(datos["lineas"]),
            usuario_id=request.user.id,
            negocio_id=self.negocio_id,
            nota=datos["nota"],
        )
        return self._creados(movimientos)

    @extend_schema(
        summary="Registrar una merma",
        description="Lo que se rompió, se derramó o se venció. El motivo es obligatorio.",
        request=serializers.MermaInputSerializer,
        responses={201: serializers.MovimientoOutputSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="mermas")
    def mermas(self, request: Request) -> Response:
        datos = self._validar(serializers.MermaInputSerializer, request)
        movimientos = operaciones.registrar_merma(
            ubicacion_id=datos["ubicacion_id"],
            lineas=self._lineas(datos["lineas"]),
            usuario_id=request.user.id,
            negocio_id=self.negocio_id,
            motivo=datos["motivo"],
        )
        return self._creados(movimientos)

    @extend_schema(
        summary="Trasladar entre ubicaciones",
        description="Deja **dos** filas de kardex con la misma referencia, no una.",
        request=serializers.TrasladoInputSerializer,
        responses={201: serializers.MovimientoOutputSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="traslados")
    def traslados(self, request: Request) -> Response:
        datos = self._validar(serializers.TrasladoInputSerializer, request)
        movimientos = operaciones.transferir_entre_ubicaciones(
            usuario_id=request.user.id, negocio_id=self.negocio_id, **datos
        )
        return self._creados(movimientos)

    @extend_schema(
        summary="Ajustar por conteo físico",
        description=(
            "Se manda **lo contado**, no la diferencia. Si el conteo coincide "
            "devuelve `204`: un movimiento de cero no es un movimiento."
        ),
        request=serializers.AjusteInputSerializer,
        responses={201: serializers.MovimientoOutputSerializer, 204: None},
    )
    @action(detail=False, methods=["post"], url_path="ajustes")
    def ajustes(self, request: Request) -> Response:
        datos = self._validar(serializers.AjusteInputSerializer, request)
        movimiento = servicio_de_ajustes.ajustar_existencias(
            usuario_id=request.user.id, negocio_id=self.negocio_id, **datos
        )
        if movimiento is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            serializers.MovimientoOutputSerializer(movimiento).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Reconstruir el saldo desde el kardex",
        description=(
            "Repara un saldo cacheado que se desvió. **No crea movimiento**: "
            "inventarlo falsearía la historia de la mercancía. Que haga falta "
            "llamarla es el síntoma de un bug, y queda un WARNING en los logs."
        ),
        request=serializers.ReconstruccionInputSerializer,
        responses={200: serializers.ExistenciaOutputSerializer},
    )
    @action(detail=False, methods=["post"], url_path="reconstruccion")
    def reconstruccion(self, request: Request) -> Response:
        datos = self._validar(serializers.ReconstruccionInputSerializer, request)
        existencia = servicio_de_ajustes.reconstruir_saldo_desde_kardex(
            negocio_id=self.negocio_id, **datos
        )
        return Response(serializers.ExistenciaOutputSerializer(existencia).data)

    @extend_schema(
        summary="Anular un movimiento",
        description=(
            "Crea el movimiento contrario; **nunca borra**. Puede fallar con "
            "`existencias_insuficientes` si lo que entró de más ya se vendió."
        ),
        request=serializers.MotivoInputSerializer,
        responses={201: serializers.MovimientoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="anulacion")
    def anulacion(self, request: Request, pk: str) -> Response:
        datos = self._validar(serializers.MotivoInputSerializer, request)
        contrario = operaciones.anular_movimiento(
            movimiento_id=int(pk),
            negocio_id=self.negocio_id,
            usuario_id=request.user.id,
            motivo=datos["motivo"],
        )
        return Response(
            serializers.MovimientoOutputSerializer(contrario).data,
            status=status.HTTP_201_CREATED,
        )

    def _validar(self, serializer, request: Request) -> dict:
        entrada = serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return entrada.validated_data

    def _creados(self, movimientos: "list[MovimientoInventario]") -> Response:
        return Response(
            serializers.MovimientoOutputSerializer(movimientos, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class ValorizacionView(MixinDelNegocio, APIView):
    """GET /api/v1/inventario/valorizacion/ — lo que vale el inventario a costo."""

    permission_classes = [EsAdministrador]

    @extend_schema(
        summary="Valorizar el inventario",
        description="A precio de costo. Lo multiplica y lo suma la base de datos.",
        responses={200: serializers.ValorizacionOutputSerializer},
    )
    def get(self, request: Request) -> Response:
        total: Decimal = selector.valorizacion_del_inventario(negocio_id=self.negocio_id)
        return Response(serializers.ValorizacionOutputSerializer({"total": total}).data)
