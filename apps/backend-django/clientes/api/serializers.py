"""Traducción JSON ↔ Python de las fichas de cliente."""

from rest_framework import serializers

from clientes.models import Cliente


class ClienteInputSerializer(serializers.Serializer):
    tipo_documento = serializers.ChoiceField(choices=Cliente.TipoDocumento.choices)
    numero_documento = serializers.CharField(max_length=30)
    nombre = serializers.CharField(max_length=120)
    apellido = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True, default=None)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    correo = serializers.EmailField(max_length=150, required=False, allow_blank=True, default="")
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notas = serializers.CharField(required=False, allow_blank=True, default="")


class ClienteOutputSerializer(serializers.ModelSerializer):
    """`es_menor_de_edad` sale calculado para que la pantalla lo pinte en rojo.

    Es un aviso, no un bloqueo: la cuenta se abre igual (decisión 7).
    """

    nombre_completo = serializers.CharField(read_only=True)
    edad = serializers.IntegerField(read_only=True)
    es_menor_de_edad = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cliente
        fields = (
            "id",
            "tipo_documento",
            "numero_documento",
            "nombre",
            "apellido",
            "nombre_completo",
            "fecha_nacimiento",
            "edad",
            "es_menor_de_edad",
            "telefono",
            "correo",
            "ciudad",
            "notas",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class BusquedaPorDocumentoSerializer(serializers.Serializer):
    tipo_documento = serializers.ChoiceField(choices=Cliente.TipoDocumento.choices)
    numero_documento = serializers.CharField(max_length=30)
