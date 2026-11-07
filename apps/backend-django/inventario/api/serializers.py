"""Traducción JSON ↔ Python del inventario."""

from rest_framework import serializers

from catalogo.models import Producto
from inventario.models import Existencia, MovimientoInventario, Ubicacion


# --------------------------------------------------------------------------- #
# Ubicaciones
# --------------------------------------------------------------------------- #
class UbicacionInputSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    tipo = serializers.ChoiceField(choices=Ubicacion.Tipo.choices)
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class UbicacionOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = ("id", "nombre", "tipo", "direccion", "activa", "creado_en", "actualizado_en")


# --------------------------------------------------------------------------- #
# Existencias
# --------------------------------------------------------------------------- #
class ProductoAnidadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ("id", "sku", "nombre")


class ExistenciaOutputSerializer(serializers.ModelSerializer):
    """`esta_bajo_minimo` sale calculado: con la mínima en 0 nunca lo está."""

    producto = ProductoAnidadoSerializer(read_only=True)
    ubicacion = UbicacionOutputSerializer(read_only=True)
    esta_bajo_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Existencia
        fields = (
            "id",
            "producto",
            "ubicacion",
            "cantidad_disponible",
            "cantidad_minima",
            "esta_bajo_minimo",
            "actualizado_en",
        )


class CantidadMinimaInputSerializer(serializers.Serializer):
    """Un cero es «sin alerta», no «alerta siempre»."""

    producto_id = serializers.IntegerField()
    ubicacion_id = serializers.IntegerField()
    cantidad_minima = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)


class ValorizacionOutputSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=24, decimal_places=2)


# --------------------------------------------------------------------------- #
# Movimientos
# --------------------------------------------------------------------------- #
class MovimientoOutputSerializer(serializers.ModelSerializer):
    """La cantidad sale **con signo**: positiva suma, negativa resta."""

    producto = ProductoAnidadoSerializer(read_only=True)
    ubicacion = serializers.CharField(source="ubicacion.nombre", read_only=True)
    usuario = serializers.CharField(source="usuario.nombre_completo", read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = (
            "id",
            "producto",
            "ubicacion",
            "tipo",
            "cantidad",
            "referencia_tipo",
            "referencia_id",
            "usuario",
            "nota",
            "fecha",
        )


class LineaInputSerializer(serializers.Serializer):
    """La cantidad va **en positivo**: el signo lo pone el servicio."""

    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def validate_cantidad(self, valor):
        if valor == 0:
            raise serializers.ValidationError("Un movimiento de cero no es un movimiento.")
        return valor


class OperacionInputSerializer(serializers.Serializer):
    """Entrada o salida de mercancía en una ubicación."""

    ubicacion_id = serializers.IntegerField()
    lineas = LineaInputSerializer(many=True, allow_empty=False)
    nota = serializers.CharField(required=False, allow_blank=True, default="")


class MermaInputSerializer(serializers.Serializer):
    """La merma exige motivo: se mide y se compara contra la venta."""

    ubicacion_id = serializers.IntegerField()
    lineas = LineaInputSerializer(many=True, allow_empty=False)
    motivo = serializers.CharField(max_length=500)


class TrasladoInputSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    origen_id = serializers.IntegerField()
    destino_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    nota = serializers.CharField(required=False, allow_blank=True, default="")


class AjusteInputSerializer(serializers.Serializer):
    """Se manda **lo contado**, no la diferencia: quien cuenta cuenta cajas."""

    producto_id = serializers.IntegerField()
    ubicacion_id = serializers.IntegerField()
    cantidad_contada = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    motivo = serializers.CharField(max_length=500)


class ReconstruccionInputSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    ubicacion_id = serializers.IntegerField()


class MotivoInputSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=500)
