"""Traducción JSON ↔ Python del catálogo.

Entrada y salida van separadas: lo que se acepta no tiene por qué coincidir
con lo que se devuelve. El serializer valida **formato** (que el campo venga,
que sea un número, que quepa); las reglas del negocio —que el SKU no esté
repetido, que la categoría sea de este negocio— viven en `servicios/`.
"""

from rest_framework import serializers

from catalogo.models import Categoria, Producto, ProductoProveedor, Proveedor


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
    costo = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    precio_evento = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    precio_mayorista = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)


class CategoriaAnidadaSerializer(serializers.ModelSerializer):
    """La categoría dentro de un producto: lo justo para pintarla, sin otra petición."""

    class Meta:
        model = Categoria
        fields = ("id", "nombre")


class ProductoOutputSerializer(serializers.ModelSerializer):
    categoria = CategoriaAnidadaSerializer(read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id",
            "sku",
            "nombre",
            "categoria",
            "costo",
            "precio_evento",
            "precio_mayorista",
            "activo",
            "creado_en",
            "actualizado_en",
        )


class CambioDePrecioInputSerializer(serializers.Serializer):
    """Al menos uno de los dos precios. Mandar el cuerpo vacío no es un cambio."""

    precio_evento = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )
    precio_mayorista = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )

    def validate(self, datos: dict) -> dict:
        if not datos:
            raise serializers.ValidationError("Indica al menos un precio para cambiar.")
        return datos


class MargenDeVentaOutputSerializer(serializers.Serializer):
    """Los márgenes van como porcentaje, y en `null` cuando el costo es cero."""

    costo = serializers.DecimalField(max_digits=12, decimal_places=2)
    precio_evento = serializers.DecimalField(max_digits=12, decimal_places=2)
    precio_mayorista = serializers.DecimalField(max_digits=12, decimal_places=2)
    margen_evento = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    margen_mayorista = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


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
