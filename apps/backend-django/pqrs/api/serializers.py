"""Serializadores de radicación y seguimiento de PQR."""

from rest_framework import serializers

from clientes.models import Cliente
from pqrs.models import Pqr, PqrSeguimiento


class PqrSeguimientoOutputSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = PqrSeguimiento
        fields = (
            "id",
            "tipo",
            "contenido",
            "estado_anterior",
            "estado_nuevo",
            "usuario_nombre",
            "visible_solicitante",
            "creado_en",
        )

    def get_usuario_nombre(self, seguimiento):
        usuario = seguimiento.usuario
        return f"{usuario.nombre} {usuario.apellido}".strip() if usuario else "Usuario eliminado"


class PqrOutputSerializer(serializers.ModelSerializer):
    cliente_id = serializers.IntegerField(read_only=True)
    responsable_id = serializers.IntegerField(read_only=True)
    responsable_nombre = serializers.SerializerMethodField()
    seguimientos = PqrSeguimientoOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Pqr
        fields = (
            "id",
            "radicado",
            "cliente_id",
            "nombre_solicitante",
            "documento_solicitante",
            "telefono_solicitante",
            "correo_solicitante",
            "tipo",
            "ambito",
            "canal",
            "asunto",
            "descripcion",
            "estado",
            "fecha_radicacion",
            "fecha_cierre",
            "usuario_registro",
            "responsable_id",
            "responsable_nombre",
            "seguimientos",
        )
        read_only_fields = fields

    def get_responsable_nombre(self, pqr):
        usuario = pqr.responsable
        return f"{usuario.nombre} {usuario.apellido}".strip() if usuario else ""


class PqrInputSerializer(serializers.ModelSerializer):
    nombre_solicitante = serializers.CharField(min_length=3, max_length=180)
    asunto = serializers.CharField(min_length=4, max_length=180)
    descripcion = serializers.CharField(min_length=10)

    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.none(), required=False, allow_null=True
    )

    class Meta:
        model = Pqr
        fields = (
            "cliente",
            "nombre_solicitante",
            "documento_solicitante",
            "telefono_solicitante",
            "correo_solicitante",
            "tipo",
            "ambito",
            "canal",
            "asunto",
            "descripcion",
        )

    def get_fields(self):
        fields = super().get_fields()
        negocio_id = self.context["request"].user.negocio_id
        fields["cliente"].queryset = Cliente.objects.filter(negocio_id=negocio_id)
        return fields

    def validate(self, attrs):
        if not attrs.get("cliente") and attrs.get("documento_solicitante"):
            coincidencias = Cliente.objects.filter(
                negocio_id=self.context["request"].user.negocio_id,
                numero_documento=attrs["documento_solicitante"].strip(),
            )
            if coincidencias.count() == 1:
                attrs["cliente"] = coincidencias.first()
        return attrs


class PqrSeguimientoInputSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(
        choices=(
            PqrSeguimiento.Tipo.NOTA,
            PqrSeguimiento.Tipo.RESPUESTA,
            PqrSeguimiento.Tipo.CAMBIO_ESTADO,
            PqrSeguimiento.Tipo.ASIGNACION,
        )
    )
    contenido = serializers.CharField(required=False, allow_blank=True, default="")
    nuevo_estado = serializers.ChoiceField(
        choices=Pqr.Estado.choices, required=False, allow_blank=True, default=""
    )

    def validate(self, attrs):
        tipo = attrs["tipo"]
        contenido = attrs["contenido"].strip()
        attrs["contenido"] = contenido
        if tipo in (PqrSeguimiento.Tipo.NOTA, PqrSeguimiento.Tipo.RESPUESTA) and not contenido:
            raise serializers.ValidationError(
                {"contenido": "Escribe el contenido del seguimiento o de la respuesta."}
            )
        if tipo == PqrSeguimiento.Tipo.CAMBIO_ESTADO and not attrs["nuevo_estado"]:
            raise serializers.ValidationError(
                {"nuevo_estado": "Selecciona el estado al que cambiará la PQR."}
            )
        return attrs


class PqrResumenSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    servicio = serializers.IntegerField()
    productos = serializers.IntegerField()
    pendientes = serializers.IntegerField()
