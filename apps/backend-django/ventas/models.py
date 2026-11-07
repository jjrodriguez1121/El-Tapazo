"""Ventas y cuentas por cobrar.

Una venta puede ser de contado o a crédito. Las de crédito generan exactamente
una cuenta por cobrar, cuyo saldo se actualiza con cada abono.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio


class MetodoPago(ModeloDelNegocio):
    nombre = models.CharField("nombre", max_length=50)
    estado = models.BooleanField("estado", default=True)

    class Meta:
        db_table = "metodos_pago"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"], name="metodo_pago_nombre_unico_por_negocio"
            )
        ]


class Venta(ModeloDelNegocio):
    class TipoPago(models.TextChoices):
        CONTADO = "contado", "Contado"
        CREDITO = "credito", "Crédito"

    class Estado(models.TextChoices):
        PAGADA = "pagada", "Pagada"
        PENDIENTE = "pendiente", "Pendiente de cobro"
        ANULADA = "anulada", "Anulada"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="ventas",
        null=True,
        blank=True,
        verbose_name="cliente",
    )
    numero_venta = models.CharField("número de venta", max_length=30, blank=True)
    fecha_vencimiento = models.DateField("fecha de vencimiento", null=True, blank=True)
    subtotal = models.DecimalField("subtotal", max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField("descuento", max_digits=14, decimal_places=2, default=0)
    total_iva = models.DecimalField("total IVA", max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField("total", max_digits=14, decimal_places=2, default=0)
    vendedor = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="ventas_registradas",
        verbose_name="vendedor",
    )
    tipo_pago = models.CharField("tipo de pago", max_length=10, choices=TipoPago.choices)
    estado = models.CharField("estado", max_length=12, choices=Estado.choices)
    fecha = models.DateTimeField("fecha", default=timezone.now)
    observaciones = models.TextField("observaciones", blank=True)

    class Meta:
        db_table = "ventas"
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(tipo_pago="contado", estado="pagada")
                    | models.Q(tipo_pago="credito", estado="pendiente")
                    | models.Q(estado="anulada")
                ),
                name="venta_estado_coherente_con_pago",
            ),
        ]

    def __str__(self) -> str:
        return f"Venta {self.pk}"


class DetalleVenta(ModeloDelNegocio):
    venta = models.ForeignKey(
        "ventas.Venta", on_delete=models.CASCADE, related_name="detalles", verbose_name="venta"
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        related_name="detalles_venta",
        verbose_name="producto",
    )
    cantidad = models.DecimalField("cantidad", max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField("precio unitario", max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField("costo unitario", max_digits=14, decimal_places=2, default=0)
    porcentaje_iva = models.DecimalField("porcentaje IVA", max_digits=5, decimal_places=2, default=0)
    base_gravable = models.DecimalField("base gravable", max_digits=14, decimal_places=2, default=0)
    valor_iva = models.DecimalField("valor IVA", max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField("descuento", max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField("subtotal", max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "detalles_venta"
        constraints = [
            models.UniqueConstraint(fields=["venta", "producto"], name="detalle_venta_producto_unico"),
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name="detalle_venta_cantidad_positiva"),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0), name="detalle_venta_precio_no_negativo"
            ),
        ]


class CuentaPorCobrar(ModeloDelNegocio):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PARCIAL = "parcial", "Abonada parcialmente"
        PAGADA = "pagada", "Pagada"
        VENCIDA = "vencida", "Vencida"

    venta = models.OneToOneField(
        "ventas.Venta",
        on_delete=models.PROTECT,
        related_name="cuenta_por_cobrar",
        verbose_name="venta",
    )
    fecha_vencimiento = models.DateField("fecha de vencimiento")
    total = models.DecimalField("total", max_digits=14, decimal_places=2)
    saldo = models.DecimalField("saldo", max_digits=14, decimal_places=2)
    estado = models.CharField("estado", max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)

    class Meta:
        db_table = "cuentas_por_cobrar"
        ordering = ["fecha_vencimiento"]
        constraints = [
            models.CheckConstraint(condition=models.Q(total__gt=0), name="cuenta_total_positivo"),
            models.CheckConstraint(condition=models.Q(saldo__gte=0), name="cuenta_saldo_no_negativo"),
            models.CheckConstraint(condition=models.Q(saldo__lte=models.F("total")), name="cuenta_saldo_no_supera_total"),
        ]


class PagoVenta(ModeloDelNegocio):
    """Un cobro de contado o un abono a una cuenta por cobrar."""

    venta = models.ForeignKey(
        "ventas.Venta", on_delete=models.PROTECT, related_name="pagos", verbose_name="venta"
    )
    cuenta_por_cobrar = models.ForeignKey(
        "ventas.CuentaPorCobrar",
        on_delete=models.PROTECT,
        related_name="abonos",
        null=True,
        blank=True,
        verbose_name="cuenta por cobrar",
    )
    monto = models.DecimalField("monto", max_digits=14, decimal_places=2)
    metodo_pago = models.ForeignKey(
        "ventas.MetodoPago", on_delete=models.PROTECT, related_name="pagos_venta",
        null=True, blank=True,
    )
    metodo = models.CharField("medio de pago legado", max_length=20, blank=True)
    referencia_transaccion = models.CharField("referencia", max_length=100, blank=True)
    recibido_por = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.PROTECT, related_name="pagos_recibidos", verbose_name="recibido por"
    )
    fecha = models.DateTimeField("fecha", default=timezone.now)

    class Meta:
        db_table = "pagos_venta"
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(condition=models.Q(monto__gt=0), name="pago_venta_monto_positivo"),
        ]


ESTADOS_DE_VENTA = Venta.Estado.choices
ESTADOS_DE_CUENTA_POR_COBRAR = CuentaPorCobrar.Estado.choices
