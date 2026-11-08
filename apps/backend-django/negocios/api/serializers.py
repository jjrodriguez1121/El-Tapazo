"""Traducción JSON ↔ Python de la administración de negocios."""

from rest_framework import serializers

from negocios.models import Negocio


class NegocioInputSerializer(serializers.Serializer):
    """El estado no se manda: se cambia con «suspensión» y «reactivación»."""

    nombre_comercial = serializers.CharField(max_length=150)
    nit = serializers.CharField(max_length=20)


class NegocioOutputSerializer(serializers.ModelSerializer):
    esta_operativo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Negocio
        fields = (
            "id",
            "nombre_comercial",
            "nit",
            "estado",
            "esta_operativo",
            "creado_en",
            "actualizado_en",
        )


class RangoDeFechasSerializer(serializers.Serializer):
    """Los dos parámetros del informe. Sin ellos, el mes en curso."""

    desde = serializers.DateField(required=False, allow_null=True, default=None)
    hasta = serializers.DateField(required=False, allow_null=True, default=None)


class RangoDeFechasObligatorioSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()

    def validate(self, datos):
        if datos["desde"] > datos["hasta"]:
            raise serializers.ValidationError("La fecha inicial no puede ser posterior a la fecha final.")
        return datos


class VentasDelCanalSerializer(serializers.Serializer):
    canal = serializers.CharField()
    vendido = serializers.DecimalField(max_digits=24, decimal_places=2)
    cobrado = serializers.DecimalField(max_digits=24, decimal_places=2)


class ResumenDeVentasOutputSerializer(serializers.Serializer):
    """`vendido` y `cobrado` no tienen por qué coincidir: el mayoreo va a crédito."""

    desde = serializers.DateField()
    hasta = serializers.DateField()
    canales = VentasDelCanalSerializer(many=True)
    vendido_total = serializers.DecimalField(max_digits=24, decimal_places=2)
    cobrado_total = serializers.DecimalField(max_digits=24, decimal_places=2)


class ResumenDashboardOutputSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    ventas_facturadas = serializers.DecimalField(max_digits=24, decimal_places=2)
    ventas_netas = serializers.DecimalField(max_digits=24, decimal_places=2)
    descuentos = serializers.DecimalField(max_digits=24, decimal_places=2)
    impuestos = serializers.DecimalField(max_digits=24, decimal_places=2)
    costo_de_ventas = serializers.DecimalField(max_digits=24, decimal_places=2)
    utilidad_bruta = serializers.DecimalField(max_digits=24, decimal_places=2)
    cobrado_en_periodo = serializers.DecimalField(max_digits=24, decimal_places=2)
    por_cobrar = serializers.DecimalField(max_digits=24, decimal_places=2)
    por_pagar = serializers.DecimalField(max_digits=24, decimal_places=2)
    ventas_registradas = serializers.IntegerField()
    ventas_contado = serializers.IntegerField()
    ventas_credito = serializers.IntegerField()
    productos_mas_vendidos = serializers.ListField(child=serializers.DictField())
    entregas_pendientes = serializers.IntegerField()
    stock_bajo = serializers.IntegerField()
