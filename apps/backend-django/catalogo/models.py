"""Catálogo: qué vende el negocio, de qué tipo y a quién se lo compra.

`categorias` clasifica, `proveedores` son las empresas a las que se compra
y `productos` es lo que se vende.
"""

from decimal import Decimal

from django.db import models

from nucleo.models import ModeloDelNegocio


class Impuesto(ModeloDelNegocio):
    class TipoTratamiento(models.TextChoices):
        GRAVADO = "gravado", "Gravado"
        EXENTO = "exento", "Exento"
        NO_GRAVADO = "no_gravado", "No gravado"

    nombre = models.CharField("nombre", max_length=100)
    porcentaje = models.DecimalField("porcentaje", max_digits=5, decimal_places=2, default=0)
    tipo_tratamiento = models.CharField(
        "tipo de tratamiento", max_length=20, choices=TipoTratamiento.choices,
        default=TipoTratamiento.GRAVADO,
    )
    activo = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "impuestos"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"], name="impuesto_nombre_unico_por_negocio"
            ),
            models.CheckConstraint(
                condition=models.Q(porcentaje__gte=0) & models.Q(porcentaje__lte=100),
                name="impuesto_porcentaje_valido",
            ),
        ]


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
    le compra. Cada compra registra por separado el proveedor y el producto.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.proveedores` y no `negocio.proveedors`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="proveedores",
        verbose_name="negocio",
    )
    tipo_documento = models.CharField("tipo de documento", max_length=20, blank=True)
    numero_documento = models.CharField("número de documento", max_length=30, blank=True)

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

    Cada producto tiene un único precio de venta vigente.
    """

    sku = models.CharField("SKU", max_length=50, db_index=True)
    nombre = models.CharField("nombre", max_length=200)
    categoria = models.ForeignKey(
        "catalogo.Categoria",
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="categoría",
    )
    impuesto = models.ForeignKey(
        "catalogo.Impuesto",
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="impuesto",
        null=True,
        blank=True,
    )
    costo = models.DecimalField(
        "costo",
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=(
            "Costo vigente del producto."
        ),
    )
    precio_venta = models.DecimalField("precio de venta", max_digits=12, decimal_places=2)
    margen_ganancia = models.DecimalField(
        "margen de ganancia",
        max_digits=6,
        decimal_places=2,
        default=Decimal("30.00"),
    )
    precio_venta_automatico = models.BooleanField(
        "precio de venta automático",
        default=True,
    )
    imagen = models.TextField("imagen", blank=True, default="")
    codigo = models.CharField("código", max_length=50, blank=True)
    presentacion = models.CharField("presentación", max_length=30, blank=True)
    contenido_presentacion = models.CharField(
        "contenido de la presentación", max_length=100, blank=True
    )
    stock_minimo = models.PositiveIntegerField("stock mínimo", default=0)
    controla_inventario = models.BooleanField("controla inventario", default=True)

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
                    & models.Q(precio_venta__gte=0)
                ),
                name="producto_precios_no_negativos",
                violation_error_message="Ni el costo ni los precios pueden ser negativos.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sku} — {self.nombre}"
