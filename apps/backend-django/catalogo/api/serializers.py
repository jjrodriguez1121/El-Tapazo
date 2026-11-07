"""Traducción JSON ↔ Python del catálogo.

Entrada y salida van separadas: lo que se acepta no tiene por qué coincidir
con lo que se devuelve. El serializer valida **formato** (que el campo venga,
que sea un número, que quepa); las reglas del negocio —que el SKU no esté
repetido, que la categoría sea de este negocio— viven en `servicios/`.
"""

from rest_framework import serializers

from catalogo.models import Categoria, Impuesto, Producto, ProductoProveedor, Proveedor


# --------------------------------------------------------------------------- #
# Categorías
# --------------------------------------------------------------------------- #
class CategoriaInputSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    descripcion = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class CategoriaOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nombre", "descripcion", "activa", "creado_en", "actualizado_en")


# --------------------------------------------------------------------------- #
# Proveedores
# --------------------------------------------------------------------------- #
class ProveedorInputSerializer(serializers.Serializer):
    razon_social = serializers.CharField(max_length=150)
    nit = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    nombre_contacto = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default=""
    )
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    correo = serializers.EmailField(max_length=150, required=False, allow_blank=True, default="")
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class ProveedorOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = (
            "id",
            "razon_social",
            "nit",
            "nombre_contacto",
            "telefono",
            "correo",
            "ciudad",
            "direccion",
            "activo",
            "creado_en",
            "actualizado_en",
        )


# --------------------------------------------------------------------------- #
# Productos
# --------------------------------------------------------------------------- #
class ProductoInputSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=50)
    nombre = serializers.CharField(max_length=200)
    categoria_id = serializers.IntegerField()
    costo = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, default=0
    )
    precio_venta = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    imagen = serializers.CharField(required=False, allow_blank=True, default="")
    cantidad_disponible = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, default=0
    )
    cantidad_minima = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, default=0
    )
    margen_ganancia = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=0, required=False, default=30
    )
    precio_venta_automatico = serializers.BooleanField(required=False, default=True)


class CategoriaAnidadaSerializer(serializers.ModelSerializer):
    """La categoría dentro de un producto: lo justo para pintarla, sin otra petición."""

    class Meta:
        model = Categoria
        fields = ("id", "nombre")


class ImpuestoAnidadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impuesto
        fields = ("id", "nombre", "porcentaje", "tipo_tratamiento", "activo")


class ProductoOutputSerializer(serializers.ModelSerializer):
    categoria = CategoriaAnidadaSerializer(read_only=True)
    impuesto = ImpuestoAnidadoSerializer(read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id",
            "sku",
            "nombre",
            "categoria",
            "impuesto",
            "costo",
            "precio_venta",
            "margen_ganancia",
            "precio_venta_automatico",
            "imagen",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class CambioDePrecioInputSerializer(serializers.Serializer):
    """El nuevo precio de venta."""

    precio_venta = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def validate(self, datos: dict) -> dict:
        return datos


class MargenDeVentaOutputSerializer(serializers.Serializer):
    """Los márgenes van como porcentaje, y en `null` cuando el costo es cero."""

    costo = serializers.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = serializers.DecimalField(max_digits=12, decimal_places=2)
    margen = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


# --------------------------------------------------------------------------- #
# Precios de proveedor
# --------------------------------------------------------------------------- #
class OfertaInputSerializer(serializers.Serializer):
    proveedor_id = serializers.IntegerField()
    precio_compra = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    codigo_proveedor = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    es_principal = serializers.BooleanField(required=False, default=False)


class ProveedorAnidadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ("id", "razon_social")


class OfertaOutputSerializer(serializers.ModelSerializer):
    proveedor = ProveedorAnidadoSerializer(read_only=True)

    class Meta:
        model = ProductoProveedor
        fields = ("id", "proveedor", "precio_compra", "codigo_proveedor", "es_principal")
