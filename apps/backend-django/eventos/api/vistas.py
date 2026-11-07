"""Capa HTTP del canal evento/bar.

El reparto de permisos es la decisión 6 del plan, más las decisiones 10 y 11:

* **Abrir y cerrar la caja** — cajero y administrador. El mesero no.
* **Abrir grupos y cuentas, asignar pulseras, tomar y entregar comandas** — los
  tres roles. Es la operación de la barra.
* **Cobrar, liberar cuentas y cancelar comandas** — cajero y administrador.
  Cancelar devuelve stock y es una corrección de caja.
* **Registrar pulseras y dispositivos** — solo administrador.

El punto de control es aparte: lo consulta un aparato, no una persona.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from eventos.api import filtros, serializers
from eventos.api.autenticacion import AutenticacionDeDispositivo
from eventos.dtos import LineaDePedidoDTO
from eventos.models import (
    AlertaConsumo,
    ClienteEvento,
    DispositivoNfc,
    Evento,
    GrupoEvento,
    PedidoEvento,
    PulseraNfc,
)
from eventos.permisos import EsDispositivoNfc
from eventos.repositorios import pulseras as repositorio_de_pulseras
from eventos.selectores import (
    consultar_punto_de_control,
    consumo_de_un_grupo,
    consumo_de_una_cuenta,
    informe_de_cierre,
)
from eventos.selectores import eventos as selector
from eventos.servicios import alertas as servicio_de_alertas
from eventos.servicios import cuentas as servicio_de_cuentas
from eventos.servicios import jornadas as servicio_de_jornadas
from eventos.servicios import pagos as servicio_de_pagos
from eventos.servicios import pedidos as servicio_de_pedidos
from eventos.servicios import pulseras as servicio_de_pulseras
from nucleo.api.vistas import MixinDelNegocio
from nucleo.permisos import EsAdministrador, EsCajeroOAdministrador, EsDelEquipo


class _ViewSetDelEvento(MixinDelNegocio, mixins.ListModelMixin, GenericViewSet):
    lookup_value_regex = "[0-9]+"

    def _validado(self, serializer, request: Request) -> dict:
        entrada = serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return entrada.validated_data


# --------------------------------------------------------------------------- #
# La jornada (abrir y cerrar caja)
# --------------------------------------------------------------------------- #
class JornadaViewSet(_ViewSetDelEvento, mixins.RetrieveModelMixin):
    """/api/v1/eventos/jornadas/ — el cajero solo ve «abrir caja» y «cerrar caja»."""

    serializer_class = serializers.EventoOutputSerializer
    filterset_class = filtros.EventoFiltro
    permission_classes = [EsCajeroOAdministrador]
    queryset = Evento.objects.none()

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [EsDelEquipo()]
        return [EsCajeroOAdministrador()]

    def get_queryset(self):
        return selector.eventos_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las jornadas del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una jornada")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Abrir la caja",
        description=(
            "Devuelve la jornada en curso de esa ubicación y, si no hay, la abre. "
            "Nadie tiene que crear el evento a mano cada mañana."
        ),
        request=serializers.AperturaDeJornadaInputSerializer,
        responses={200: serializers.EventoOutputSerializer},
    )
    @action(detail=False, methods=["post"], url_path="apertura")
    def apertura(self, request: Request) -> Response:
        datos = self._validado(serializers.AperturaDeJornadaInputSerializer, request)
        jornada = servicio_de_jornadas.obtener_o_abrir_jornada(
            negocio_id=self.negocio_id, ubicacion_id=datos["ubicacion_id"]
        )
        return Response(serializers.EventoOutputSerializer(jornada).data)

    @extend_schema(
        summary="Cerrar la caja",
        description="Se bloquea si quedan cuentas sin saldar, y dice cuáles.",
        request=None,
        responses={200: serializers.EventoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cierre")
    def cierre(self, request: Request, pk: str) -> Response:
        jornada = servicio_de_jornadas.cerrar_jornada(evento_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.EventoOutputSerializer(jornada).data)

    @extend_schema(
        summary="Ver el informe de cierre",
        description="Ventas por producto, pagos por método y total cobrado.",
        responses={200: serializers.InformeDeCierreOutputSerializer},
    )
    @action(detail=True, methods=["get"], url_path="informe")
    def informe(self, request: Request, pk: str) -> Response:
        servicio_de_jornadas.obtener_jornada(evento_id=int(pk), negocio_id=self.negocio_id)
        datos = informe_de_cierre(evento_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.InformeDeCierreOutputSerializer(datos).data)


# --------------------------------------------------------------------------- #
# Grupos
# --------------------------------------------------------------------------- #
class GrupoViewSet(_ViewSetDelEvento):
    """/api/v1/eventos/grupos/ — la mesa. La abre cualquiera del equipo."""

    serializer_class = serializers.GrupoOutputSerializer
    filterset_class = filtros.GrupoFiltro
    permission_classes = [EsDelEquipo]
    queryset = GrupoEvento.objects.none()

    def get_queryset(self):
        return selector.grupos_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar los grupos")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Abrir un grupo",
        request=serializers.GrupoInputSerializer,
        responses={201: serializers.GrupoOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.GrupoInputSerializer, request)
        grupo = servicio_de_cuentas.abrir_grupo(
            negocio_id=self.negocio_id, abierto_por_id=request.user.id, **datos
        )
        return Response(
            serializers.GrupoOutputSerializer(grupo).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Cerrar un grupo",
        description="Las cuentas que sigan abiertas se liberan con él.",
        request=None,
        responses={200: serializers.GrupoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cierre")
    def cierre(self, request: Request, pk: str) -> Response:
        grupo = servicio_de_cuentas.cerrar_grupo(
            grupo_id=int(pk), negocio_id=self.negocio_id, cerrado_por_id=request.user.id
        )
        return Response(serializers.GrupoOutputSerializer(grupo).data)

    @extend_schema(
        summary="Ver lo consumido por el grupo",
        responses={200: serializers.ConsumoOutputSerializer},
    )
    @action(detail=True, methods=["get"], url_path="consumo")
    def consumo(self, request: Request, pk: str) -> Response:
        servicio_de_cuentas.obtener_grupo(grupo_id=int(pk), negocio_id=self.negocio_id)
        total = consumo_de_un_grupo(grupo_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.ConsumoOutputSerializer({"consumido": total}).data)

    @extend_schema(
        summary="Cobrar el grupo completo",
        description="Cierra el grupo y libera todas sus cuentas.",
        request=serializers.CobroInputSerializer,
        responses={201: serializers.ResultadoDeCobroOutputSerializer},
    )
    @action(
        detail=True, methods=["post"], url_path="cobro", permission_classes=[EsCajeroOAdministrador]
    )
    def cobro(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.CobroInputSerializer, request)
        resultado = servicio_de_pagos.registrar_pago_de_grupo(
            grupo_id=int(pk),
            negocio_id=self.negocio_id,
            recibido_por_id=request.user.id,
            **datos,
        )
        return Response(
            serializers.ResultadoDeCobroOutputSerializer(resultado).data,
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------------------------------- #
# Cuentas
# --------------------------------------------------------------------------- #
class CuentaViewSet(_ViewSetDelEvento, mixins.RetrieveModelMixin):
    """/api/v1/eventos/cuentas/ — la persona con su pulsera."""

    serializer_class = serializers.CuentaOutputSerializer
    filterset_class = filtros.CuentaFiltro
    permission_classes = [EsDelEquipo]
    queryset = ClienteEvento.objects.none()

    def get_queryset(self):
        return selector.cuentas_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las cuentas")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una cuenta")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Abrir una cuenta",
        description=(
            "La pulsera es opcional. Ser menor de edad **no impide** abrirla: la "
            "respuesta trae `es_menor_de_edad` para que la pantalla lo avise."
        ),
        request=serializers.CuentaInputSerializer,
        responses={201: serializers.CuentaOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.CuentaInputSerializer, request)
        cuenta = servicio_de_cuentas.abrir_cuenta(
            negocio_id=self.negocio_id, asignada_por_id=request.user.id, **datos
        )
        return Response(
            serializers.CuentaOutputSerializer(cuenta).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Ver lo consumido por la cuenta",
        responses={200: serializers.ConsumoOutputSerializer},
    )
    @action(detail=True, methods=["get"], url_path="consumo")
    def consumo(self, request: Request, pk: str) -> Response:
        servicio_de_cuentas.obtener_cuenta(cuenta_id=int(pk), negocio_id=self.negocio_id)
        total = consumo_de_una_cuenta(cliente_evento_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.ConsumoOutputSerializer({"consumido": total}).data)

    @extend_schema(
        summary="Liberar la cuenta sin cobrar",
        description="Para corregir; lo normal es que la libere el cobro.",
        request=None,
        responses={200: serializers.CuentaOutputSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="liberacion",
        permission_classes=[EsCajeroOAdministrador],
    )
    def liberacion(self, request: Request, pk: str) -> Response:
        cuenta = servicio_de_cuentas.liberar_cuenta(
            cuenta_id=int(pk), negocio_id=self.negocio_id, liberada_por_id=request.user.id
        )
        return Response(serializers.CuentaOutputSerializer(cuenta).data)

    @extend_schema(
        summary="Cobrar y cerrar la cuenta",
        description="Un solo pago que cubre el total: en el bar no hay abonos.",
        request=serializers.CobroInputSerializer,
        responses={201: serializers.ResultadoDeCobroOutputSerializer},
    )
    @action(
        detail=True, methods=["post"], url_path="cobro", permission_classes=[EsCajeroOAdministrador]
    )
    def cobro(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.CobroInputSerializer, request)
        resultado = servicio_de_pagos.registrar_pago_de_cuenta(
            cuenta_id=int(pk),
            negocio_id=self.negocio_id,
            recibido_por_id=request.user.id,
            **datos,
        )
        return Response(
            serializers.ResultadoDeCobroOutputSerializer(resultado).data,
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------------------------------- #
# Comandas
# --------------------------------------------------------------------------- #
class PedidoViewSet(_ViewSetDelEvento, mixins.RetrieveModelMixin):
    """/api/v1/eventos/pedidos/ — la comanda."""

    serializer_class = serializers.PedidoOutputSerializer
    filterset_class = filtros.PedidoFiltro
    permission_classes = [EsDelEquipo]
    queryset = PedidoEvento.objects.none()

    def get_queryset(self):
        return selector.pedidos_del_negocio(negocio_id=self.negocio_id).prefetch_related(
            "detalles__producto"
        )

    @extend_schema(summary="Listar las comandas")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una comanda")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Tomar una comanda",
        description=(
            "Descuenta el inventario **al crearla**, no al entregarla. Sin "
            "existencias suficientes se bloquea y no queda ni el pedido. "
            "`cliente_evento_id` vacío es la venta de mostrador."
        ),
        request=serializers.PedidoInputSerializer,
        responses={201: serializers.PedidoOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.PedidoInputSerializer, request)
        pedido = servicio_de_pedidos.registrar_pedido(
            evento_id=datos["evento_id"],
            cliente_evento_id=datos["cliente_evento_id"],
            lineas=[
                LineaDePedidoDTO(producto_id=linea["producto_id"], cantidad=linea["cantidad"])
                for linea in datos["lineas"]
            ],
            mesero_id=request.user.id,
            negocio_id=self.negocio_id,
        )
        return Response(
            serializers.PedidoOutputSerializer(pedido).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Entregar la comanda",
        description="Solo cambia el estado: el stock ya salió al tomarla.",
        request=None,
        responses={200: serializers.PedidoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="entrega")
    def entrega(self, request: Request, pk: str) -> Response:
        pedido = servicio_de_pedidos.entregar_pedido(pedido_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.PedidoOutputSerializer(pedido).data)

    @extend_schema(
        summary="Cancelar la comanda",
        description=(
            "Devuelve al inventario lo que descontó. Es del cajero, porque es "
            "una corrección de caja. Se puede cancelar una comanda ya entregada "
            "mientras no esté cobrada."
        ),
        request=serializers.MotivoDeCancelacionInputSerializer,
        responses={200: serializers.PedidoOutputSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="cancelacion",
        permission_classes=[EsCajeroOAdministrador],
    )
    def cancelacion(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.MotivoDeCancelacionInputSerializer, request)
        pedido = servicio_de_pedidos.cancelar_pedido(
            pedido_id=int(pk),
            negocio_id=self.negocio_id,
            usuario_id=request.user.id,
            motivo=datos["motivo"],
        )
        return Response(serializers.PedidoOutputSerializer(pedido).data)

    @extend_schema(
        summary="Cobrar una venta de mostrador",
        request=serializers.CobroInputSerializer,
        responses={201: serializers.ResultadoDeCobroOutputSerializer},
    )
    @action(
        detail=True, methods=["post"], url_path="cobro", permission_classes=[EsCajeroOAdministrador]
    )
    def cobro(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.CobroInputSerializer, request)
        resultado = servicio_de_pagos.registrar_pago_de_mostrador(
            pedido_id=int(pk),
            negocio_id=self.negocio_id,
            recibido_por_id=request.user.id,
            **datos,
        )
        return Response(
            serializers.ResultadoDeCobroOutputSerializer(resultado).data,
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------------------------------- #
# Pulseras, dispositivos y alertas
# --------------------------------------------------------------------------- #
class PulseraViewSet(_ViewSetDelEvento):
    """/api/v1/eventos/pulseras/ — el inventario de chips. Solo administrador."""

    serializer_class = serializers.PulseraOutputSerializer
    permission_classes = [EsAdministrador]
    queryset = PulseraNfc.objects.none()

    def get_permissions(self):
        if self.action == "list":
            return [EsDelEquipo()]
        return [EsAdministrador()]

    def get_queryset(self):
        return selector.pulseras_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las pulseras")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar una pulsera",
        description="Se da de alta por el UID que el chip trae de fábrica.",
        request=serializers.PulseraInputSerializer,
        responses={201: serializers.PulseraOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.PulseraInputSerializer, request)
        pulsera = servicio_de_pulseras.registrar_pulsera(negocio_id=self.negocio_id, **datos)
        return Response(
            serializers.PulseraOutputSerializer(pulsera).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Cambiar el estado de una pulsera",
        description="Solo la condición física del chip: dañada, perdida o retirada.",
        request=serializers.EstadoDePulseraInputSerializer,
        responses={200: serializers.PulseraOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="estado")
    def estado(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.EstadoDePulseraInputSerializer, request)
        pulsera = servicio_de_pulseras.cambiar_estado_de_pulsera(
            pulsera_id=int(pk), negocio_id=self.negocio_id, **datos
        )
        return Response(serializers.PulseraOutputSerializer(pulsera).data)


class DispositivoViewSet(_ViewSetDelEvento):
    """/api/v1/eventos/dispositivos/ — los lectores de la puerta."""

    serializer_class = serializers.DispositivoOutputSerializer
    permission_classes = [EsAdministrador]
    # Solo para que drf-spectacular sepa de qué modelo es el listado: el
    # queryset de verdad lo arma `get_queryset` con el negocio del usuario.
    queryset = DispositivoNfc.objects.none()

    def get_queryset(self):
        return repositorio_de_pulseras.dispositivos_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar los lectores de puerta")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Dar de alta un lector",
        description=(
            "Devuelve el token **una sola vez**: en la base solo queda su hash. "
            "Si se pierde, se da de alta otro y se revoca este."
        ),
        request=serializers.DispositivoInputSerializer,
        responses={201: serializers.DispositivoCreadoOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        datos = self._validado(serializers.DispositivoInputSerializer, request)
        dispositivo, token = servicio_de_pulseras.registrar_dispositivo(
            negocio_id=self.negocio_id, **datos
        )
        salida = serializers.DispositivoCreadoOutputSerializer(dispositivo).data | {"token": token}
        return Response(salida, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Revocar un lector",
        description="Es lo que se hace cuando alguien abre la caja y se lleva el token.",
        request=None,
        responses={200: serializers.DispositivoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="revocacion")
    def revocacion(self, request: Request, pk: str) -> Response:
        dispositivo = servicio_de_pulseras.revocar_dispositivo(
            dispositivo_id=int(pk), negocio_id=self.negocio_id
        )
        return Response(serializers.DispositivoOutputSerializer(dispositivo).data)


class AlertaViewSet(_ViewSetDelEvento):
    """/api/v1/eventos/alertas/ — cuándo una cuenta cruzó su límite."""

    serializer_class = serializers.AlertaOutputSerializer
    filterset_class = filtros.AlertaFiltro
    permission_classes = [EsDelEquipo]
    queryset = AlertaConsumo.objects.none()

    def get_queryset(self):
        return selector.alertas_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las alertas de consumo")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Atender una alerta",
        description="Guarda quién la atendió y qué hizo. Los tres datos van juntos.",
        request=serializers.AtencionDeAlertaInputSerializer,
        responses={200: serializers.AlertaOutputSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="atencion",
        permission_classes=[EsCajeroOAdministrador],
    )
    def atencion(self, request: Request, pk: str) -> Response:
        datos = self._validado(serializers.AtencionDeAlertaInputSerializer, request)
        alerta = servicio_de_alertas.atender_alerta(
            alerta_id=int(pk),
            negocio_id=self.negocio_id,
            atendida_por_id=request.user.id,
            **datos,
        )
        return Response(serializers.AlertaOutputSerializer(alerta).data)


# --------------------------------------------------------------------------- #
# Punto de control NFC
# --------------------------------------------------------------------------- #
class PuntoDeControlView(APIView):
    """POST /api/v1/eventos/puntos-de-control/consultar/

    Lo llama el aparato de la puerta, no una persona: se autentica con su
    propio token y el negocio sale de ahí, nunca de la petición.

    Devuelve **lo mínimo** —nombre y monto— y lleva freno de peticiones: sin
    él, cualquiera con un lector de tres dólares podría ir preguntándole al
    sistema cuánto debe cada persona del bar.
    """

    authentication_classes = [AutenticacionDeDispositivo]
    permission_classes = [EsDispositivoNfc]
    throttle_scope = "punto_de_control"

    @extend_schema(
        summary="Consultar una pulsera desde la puerta",
        description="`Authorization: Dispositivo <token>`.",
        request=serializers.ConsultaDePuntoDeControlInputSerializer,
        responses={200: serializers.PuntoDeControlOutputSerializer},
    )
    def post(self, request: Request) -> Response:
        entrada = serializers.ConsultaDePuntoDeControlInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        respuesta = consultar_punto_de_control(
            uid_tag=entrada.validated_data["uid_tag"].strip().upper(),
            negocio_id=request.auth.negocio_id,
        )
        return Response(serializers.PuntoDeControlOutputSerializer(respuesta).data)
