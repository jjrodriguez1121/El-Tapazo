"""Inventario: dónde está la mercancía, cuánta hay y cómo llegó ahí.

Tres tablas:

- `ubicaciones` — los lugares físicos donde se guarda o se vende la mercancía.
- `existencias` — el saldo de un producto en una ubicación, ahora mismo.
- `movimientos_inventario` — el kardex: cada entrada y cada salida, con autor.

El kardex es la **fuente de verdad**; `existencias` es un saldo cacheado para
no sumar un millón de filas en cada consulta. Si los dos discrepan, manda el
kardex.
"""

from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio


class Ubicacion(ModeloDelNegocio):
    """Un lugar físico donde hay mercancía: una bodega o un punto de venta.

    Las existencias no son "del negocio" sino "de un sitio": la misma cerveza
    puede estar en la bodega y en la barra del evento, y son cantidades
    distintas que se mueven por separado.
    """

    class Tipo(models.TextChoices):
        BODEGA = "bodega", "Bodega"
        PUNTO_VENTA_EVENTO = "punto_venta_evento", "Punto de venta en evento"

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.ubicaciones` y no `negocio.ubicacions`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="ubicaciones",
        verbose_name="negocio",
    )

    nombre = models.CharField("nombre", max_length=100)
    tipo = models.CharField(
        "tipo",
        max_length=30,
        choices=Tipo.choices,
        default=Tipo.BODEGA,
    )
    direccion = models.CharField("dirección", max_length=255, blank=True)
    activa = models.BooleanField(
        "activa",
        default=True,
        help_text="Desactivar en vez de borrar: el kardex histórico la sigue referenciando.",
    )

    class Meta:
        db_table = "ubicaciones"
        ordering = ["nombre"]
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"],
                name="ubicacion_nombre_unico_por_negocio",
                violation_error_message="Ya existe una ubicación con ese nombre en este negocio.",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre


class Existencia(ModeloDelNegocio):
    """Cuánto hay de un producto en una ubicación.

    Es una **desnormalización deliberada**: el saldo se puede calcular sumando
    el kardex (`SUM(cantidad)` de `movimientos_inventario` para ese producto y
    esa ubicación), pero hacerlo en cada consulta significaría recorrer todo el
    histórico de movimientos cada vez que un mesero mira si queda cerveza.
    Esta tabla guarda ese resultado ya sumado; el kardex sigue siendo la fuente
    de verdad y, si los dos discrepan, manda el kardex.

    Nunca se escribe a mano: la actualizan los servicios que registran un
    movimiento, dentro de la misma transacción y con `F()` para que dos ventas
    simultáneas no se pisen.
    """

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        related_name="existencias",
        verbose_name="producto",
    )
    ubicacion = models.ForeignKey(
        "inventario.Ubicacion",
        on_delete=models.PROTECT,
        related_name="existencias",
        verbose_name="ubicación",
    )
    cantidad_disponible = models.DecimalField(
        "cantidad disponible",
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Saldo cacheado del kardex. La fuente de verdad es movimientos_inventario.",
    )
    # El punto de reposición va aquí y no en `productos` porque es distinto en
    # cada sitio: veinte cervezas en la barra es alerta, en la bodega no.
    cantidad_minima = models.DecimalField(
        "cantidad mínima",
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Por debajo de esto hay que reponer. 0 = sin alerta, no «alerta siempre».",
    )

    class Meta:
        db_table = "existencias"
        ordering = ["ubicacion", "producto"]
        verbose_name = "existencia"
        verbose_name_plural = "existencias"
        constraints = [
            # Un producto tiene un solo saldo por ubicación. Dos filas para el
            # mismo par serían dos verdades sobre la misma cantidad.
            models.UniqueConstraint(
                fields=["producto", "ubicacion"],
                name="existencia_unica_por_producto_y_ubicacion",
                violation_error_message="Ese producto ya tiene existencias en esta ubicación.",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_disponible__gte=0),
                name="existencia_no_negativa",
                violation_error_message="Las existencias no pueden quedar en negativo.",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_minima__gte=0),
                name="existencia_minima_no_negativa",
                violation_error_message="La cantidad mínima no puede ser negativa.",
            ),
        ]
        indexes = [
            # Índice parcial: el informe de reposición no tiene por qué
            # escanear la tabla entera cuando la inmensa mayoría de las filas
            # tendrá 0, que es «sin alerta».
            models.Index(
                fields=["negocio"],
                condition=models.Q(cantidad_minima__gt=0),
                name="existencia_con_minimo_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.producto} en {self.ubicacion}: {self.cantidad_disponible}"

    @property
    def esta_bajo_minimo(self) -> bool:
        """Hay que reponer. Con la mínima en 0 nunca lo está: ese es el «sin alerta»."""
        return self.cantidad_minima > 0 and self.cantidad_disponible < self.cantidad_minima


class MovimientoInventario(ModeloDelNegocio):
    """Una entrada o una salida de mercancía. El kardex.

    Es la **fuente de verdad** del inventario y la tabla que responde "¿dónde
    se perdieron 12 cervezas?". Por eso nada se borra de aquí nunca: un
    movimiento equivocado se corrige con un movimiento contrario, y los dos
    quedan.

    `cantidad` **lleva signo**: positiva suma al inventario, negativa resta.
    Así `SUM(cantidad)` agrupado por producto y ubicación *es* el saldo, sin
    tener que mirar el tipo, y el ajuste que sube y el que baja son el mismo
    tipo en vez de dos. La consecuencia es que un traslado son **dos filas**,
    no una: negativa en el origen y positiva en el destino, con el mismo
    `referencia_id`.
    """

    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SALIDA = "salida", "Salida"
        TRASLADO = "traslado", "Traslado"
        AJUSTE = "ajuste", "Ajuste"
        MERMA = "merma", "Merma"

    class ReferenciaTipo(models.TextChoices):
        PEDIDO_EVENTO = "pedido_evento", "Pedido de evento"
        PEDIDO_DISTRIBUCION = "pedido_distribucion", "Pedido de distribución"
        COMPRA = "compra", "Compra a proveedor"
        TRASLADO = "traslado", "Traslado entre ubicaciones"
        AJUSTE = "ajuste", "Ajuste manual"

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.movimientos_inventario` y no `negocio.movimientoinventarios`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="movimientos_inventario",
        verbose_name="negocio",
    )

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        related_name="movimientos",
        verbose_name="producto",
    )
    ubicacion = models.ForeignKey(
        "inventario.Ubicacion",
        on_delete=models.PROTECT,
        related_name="movimientos",
        verbose_name="ubicación",
    )
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    cantidad = models.DecimalField(
        "cantidad",
        max_digits=12,
        decimal_places=2,
        help_text="Con signo: positiva suma al inventario, negativa resta. Nunca cero.",
    )

    referencia_tipo = models.CharField(
        "tipo de referencia",
        max_length=30,
        choices=ReferenciaTipo.choices,
        help_text="Qué originó el movimiento.",
    )
    referencia_id = models.BigIntegerField(
        "id de la referencia",
        null=True,
        blank=True,
        help_text="Id dentro de la tabla que indica referencia_tipo. Vacío en un ajuste manual.",
    )

    # Obligatorio a propósito: ésta es la tabla donde se detecta un faltante, y
    # un ajuste sin autor es exactamente lo que no puede pasar. Los movimientos
    # que genera el sistema van con un usuario de sistema.
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="movimientos_inventario",
        verbose_name="usuario",
    )
    nota = models.TextField("nota", blank=True)
    fecha = models.DateTimeField(
        "fecha",
        default=timezone.now,
        help_text="Cuándo ocurrió el movimiento, que no siempre es cuándo se registró.",
    )

    class Meta:
        db_table = "movimientos_inventario"
        ordering = ["-fecha"]
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(cantidad=0),
                name="movimiento_cantidad_distinta_de_cero",
                violation_error_message="Un movimiento de cero no es un movimiento.",
            ),
        ]
        indexes = [
            # No empieza por negocio_id, y es a propósito: la consulta estrella
            # es el kardex de UN producto en un rango de fechas, y producto_id
            # es mucho más selectivo. Además filtrar por producto ya implica el
            # negocio, porque el producto es de un solo negocio.
            models.Index(fields=["producto", "fecha"], name="movimiento_producto_fecha_idx"),
            # Para ir de un pedido a los movimientos que generó.
            models.Index(
                fields=["referencia_tipo", "referencia_id"],
                name="movimiento_referencia_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} de {self.cantidad} — {self.producto}"

    @property
    def suma_al_inventario(self) -> bool:
        """El movimiento aumenta el saldo (cantidad positiva)."""
        return self.cantidad > 0


# Dos campos distintos se llaman `tipo` y sus listas de valores no son la misma.
# Sin estos nombres, el esquema de la API los bautiza `Tipo34fEnum`, que no le
# dice nada a quien genera el cliente del frontend. Se exponen a nivel de módulo
# porque `ENUM_NAME_OVERRIDES` resuelve `modulo.atributo`, no atributos de una
# clase anidada.
TIPOS_DE_UBICACION = Ubicacion.Tipo.choices
TIPOS_DE_MOVIMIENTO = MovimientoInventario.Tipo.choices
