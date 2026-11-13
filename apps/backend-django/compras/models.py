from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio


class Compra(ModeloDelNegocio):
    proveedor = models.ForeignKey(
        "catalogo.Proveedor", on_delete=models.PROTECT, related_name="compras"
    )
    usuario = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.PROTECT, related_name="compras_registradas"
    )
    numero_compra = models.CharField("número de compra", max_length=30, unique=True)
    numero_factura = models.CharField("número de factura", max_length=50, blank=True)
    fecha_compra = models.DateTimeField("fecha de compra", default=timezone.now)
    condicion_pago = models.CharField(
        "condición de pago", max_length=15,
        choices=[("CONTADO", "Contado"), ("CREDITO", "Crédito")],
    )
    fecha_vencimiento = models.DateField("fecha de vencimiento", null=True, blank=True)
    subtotal = models.DecimalField("subtotal", max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField("descuento", max_digits=14, decimal_places=2, default=0)
    total_iva = models.DecimalField("total IVA", max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField("total", max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(
        "estado", max_length=15,
        choices=[("BORRADOR", "Borrador"), ("RECIBIDA", "Recibida"), ("ANULADA", "Anulada")],
        default="BORRADOR",
    )

    class Meta:
        db_table = "compras"
        ordering = ["-fecha_compra"]


class DetalleCompra(ModeloDelNegocio):
    compra = models.ForeignKey(
        "compras.Compra", on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "catalogo.Producto", on_delete=models.PROTECT, related_name="detalles_compra"
    )
    cantidad = models.PositiveIntegerField("cantidad")
    costo_unitario = models.DecimalField("costo unitario", max_digits=14, decimal_places=2)
    porcentaje_iva = models.DecimalField("porcentaje IVA", max_digits=5, decimal_places=2, default=0)
    base_gravable = models.DecimalField("base gravable", max_digits=14, decimal_places=2, default=0)
    valor_iva = models.DecimalField("valor IVA", max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField("descuento", max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField("subtotal", max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "detalles_compra"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name="detalle_compra_cantidad_positiva"),
        ]


class PagoCompra(ModeloDelNegocio):
    compra = models.ForeignKey(
        "compras.Compra", on_delete=models.PROTECT, related_name="pagos"
    )
    metodo_pago = models.ForeignKey(
        "ventas.MetodoPago", on_delete=models.PROTECT, related_name="pagos_compra"
    )
    usuario = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.PROTECT, related_name="pagos_compra_registrados"
    )
    fecha_pago = models.DateTimeField("fecha de pago", default=timezone.now)
    valor = models.DecimalField("valor", max_digits=14, decimal_places=2)
    referencia = models.CharField("referencia", max_length=100, blank=True)
    estado = models.CharField(
        "estado", max_length=15,
        choices=[("CONFIRMADO", "Confirmado"), ("ANULADO", "Anulado")],
        default="CONFIRMADO",
    )

    class Meta:
        db_table = "pagos_compras"
        ordering = ["-fecha_pago"]


class CuentaPorPagar(ModeloDelNegocio):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PARCIAL = "PARCIAL", "Abonada parcialmente"
        PAGADA = "PAGADA", "Pagada"
        VENCIDA = "VENCIDA", "Vencida"

    compra = models.OneToOneField(
        "compras.Compra",
        on_delete=models.PROTECT,
        related_name="cuenta_por_pagar",
    )
    fecha_vencimiento = models.DateField("fecha de vencimiento")
    total = models.DecimalField("total", max_digits=14, decimal_places=2)
    saldo = models.DecimalField("saldo", max_digits=14, decimal_places=2)
    estado = models.CharField(
        "estado", max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )

    class Meta:
        db_table = "cuentas_por_pagar"
        ordering = ["fecha_vencimiento"]
        constraints = [
            models.CheckConstraint(condition=models.Q(total__gt=0), name="cuenta_por_pagar_total_positivo"),
            models.CheckConstraint(condition=models.Q(saldo__gte=0), name="cuenta_por_pagar_saldo_no_negativo"),
            models.CheckConstraint(condition=models.Q(saldo__lte=models.F("total")), name="cuenta_por_pagar_saldo_valido"),
        ]
