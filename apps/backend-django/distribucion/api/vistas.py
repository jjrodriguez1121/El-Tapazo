"""Capa HTTP del canal mayorista.

**Todo es de administrador** (decisión 6 del plan): el mayoreo mueve crédito y
bodega, no la operación de una noche. El cajero y el mesero no entran aquí.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from distribucion.api import filtros, serializers
from distribucion.dtos import DatosDeClienteDistribucionDTO, LineaDePedidoDTO
from distribucion.models import ClienteDistribucion, PedidoDistribucion
from distribucion.selectores import clientes as selector_de_clientes
from distribucion.selectores import (
    clientes_en_mora,
    pagos_de_un_pedido,
    pedidos_del_cliente,
    saldo_de_un_cliente,
    saldo_de_un_pedido,
)
from distribucion.selectores import pedidos as selector_de_pedidos
from distribucion.servicios import clientes as servicio_de_clientes
from distribucion.servicios import pagos as servicio_de_pagos
from distribucion.servicios import pedidos as servicio_de_pedidos
from nucleo.api.vistas import MixinDelNegocio
from nucleo.permisos import EsAdministrador


class _ViewSetMayorista(
    MixinDelNegocio, mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    lookup_value_regex = "[0-9]+"
    permission_classes = [EsAdministrador]

    def _validado(self, serializer, request: Request) -> dict:
        entrada = serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return entrada.validated_data


# --------------------------------------------------------------------------- #
# Tiendas cliente
# --------------------------------------------------------------------------- #
class ClienteDistribucionViewSet(_ViewSetMayorista):
    """/api/v1/distribucion/clientes/ — las tiendas a las que se les vende."""

    serializer_class = serializers.ClienteDistribucionOutputSerializer
    filterset_class = filtros.ClienteDistribucionFiltro
    # Solo para que drf-spectacular sepa de qué modelo es el listado: el
    # queryset de verdad lo arma `get_queryset` con el negocio del usuario.
    queryset = ClienteDistribucion.objects.none()

    def get_queryset(self):
        return selector_de_clientes.clientes_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las tiendas cliente")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una tienda cliente")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Dar de alta una tienda",
        request=serializers.ClienteDistribucionInputSerializer,
        responses={201: serializers.ClienteDistribucionOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.ClienteDistribucionInputSerializer, request)
        cliente = servicio_de_clientes.registrar_cliente(
            negocio_id=self.negocio_id, datos=DatosDeClienteDistribucionDTO(**datos)
        )
        return Response(
            serializers.ClienteDistribucionOutputSerializer(cliente).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Corregir la ficha de una tienda",
        description="Cambiar los días de crédito cambia el vencimiento de lo que ya debe.",
        request=serializers.ClienteDistribucionInputSerializer,
        responses={200: serializers.ClienteDistribucionOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.ClienteDistribucionInputSerializer, request)
        cliente = servicio_de_clientes.actualizar_cliente(
            cliente_id=int(pk),
            negocio_id=self.negocio_id,
            datos=DatosDeClienteDistribucionDTO(**datos),
        )
        return Response(serializers.ClienteDistribucionOutputSerializer(cliente).data)

    @extend_schema(
        summary="Desactivar una tienda",
        description="No se borra: sus pedidos históricos la siguen nombrando.",
        request=None,
        responses={200: serializers.ClienteDistribucionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="desactivacion")
    def desactivacion(self, request: Request, pk: str) -> Response:
        cliente = servicio_de_clientes.desactivar_cliente(
            cliente_id=int(pk), negocio_id=self.negocio_id
        )
        return Response(serializers.ClienteDistribucionOutputSerializer(cliente).data)

    @extend_schema(
        summary="Ver los pedidos de una tienda",
        responses={200: serializers.PedidoDistribucionOutputSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="pedidos")
    def pedidos(self, request: Request, pk: str) -> Response:
        pedidos = pedidos_del_cliente(cliente_id=int(pk), negocio_id=self.negocio_id)
        pagina = self.paginate_queryset(pedidos)
        salida = serializers.PedidoDistribucionOutputSerializer(pagina, many=True)
        return self.get_paginated_response(salida.data)

    @extend_schema(
        summary="Ver lo que debe una tienda",
        description="Todo lo que debe, esté vencido o no. Lo cancelado no cuenta.",
        responses={200: serializers.SaldoDelClienteOutputSerializer},
    )
    @action(detail=True, methods=["get"], url_path="saldo")
    def saldo(self, request: Request, pk: str) -> Response:
        debe = saldo_de_un_cliente(cliente_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.SaldoDelClienteOutputSerializer({"saldo": debe}).data)

    @extend_schema(
        summary="Listar las tiendas en mora",
        description=(
            "A quién hay que cobrarle: se le pasó el plazo y todavía debe. "
            "`deuda_vencida` es lo vencido, no lo que debe en total."
        ),
        responses={200: serializers.ClienteEnMoraOutputSerializer(many=True)},
        filters=False,
    )
    @action(detail=False, methods=["get"], url_path="mora")
    def mora(self, request: Request) -> Response:
        morosos = clientes_en_mora(negocio_id=self.negocio_id)
        pagina = self.paginate_queryset(morosos)
        salida = serializers.ClienteEnMoraOutputSerializer(pagina, many=True)
        return self.get_paginated_response(salida.data)


# --------------------------------------------------------------------------- #
# Pedidos
# --------------------------------------------------------------------------- #
class PedidoDistribucionViewSet(_ViewSetMayorista):
    """/api/v1/distribucion/pedidos/ — la orden mayorista, de la toma a la entrega."""

    serializer_class = serializers.PedidoDistribucionOutputSerializer
    filterset_class = filtros.PedidoDistribucionFiltro
    queryset = PedidoDistribucion.objects.none()

    def get_queryset(self):
        return selector_de_pedidos.pedidos_del_negocio(negocio_id=self.negocio_id).prefetch_related(
            "detalles__producto"
        )

    @extend_schema(summary="Listar los pedidos mayoristas")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver un pedido mayorista")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Tomar un pedido",
        description=(
            "Congela el precio mayorista de cada línea y **no toca el stock**: "
            "un pedido pendiente todavía no salió de la bodega."
        ),
        request=serializers.PedidoMayoristaInputSerializer,
        responses={201: serializers.PedidoDistribucionOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.PedidoMayoristaInputSerializer, request)
        pedido = servicio_de_pedidos.crear_pedido(
            cliente_distribucion_id=datos["cliente_distribucion_id"],
            lineas=[
                LineaDePedidoDTO(producto_id=linea["producto_id"], cantidad=linea["cantidad"])
                for linea in datos["lineas"]
            ],
            usuario_id=request.user.id,
            negocio_id=self.negocio_id,
        )
        return Response(
            serializers.PedidoDistribucionOutputSerializer(pedido).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Despachar el pedido",
        description=(
            "Carga el camión y descuenta la mercancía de esa bodega. Un pedido "
            "que volvió sin entregarse se vuelve a despachar por aquí."
        ),
        request=serializers.DespachoInputSerializer,
        responses={200: serializers.PedidoDistribucionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="despacho")
    def despacho(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.DespachoInputSerializer, request)
        pedido = servicio_de_pedidos.despachar_pedido(
            pedido_id=int(pk),
            negocio_id=self.negocio_id,
            usuario_id=request.user.id,
            **datos,
        )
        return Response(serializers.PedidoDistribucionOutputSerializer(pedido).data)

    @extend_schema(
        summary="Entregar el pedido",
        description="Desde aquí corre el plazo de crédito. El stock ya salió al despachar.",
        request=None,
        responses={200: serializers.PedidoDistribucionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="entrega")
    def entrega(self, request: Request, pk: str) -> Response:
        pedido = servicio_de_pedidos.entregar_pedido(pedido_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.PedidoDistribucionOutputSerializer(pedido).data)

    @extend_schema(
        summary="Marcar el pedido como no entregado",
        description=(
            "La mercancía vuelve al inventario **en el acto**, no cuando llegue "
            "el camión, y el pedido se puede volver a despachar."
        ),
        request=serializers.MotivoDeNoEntregaInputSerializer,
        responses={200: serializers.PedidoDistribucionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="no-entrega")
    def no_entrega(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.MotivoDeNoEntregaInputSerializer, request)
        pedido = servicio_de_pedidos.marcar_no_entregado(
            pedido_id=int(pk),
            negocio_id=self.negocio_id,
            usuario_id=request.user.id,
            motivo=datos["motivo"],
        )
        return Response(serializers.PedidoDistribucionOutputSerializer(pedido).data)

    @extend_schema(
        summary="Cancelar el pedido",
        description=(
            "Solo con la mercancía en la bodega: pendiente o no entregado. "
            "Desde «en ruta» hay que marcar primero la no entrega."
        ),
        request=None,
        responses={200: serializers.PedidoDistribucionOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cancelacion")
    def cancelacion(self, request: Request, pk: str) -> Response:
        pedido = servicio_de_pedidos.cancelar_pedido(pedido_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.PedidoDistribucionOutputSerializer(pedido).data)

    @extend_schema(
        summary="Ver el saldo del pedido",
        responses={200: serializers.SaldoDelPedidoOutputSerializer},
    )
    @action(detail=True, methods=["get"], url_path="saldo")
    def saldo(self, request: Request, pk: str) -> Response:
        saldo = saldo_de_un_pedido(pedido_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.SaldoDelPedidoOutputSerializer(saldo).data)

    @extend_schema(
        summary="Ver los abonos del pedido",
        responses={200: serializers.PagoDistribucionOutputSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="abonos")
    def abonos(self, request: Request, pk: str) -> Response:
        pagos = pagos_de_un_pedido(pedido_id=int(pk), negocio_id=self.negocio_id)
        pagina = self.paginate_queryset(pagos)
        salida = serializers.PagoDistribucionOutputSerializer(pagina, many=True)
        return self.get_paginated_response(salida.data)

    @extend_schema(
        summary="Registrar un abono",
        description="Aquí sí hay abonos: una tienda a 30 días paga en varias veces.",
        request=serializers.AbonoInputSerializer,
        responses={201: serializers.ResultadoDeAbonoOutputSerializer},
    )
    @abonos.mapping.post
    def registrar_abono(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.AbonoInputSerializer, request)
        resultado = servicio_de_pagos.registrar_pago(
            pedido_id=int(pk),
            negocio_id=self.negocio_id,
            recibido_por_id=request.user.id,
            **datos,
        )
        return Response(
            serializers.ResultadoDeAbonoOutputSerializer(resultado).data,
            status=status.HTTP_201_CREATED,
        )
