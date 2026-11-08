from django.utils import timezone
from rest_framework import serializers

from compras.models import Compra


class ProductoNuevoSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=50)
    nombre = serializers.CharField(max_length=200)
    categoria_id = serializers.IntegerField()
    impuesto_id = serializers.IntegerField(required=True)
    imagen = serializers.CharField(required=False, allow_blank=True, default="")


class DetalleCompraSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(required=False)
    producto_nuevo = ProductoNuevoSerializer(required=False)
    cantidad = serializers.IntegerField(min_value=1)
    costo_unitario = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    descuento = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False, default=0
    )
    porcentaje_iva = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, required=False, default=0
    )

    def validate(self, data):
        if not data.get("producto_id") and not data.get("producto_nuevo"):
            raise serializers.ValidationError(
                "Cada línea debe contener un producto existente o los datos de uno nuevo."
            )
        if data.get("producto_id") and data.get("producto_nuevo"):
            raise serializers.ValidationError(
                "Seleccione un producto existente o cree uno nuevo, no ambos."
            )
        valor_bruto = data["costo_unitario"] * data["cantidad"]
        if data["descuento"] > valor_bruto:
            raise serializers.ValidationError({
                "descuento": "El descuento no puede superar el valor de la línea."
            })
        return data


class CompraCrearSerializer(serializers.Serializer):
    proveedor_id = serializers.IntegerField()
    numero_factura = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    condicion_pago = serializers.ChoiceField(choices=["CONTADO", "CREDITO"])
    metodo_pago_id = serializers.IntegerField(required=False, allow_null=True)
    fecha_vencimiento = serializers.DateField(required=False, allow_null=True)
    detalles = DetalleCompraSerializer(many=True)
    estado = serializers.ChoiceField(
        choices=["BORRADOR", "RECIBIDA"], required=False, default="RECIBIDA"
    )

    def validate(self, datos):
        if datos.get("condicion_pago") == "CREDITO" and datos.get("detalles") and not any(
            linea["costo_unitario"] * linea["cantidad"] > linea["descuento"]
            for linea in datos["detalles"]
        ):
            raise serializers.ValidationError({
                "detalles": "El total de la compra debe ser mayor que cero."
            })
        if datos["condicion_pago"] == "CREDITO" and not datos.get("fecha_vencimiento"):
            raise serializers.ValidationError({
                "fecha_vencimiento": "Las compras a crédito requieren fecha de vencimiento.",
            })
        if (
            datos["condicion_pago"] == "CREDITO"
            and datos["fecha_vencimiento"] <= timezone.localdate()
        ):
            raise serializers.ValidationError({
                "fecha_vencimiento": "La fecha de vencimiento debe ser posterior a hoy.",
            })
        if datos["condicion_pago"] == "CONTADO":
            datos["fecha_vencimiento"] = None
            if not datos.get("metodo_pago_id"):
                raise serializers.ValidationError({
                    "metodo_pago_id": "Las compras de contado requieren medio de pago.",
                })
        return datos

    def validate_detalles(self, detalles):
        if not detalles:
            raise serializers.ValidationError("La compra debe tener al menos un producto.")
        return detalles


class CompraOutputSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.razon_social", read_only=True)
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Compra
        fields = (
            "id",
            "numero_compra",
            "numero_factura",
            "proveedor",
            "proveedor_nombre",
            "fecha_compra",
            "condicion_pago",
            "fecha_vencimiento",
            "subtotal",
            "descuento",
            "total_iva",
            "total",
            "estado",
            "detalles",
        )

    def get_detalles(self, compra):
        return [
            {
                "id": detalle.id,
                "producto_id": detalle.producto_id,
                "producto": detalle.producto.nombre,
                "sku": detalle.producto.sku,
                "cantidad": detalle.cantidad,
                "costo_unitario": detalle.costo_unitario,
                "porcentaje_iva": detalle.porcentaje_iva,
                "subtotal": detalle.subtotal,
            }
            for detalle in compra.detalles.select_related("producto").all()
        ]
