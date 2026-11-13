"""Traducción JSON ↔ Python del canal evento/bar."""

from rest_framework import serializers

from clientes.models import Cliente
from eventos.models import (
    ClienteEvento,
    DetallePedidoEvento,
    Evento,
    GrupoEvento,
    PagoEvento,
    PedidoEvento,
)


# --------------------------------------------------------------------------- #
# Jornada
# --------------------------------------------------------------------------- #
class AperturaDeJornadaInputSerializer(serializers.Serializer):
    """Abrir caja: se dice dónde, y el resto lo pone el sistema."""

    ubicacion_id = serializers.IntegerField()


class EventoOutputSerializer(serializers.ModelSerializer):
    ubicacion = serializers.CharField(source="ubicacion.nombre", read_only=True, default="")

    class Meta:
        model = Evento
        fields = (
            "id",
            "nombre",
            "ubicacion",
            "tipo_espacio",
            "fecha_inicio",
            "fecha_fin",
            "estado",
        )


class InformeDeCierreOutputSerializer(serializers.Serializer):
    ventas_por_producto = serializers.ListField(child=serializers.DictField())
    pagos_por_metodo = serializers.ListField(child=serializers.DictField())
    total_cobrado = serializers.DecimalField(max_digits=24, decimal_places=2)
    cuentas_atendidas = serializers.IntegerField()


# --------------------------------------------------------------------------- #
# Grupos y cuentas
# --------------------------------------------------------------------------- #
class GrupoInputSerializer(serializers.Serializer):
    evento_id = serializers.IntegerField()
    nombre_referencia = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    mesa_zona = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")


class GrupoOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoEvento
        fields = (
            "id",
            "evento",
            "nombre_referencia",
            "mesa_zona",
            "estado",
            "cerrado_en",
            "creado_en",
        )


class CuentaInputSerializer(serializers.Serializer):
    grupo_id = serializers.IntegerField()
    cliente_id = serializers.IntegerField()


class ClienteDeLaCuentaSerializer(serializers.ModelSerializer):
    """`es_menor_de_edad` avisa; no bloquea nada (decisión 7)."""

    nombre_completo = serializers.CharField(read_only=True)
    es_menor_de_edad = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cliente
        fields = ("id", "nombre_completo", "es_menor_de_edad")


class CuentaOutputSerializer(serializers.ModelSerializer):
    cliente = ClienteDeLaCuentaSerializer(read_only=True)
    esta_abierta = serializers.SerializerMethodField()

    class Meta:
        model = ClienteEvento
        fields = (
            "id",
            "cliente",
            "grupo_evento",
            "esta_abierta",
            "liberada_en",
            "creado_en",
        )

    def get_esta_abierta(self, cuenta: ClienteEvento) -> bool:
        return cuenta.liberada_en is None


# --------------------------------------------------------------------------- #
# Comandas
# --------------------------------------------------------------------------- #
class LineaDePedidoInputSerializer(serializers.Serializer):
    """El precio **no** se manda: lo congela el servicio del catálogo."""

    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def validate_cantidad(self, valor):
        if valor == 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return valor


class PedidoInputSerializer(serializers.Serializer):
    """`cliente_evento_id` vacío es la venta de mostrador."""

    evento_id = serializers.IntegerField()
    cliente_evento_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    lineas = LineaDePedidoInputSerializer(many=True, allow_empty=False)


class DetalleDelPedidoSerializer(serializers.ModelSerializer):
    producto = serializers.CharField(source="producto.nombre", read_only=True)
    sku = serializers.CharField(source="producto.sku", read_only=True)

    class Meta:
        model = DetallePedidoEvento
        fields = ("id", "producto", "sku", "cantidad", "precio_unitario", "importe")


class PedidoOutputSerializer(serializers.ModelSerializer):
    detalles = DetalleDelPedidoSerializer(many=True, read_only=True)
    mesero = serializers.CharField(source="mesero.nombre_completo", read_only=True)

    class Meta:
        model = PedidoEvento
        fields = (
            "id",
            "evento",
            "cliente_evento",
            "mesero",
            "estado",
            "detalles",
            "creado_en",
        )


class MotivoDeCancelacionInputSerializer(serializers.Serializer):
    """Nombre propio y no `MotivoInput` a secas: `inventario` tiene el suyo, y
    dos componentes con el mismo nombre rompen el esquema de la API."""

    motivo = serializers.CharField(max_length=500)


# --------------------------------------------------------------------------- #
# Cobro
# --------------------------------------------------------------------------- #
class CobroInputSerializer(serializers.Serializer):
    """Un solo pago que cubre el total. En el bar no hay abonos (decisión 3)."""

    monto = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    metodo = serializers.ChoiceField(choices=PagoEvento.Metodo.choices)
    referencia_transaccion = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )

    def validate_monto(self, valor):
        if valor == 0:
            raise serializers.ValidationError("El monto debe ser mayor que cero.")
        return valor


class ResultadoDeCobroOutputSerializer(serializers.Serializer):
    pago_id = serializers.IntegerField()
    consumido = serializers.DecimalField(max_digits=24, decimal_places=2)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    cuentas_liberadas = serializers.IntegerField()


class ConsumoOutputSerializer(serializers.Serializer):
    consumido = serializers.DecimalField(max_digits=24, decimal_places=2)
