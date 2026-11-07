"""Catálogo: qué vende el negocio, de qué tipo y a quién se lo compra.

Cuatro tablas: `categorias` clasifica, `proveedores` son las empresas a las
que se compra, `productos` es lo que se vende y `productos_proveedores` une
esas dos últimas, porque un mismo producto se le puede comprar a varios
proveedores a precios distintos.
"""

from django.db import models

from nucleo.models import ModeloDelNegocio


class Categoria(ModeloDelNegocio):
    """Clasificación de productos: cervezas, licores, gaseosas, snacks…

    Es una tabla y no un texto suelto en `productos` para que al renombrar
    "Cervezas" no queden mil productos con el nombre viejo, y para que los
    informes por categoría no dependan de cómo lo escribió cada quien.
    """

    nombre = models.CharField("nombre", max_length=100)
    descripcion = models.CharField("descripción", max_length=255, blank=True)
    activa = models.BooleanField(
        "activa",
        default=True,
        help_text="Desactivar en vez de borrar: los productos históricos la siguen usando.",
    )

    class Meta:
        db_table = "categorias"
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"],
                name="categoria_nombre_unico_por_negocio",
                violation_error_message="Ya existe una categoría con ese nombre en este negocio.",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre


class Proveedor(ModeloDelNegocio):
    """Empresa a la que el negocio le compra mercancía.

    No es un usuario ni un cliente: no entra al sistema y no se le vende, se
    le compra. Su relación con los productos vive en `productos_proveedores`.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.proveedores` y no `negocio.proveedors`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="proveedores",
        verbose_name="negocio",
    )

    razon_social = models.CharField("razón social", max_length=150)
    nit = models.CharField("NIT", max_length=20, blank=True)
    nombre_contacto = models.CharField("persona de contacto", max_length=120, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    correo = models.EmailField("correo", max_length=150, blank=True)
    ciudad = models.CharField("ciudad", max_length=100, blank=True)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    activo = models.BooleanField(
        "activo",
        default=True,
        help_text="Desactivar en vez de borrar: las compras pasadas lo siguen referenciando.",
    )

    class Meta:
        db_table = "proveedores"
        ordering = ["razon_social"]
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nit"],
                condition=~models.Q(nit=""),
                name="proveedor_nit_unico_por_negocio",
                violation_error_message="Ya hay un proveedor con ese NIT en este negocio.",
            ),
        ]

    def __str__(self) -> str:
        return self.razon_social


class Producto(ModeloDelNegocio):
    """Lo que el negocio vende, en cualquiera de los dos canales.

    Un solo catálogo con dos precios: `precio_evento` para la venta directa en
    el bar y `precio_mayorista` para la distribución a tiendas.
    """

    sku = models.CharField("SKU", max_length=50, db_index=True)
    nombre = models.CharField("nombre", max_length=200)
    categoria = models.ForeignKey(
        "catalogo.Categoria",
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="categoría",
    )
    proveedores = models.ManyToManyField(
        "catalogo.Proveedor",
        through="catalogo.ProductoProveedor",
        related_name="productos",
        verbose_name="proveedores",
        blank=True,
    )

    costo = models.DecimalField(
        "costo",
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=(
            "Costo de referencia con el que se calcula el margen. Lo que cobra "
            "cada proveedor va en productos_proveedores."
        ),
    )
    precio_evento = models.DecimalField("precio en evento", max_digits=12, decimal_places=2)
    precio_mayorista = models.DecimalField("precio mayorista", max_digits=12, decimal_places=2)

    activo = models.BooleanField(
        "activo",
        default=True,
        help_text="Desactivar en vez de borrar: los pedidos históricos lo siguen referenciando.",
    )

    class Meta:
        db_table = "productos"
        ordering = ["nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "sku"],
                name="producto_sku_unico_por_negocio",
                violation_error_message="Ya existe un producto con ese SKU en este negocio.",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(costo__gte=0)
                    & models.Q(precio_evento__gte=0)
                    & models.Q(precio_mayorista__gte=0)
                ),
                name="producto_precios_no_negativos",
                violation_error_message="Ni el costo ni los precios pueden ser negativos.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sku} — {self.nombre}"


class ProductoProveedor(ModeloDelNegocio):
    """A cuánto le vende cada proveedor este producto al negocio.

    Existe como tabla propia, y no como una simple clave foránea en
    `productos`, porque el mismo producto se le compra a varios proveedores a
    precios distintos: es justo lo que hay que comparar antes de reponer.
    """

    # Igual que en `Proveedor`: solo para que la inversa se lea en español.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="productos_proveedores",
        verbose_name="negocio",
    )

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.CASCADE,
        related_name="ofertas_de_proveedor",
        verbose_name="producto",
    )
    proveedor = models.ForeignKey(
        "catalogo.Proveedor",
        on_delete=models.PROTECT,
        related_name="ofertas_de_producto",
        verbose_name="proveedor",
    )

    precio_compra = models.DecimalField("precio de compra", max_digits=12, decimal_places=2)
    codigo_proveedor = models.CharField(
        "código del proveedor",
        max_length=50,
        blank=True,
        help_text="Referencia con la que el proveedor identifica el producto en su catálogo.",
    )
    es_principal = models.BooleanField(
        "es el proveedor habitual",
        default=False,
        help_text="Solo uno por producto: al que se le compra por defecto.",
    )

    class Meta:
        db_table = "productos_proveedores"
        ordering = ["producto", "-es_principal", "precio_compra"]
        verbose_name = "producto por proveedor"
        verbose_name_plural = "productos por proveedor"
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "proveedor"],
                name="producto_proveedor_sin_repetir",
                violation_error_message="Ese proveedor ya está registrado para este producto.",
            ),
            models.UniqueConstraint(
                fields=["producto"],
                condition=models.Q(es_principal=True),
                name="producto_con_un_solo_proveedor_principal",
                violation_error_message="El producto ya tiene un proveedor habitual.",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_compra__gte=0),
                name="producto_proveedor_precio_no_negativo",
                violation_error_message="El precio de compra no puede ser negativo.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.producto} ← {self.proveedor}"
