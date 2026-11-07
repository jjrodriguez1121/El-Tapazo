"""Distribución: el canal mayorista.

Venta a tiendas, normalmente con crédito. Mismo catálogo que el bar, otro
precio (`producto.precio_mayorista`).

Tres tablas:

- `clientes_distribucion` — las tiendas a las que se les vende al por mayor.
- `pedidos_distribucion` — una orden mayorista, desde que se toma hasta que se
  entrega.
- `detalle_pedido_distribucion` — los productos de esa orden, con el precio
  congelado al momento de la venta.
- `pagos_distribucion` — lo que la tienda va abonando contra ese pedido. Aquí
  **sí hay abonos**, al revés que en el bar: una tienda a 30 días paga en
  varias veces.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio
from nucleo.opciones import MetodoDePago


class ClienteDistribucion(ModeloDelNegocio):
    """Tienda a la que el negocio le vende al por mayor, normalmente a crédito.

    Es una tabla aparte de `clientes` y no una columna `tipo` dentro de ella
    porque son dos negocios distintos: la tienda se identifica por NIT y paga a
    los N días; la persona del bar se identifica por documento y paga esa misma
    noche. Juntarlas dejaría la mitad de las columnas vacías en cada fila.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.clientes_distribucion` y no `negocio.clientedistribucions`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="clientes_distribucion",
        verbose_name="negocio",
    )

    razon_social = models.CharField("razón social", max_length=150)
    nit = models.CharField("NIT", max_length=20)
    nombre_contacto = models.CharField("persona de contacto", max_length=120, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    correo = models.EmailField("correo", max_length=150, blank=True)
    ciudad = models.CharField("ciudad", max_length=100, blank=True)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    # IntegerField y no PositiveIntegerField: este lleva su propia restricción
    # con nombre generado, y el mensaje que ve el usuario sería el de PostgreSQL.
    # Con la restricción declarada abajo el mensaje sale en español.
    dias_credito = models.IntegerField(
        "días de crédito",
        default=0,
        help_text="0 = paga de contado.",
    )
    activo = models.BooleanField(
        "activo",
        default=True,
        help_text="Desactivar en vez de borrar: sus pedidos históricos lo siguen referenciando.",
    )

    class Meta:
        db_table = "clientes_distribucion"
        ordering = ["razon_social"]
        verbose_name = "cliente de distribución"
        verbose_name_plural = "clientes de distribución"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nit"],
                name="cliente_distribucion_nit_unico_por_negocio",
                violation_error_message="Ya hay un cliente con ese NIT en este negocio.",
            ),
            models.CheckConstraint(
                condition=models.Q(dias_credito__gte=0),
                name="cliente_distribucion_credito_no_negativo",
                violation_error_message="Los días de crédito no pueden ser negativos.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.razon_social} ({self.nit})"

    @property
    def paga_de_contado(self) -> bool:
        """No tiene crédito: paga al recibir."""
        return self.dias_credito == 0


class PedidoDistribucion(ModeloDelNegocio):
    """Una orden mayorista: lo que una tienda pidió, de una sola vez.

    `fecha_pedido` y `fecha_entrega` son dos fechas distintas y las dos
    importan: entre una y otra corre el plazo de crédito de la tienda, y la
    diferencia entre ambas es lo que dice si la ruta está cumpliendo.

    `fecha_entrega` vacía = el pedido todavía no se ha entregado.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_RUTA = "en_ruta", "En ruta"
        ENTREGADO = "entregado", "Entregado"
        NO_ENTREGADO = "no_entregado", "No entregado"
        CANCELADO = "cancelado", "Cancelado"

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.pedidos_distribucion` y no `negocio.pedidodistribucions`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="pedidos_distribucion",
        verbose_name="negocio",
    )

    cliente_distribucion = models.ForeignKey(
        "distribucion.ClienteDistribucion",
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="cliente",
    )
    # Quién tomó el pedido. Obligatorio: es a quien se le pregunta cuando la
    # tienda dice que pidió otra cosa.
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pedidos_distribucion",
        verbose_name="tomado por",
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fecha_pedido = models.DateTimeField(
        "fecha del pedido",
        default=timezone.now,
        help_text="Cuándo lo pidió la tienda. Desde aquí corre el plazo de crédito.",
    )
    fecha_entrega = models.DateTimeField(
        "fecha de entrega",
        null=True,
        blank=True,
        help_text="Vacío mientras el pedido no se haya entregado.",
    )
    # Texto opcional: cadena vacía, nunca NULL. Solo se llena cuando el pedido
    # volvió en el camión, y entonces es obligatorio.
    motivo_no_entrega = models.TextField(
        "motivo de la no entrega",
        blank=True,
        help_text="Por qué no se pudo entregar. Obligatorio en el estado «no entregado».",
    )

    class Meta:
        db_table = "pedidos_distribucion"
        ordering = ["-fecha_pedido"]
        verbose_name = "pedido de distribución"
        verbose_name_plural = "pedidos de distribución"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(fecha_entrega__isnull=True)
                    | models.Q(fecha_entrega__gte=models.F("fecha_pedido"))
                ),
                name="pedido_distribucion_fechas_coherentes",
                violation_error_message="Un pedido no puede entregarse antes de haberse pedido.",
            ),
            # Un pedido que volvió sin entregarse y no dice por qué no sirve
            # para nada: no se puede llamar a la tienda ni corregir la ruta.
            #
            # El estado va como texto y no como `Estado.NO_ENTREGADO` porque el
            # cuerpo de `Meta` no ve las clases anidadas del modelo.
            models.CheckConstraint(
                condition=~models.Q(estado="no_entregado") | ~models.Q(motivo_no_entrega=""),
                name="pedido_distribucion_no_entregado_con_motivo",
                violation_error_message="Hay que decir por qué no se pudo entregar.",
            ),
        ]

    def __str__(self) -> str:
        return f"Pedido {self.pk} — {self.cliente_distribucion}"

    @property
    def esta_entregado(self) -> bool:
        """La mercancía ya llegó a la tienda."""
        return self.fecha_entrega is not None

    @property
    def se_puede_despachar(self) -> bool:
        """Todavía en la bodega: nunca salió, o volvió sin entregarse."""
        return self.estado in (self.Estado.PENDIENTE, self.Estado.NO_ENTREGADO)


