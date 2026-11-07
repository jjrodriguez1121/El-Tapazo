"""Traducción JSON ↔ Python del canal mayorista.

Los nombres llevan `Mayorista` o `Distribucion` a propósito: el esquema de la
API es plano y un `PedidoInput` de aquí chocaría con el de la barra.
"""

from rest_framework import serializers

from distribucion.models import (
    ClienteDistribucion,
    DetallePedidoDistribucion,
    PagoDistribucion,
    PedidoDistribucion,
)


# --------------------------------------------------------------------------- #
# Tiendas cliente
# --------------------------------------------------------------------------- #
class ClienteDistribucionInputSerializer(serializers.Serializer):
    """El NIT identifica a la tienda; `dias_credito` en 0 es «paga de contado»."""

    razon_social = serializers.CharField(max_length=150)
    nit = serializers.CharField(max_length=20)
    nombre_contacto = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default=""
    )
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    correo = serializers.EmailField(max_length=150, required=False, allow_blank=True, default="")
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    dias_credito = serializers.IntegerField(min_value=0, required=False, default=0)


class ClienteDistribucionOutputSerializer(serializers.ModelSerializer):
    paga_de_contado = serializers.BooleanField(read_only=True)

    class Meta:
        model = ClienteDistribucion
        fields = (
            "id",
            "razon_social",
            "nit",
            "nombre_contacto",
            "telefono",
            "correo",
            "ciudad",
            "direccion",
            "dias_credito",
            "paga_de_contado",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class ClienteEnMoraOutputSerializer(ClienteDistribucionOutputSerializer):
    """Lo mismo, más lo que debe **vencido** — que no es lo que debe en total."""

    deuda_vencida = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)

    class Meta(ClienteDistribucionOutputSerializer.Meta):
        fields = (*ClienteDistribucionOutputSerializer.Meta.fields, "deuda_vencida")


class SaldoDelClienteOutputSerializer(serializers.Serializer):
    saldo = serializers.DecimalField(max_digits=24, decimal_places=2)


# --------------------------------------------------------------------------- #
# Pedidos
# --------------------------------------------------------------------------- #
class LineaMayoristaInputSerializer(serializers.Serializer):
    """El precio **no** se manda: lo congela el servicio del catálogo."""

    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def validate_cantidad(self, valor):
        if valor == 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return valor


class PedidoMayoristaInputSerializer(serializers.Serializer):
    cliente_distribucion_id = serializers.IntegerField()
    lineas = LineaMayoristaInputSerializer(many=True, allow_empty=False)


class DetalleMayoristaSerializer(serializers.ModelSerializer):
    producto = serializers.CharField(source="producto.nombre", read_only=True)
    sku = serializers.CharField(source="producto.sku", read_only=True)

    class Meta:
        model = DetallePedidoDistribucion
        fields = ("id", "producto", "sku", "cantidad", "precio_unitario", "importe")


class PedidoDistribucionOutputSerializer(serializers.ModelSerializer):
    detalles = DetalleMayoristaSerializer(many=True, read_only=True)
    cliente = serializers.CharField(source="cliente_distribucion.razon_social", read_only=True)
    tomado_por = serializers.CharField(source="usuario.nombre_completo", read_only=True)

    class Meta:
        model = PedidoDistribucion
        fields = (
            "id",
            "cliente",
            "cliente_distribucion",
            "tomado_por",
            "estado",
            "fecha_pedido",
            "fecha_entrega",
            "motivo_no_entrega",
            "detalles",
            "creado_en",
        )


class DespachoInputSerializer(serializers.Serializer):
    """De qué bodega se carga el camión.

    Se dice al despachar y no al tomar el pedido porque es entonces cuando se
    sabe: el pedido se toma por teléfono y se carga donde haya mercancía.
    """

    ubicacion_id = serializers.IntegerField()


class MotivoDeNoEntregaInputSerializer(serializers.Serializer):
    """Obligatorio: sin él no se puede llamar a la tienda ni corregir la ruta."""

    motivo = serializers.CharField(max_length=500)


# --------------------------------------------------------------------------- #
# Abonos
# --------------------------------------------------------------------------- #
class AbonoInputSerializer(serializers.Serializer):
    """Un abono, no el pago entero: aquí una tienda paga en varias veces."""

    monto = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    metodo = serializers.ChoiceField(choices=PagoDistribucion.Metodo.choices)
    referencia_transaccion = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )

    def validate_monto(self, valor):
        if valor == 0:
            raise serializers.ValidationError("El monto debe ser mayor que cero.")
        return valor


class PagoDistribucionOutputSerializer(serializers.ModelSerializer):
    recibido_por = serializers.CharField(source="recibido_por.nombre_completo", read_only=True)

    class Meta:
        model = PagoDistribucion
        fields = (
            "id",
            "pedido_distribucion",
            "monto",
            "metodo",
            "referencia_transaccion",
            "recibido_por",
            "fecha",
        )


class SaldoDelPedidoOutputSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=24, decimal_places=2)
    pagado = serializers.DecimalField(max_digits=24, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=24, decimal_places=2)


class ResultadoDeAbonoOutputSerializer(serializers.Serializer):
    pago_id = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=24, decimal_places=2)
    pagado = serializers.DecimalField(max_digits=24, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=24, decimal_places=2)
