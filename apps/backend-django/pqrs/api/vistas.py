"""API de radicación y gestión de PQR."""

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from nucleo.api.vistas import MixinDelNegocio
from pqrs.api import serializers
from pqrs.models import Pqr, PqrSeguimiento


class PqrViewSet(
    MixinDelNegocio,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Pqr.objects.none()
    serializer_class = serializers.PqrOutputSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "radicado",
        "asunto",
        "descripcion",
        "nombre_solicitante",
        "documento_solicitante",
    ]
    filterset_fields = ["estado", "ambito", "tipo"]
    lookup_value_regex = "[0-9]+"

    def get_queryset(self):
        queryset = (
            Pqr.objects.filter(negocio_id=self.negocio_id)
            .select_related("responsable", "usuario_registro")
            .prefetch_related("seguimientos__usuario")
        )
        for campo in self.filterset_fields:
            valor = self.request.query_params.get(campo)
            if valor:
                queryset = queryset.filter(**{campo: valor})
        respuesta = self.request.query_params.get("respuesta")
        if respuesta == "si":
            queryset = queryset.filter(
                seguimientos__tipo=PqrSeguimiento.Tipo.RESPUESTA
            ).distinct()
        elif respuesta == "no":
            queryset = queryset.exclude(
                seguimientos__tipo=PqrSeguimiento.Tipo.RESPUESTA
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.PqrInputSerializer
        if self.action == "seguimientos":
            return serializers.PqrSeguimientoInputSerializer
        return serializers.PqrOutputSerializer

    @extend_schema(
        summary="Radicar una PQR",
        request=serializers.PqrInputSerializer,
        responses={201: serializers.PqrOutputSerializer},
    )
    @transaction.atomic
    def create(self, request: Request, *args, **kwargs) -> Response:
        entrada = self.get_serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        pqr = entrada.save(
            negocio_id=self.negocio_id,
            usuario_registro=request.user,
        )
        PqrSeguimiento.objects.create(
            negocio_id=self.negocio_id,
            pqr=pqr,
            tipo=PqrSeguimiento.Tipo.RADICACION,
            contenido="Solicitud radicada.",
            usuario=request.user,
        )
        pqr_actualizada = self.get_queryset().get(pk=pqr.pk)
        return Response(
            serializers.PqrOutputSerializer(pqr_actualizada).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Consultar el resumen de PQR",
        responses={200: serializers.PqrResumenSerializer},
    )
    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request: Request) -> Response:
        base = Pqr.objects.filter(negocio_id=self.negocio_id)
        conteo = base.aggregate(
            total=Count("id"),
            servicio=Count("id", filter=Q(ambito=Pqr.Ambito.SERVICIO)),
            productos=Count("id", filter=Q(ambito=Pqr.Ambito.PRODUCTOS)),
            pendientes=Count(
                "id",
                filter=Q(
                    estado__in=(
                        Pqr.Estado.RADICADA,
                        Pqr.Estado.EN_REVISION,
                        Pqr.Estado.EN_GESTION,
                    )
                ),
            ),
        )
        return Response(conteo)

    @extend_schema(
        summary="Registrar un seguimiento, respuesta o cambio de estado",
        request=serializers.PqrSeguimientoInputSerializer,
        responses={201: serializers.PqrOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="seguimientos")
    @transaction.atomic
    def seguimientos(self, request: Request, pk: str) -> Response:
        pqr = self.get_object()
        entrada = self.get_serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        tipo = datos["tipo"]
        estado_anterior = pqr.estado
        nuevo_estado = datos["nuevo_estado"]

        if tipo == PqrSeguimiento.Tipo.RESPUESTA and not nuevo_estado:
            nuevo_estado = Pqr.Estado.RESPONDIDA
        if tipo == PqrSeguimiento.Tipo.ASIGNACION:
            pqr.responsable = request.user
            pqr.save(update_fields=["responsable", "actualizado_en"])
        elif nuevo_estado and nuevo_estado != estado_anterior:
            pqr.estado = nuevo_estado
            pqr.fecha_cierre = (
                pqr.fecha_cierre or timezone.now()
                if nuevo_estado == Pqr.Estado.CERRADA
                else None
            )
            pqr.save(update_fields=["estado", "fecha_cierre", "actualizado_en"])

        registro = PqrSeguimiento.objects.create(
            negocio_id=self.negocio_id,
            pqr=pqr,
            tipo=tipo,
            contenido=datos["contenido"],
            estado_anterior=estado_anterior if pqr.estado != estado_anterior else "",
            estado_nuevo=pqr.estado if pqr.estado != estado_anterior else "",
            usuario=request.user,
            visible_solicitante=tipo == PqrSeguimiento.Tipo.RESPUESTA,
        )
        if tipo == PqrSeguimiento.Tipo.ASIGNACION and not registro.contenido:
            registro.contenido = f"Asignada a {request.user.nombre} {request.user.apellido}".strip()
            registro.save(update_fields=["contenido"])

        pqr_actualizada = self.get_queryset().get(pk=pqr.pk)
        return Response(
            serializers.PqrOutputSerializer(pqr_actualizada).data,
            status=status.HTTP_201_CREATED,
        )