class DetallePedidoDistribucion(ModeloDelNegocio):
    """Una línea de una orden mayorista: qué producto, cuántos y a cuánto.

    `precio_unitario` se copia del producto a propósito: es la **foto del
    precio mayorista al momento de la venta**. Si no, cambiar mañana la lista
    de precios reescribiría las facturas de las tiendas de este mes.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.detalles_pedido_distribucion` y no
    # `negocio.detallepedidodistribucions`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="detalles_pedido_distribucion",
        verbose_name="negocio",
    )

    # CASCADE y no PROTECT: una línea no significa nada sin su pedido.
    pedido_distribucion = models.ForeignKey(
        "distribucion.PedidoDistribucion",
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="pedido",
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        related_name="detalles_pedido_distribucion",
        verbose_name="producto",
    )
    cantidad = models.DecimalField("cantidad", max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(
        "precio unitario",
        max_digits=12,
        decimal_places=2,
        help_text="Foto del precio mayorista al momento de vender, no el precio de hoy.",
    )

    class Meta:
        db_table = "detalle_pedido_distribucion"
        ordering = ["id"]
        verbose_name = "detalle de pedido de distribución"
        verbose_name_plural = "detalles de pedido de distribución"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name="detalle_distribucion_cantidad_positiva",
                violation_error_message="La cantidad debe ser mayor que cero.",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name="detalle_distribucion_precio_no_negativo",
                violation_error_message="El precio no puede ser negativo.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} × {self.producto}"

    @property
    def importe(self) -> Decimal:
        """Lo que cuesta esta línea: cantidad por precio."""
        return self.cantidad * self.precio_unitario


class PagoDistribucion(ModeloDelNegocio):
    """Dinero que una tienda abona contra un pedido mayorista.

    Es una tabla aparte de `pagos_evento` y no una columna más allí. Reutilizar
    aquella obligaría a hacer nulo su `evento_id` y su restricción
    `pago_evento_tiene_un_solo_destino` pasaría a tener cuatro destinos
    posibles: una fila podría decir que es de un evento *y* de una tienda. Dos
    canales distintos, dos tablas — el mismo argumento que separó `clientes` de
    `clientes_distribucion`.

    **Aquí sí hay abonos**, justo al revés que en el bar: una cuenta del bar se
    salda con un solo pago que cubre el total, y una tienda a 30 días paga en
    varias veces. Es a propósito.

    Que la suma de los abonos no pase del total del pedido **no está declarado
    en la base**: es un agregado, y una restricción de fila no puede mirar las
    otras filas. Lo comprueba el servicio, bloqueando el pedido antes de sumar.
    Es una limitación de SQL, no una decisión de diseño.
    """

    Metodo = MetodoDePago

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.pagos_distribucion` y no `negocio.pagodistribucions`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="pagos_distribucion",
        verbose_name="negocio",
    )

    pedido_distribucion = models.ForeignKey(
        "distribucion.PedidoDistribucion",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="pedido",
    )
    monto = models.DecimalField("monto", max_digits=12, decimal_places=2)
    metodo = models.CharField(
        "método de pago",
        max_length=20,
        choices=MetodoDePago.choices,
        default=MetodoDePago.TRANSFERENCIA,
    )
    referencia_transaccion = models.CharField(
        "referencia de la transacción",
        max_length=100,
        blank=True,
        help_text="Número de comprobante o de consignación. Vacío en los pagos en efectivo.",
    )
    recibido_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pagos_distribucion_recibidos",
        verbose_name="recibido por",
    )
    fecha = models.DateTimeField(
        "fecha",
        default=timezone.now,
        help_text="Cuándo se recibió el dinero, que no siempre es cuándo se registró.",
    )

    class Meta:
        db_table = "pagos_distribucion"
        ordering = ["-fecha"]
        verbose_name = "pago de distribución"
        verbose_name_plural = "pagos de distribución"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gt=0),
                name="pago_distribucion_monto_positivo",
                violation_error_message="El monto de un pago debe ser mayor que cero.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.monto} — {self.pedido_distribucion}"


# Ver el comentario de `ENUM_NAME_OVERRIDES` en `config/settings/base.py`:
# varios campos se llaman `estado` y el esquema necesita distinguirlos.
ESTADOS_DE_PEDIDO_DISTRIBUCION = PedidoDistribucion.Estado.choices
