"""Evento / bar: el canal de venta directa.

La cadena es: `evento` → `grupo_evento` (la mesa) → `cliente_evento` (la
persona con su pulsera) → `pedido_evento` → `detalle_pedido_evento`.

- `eventos` — una jornada de venta: la fiesta del sábado, o el día de hoy en
  una licorería que abre a diario. Es lo que se abre al empezar y se cierra al
  cuadrar la caja.
- `pulseras_nfc` — el inventario de chips físicos y su condición. Nada más.
- `grupos_evento` — la mesa, la mancha, el combo: varias cuentas que llegaron
  juntas.
- `clientes_evento` — la cuenta de una persona durante un evento, con pulsera
  o sin ella.
- `pedidos_evento` — una comanda. Sin cuenta asociada es venta de mostrador.
- `detalle_pedido_evento` — los productos de esa comanda, con el precio
  congelado al momento de la venta.
- `alertas_consumo` — cuándo una cuenta cruzó su umbral, y qué se hizo.
- `pagos_evento` — el dinero recibido, y contra qué se recibió.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio
from nucleo.opciones import MetodoDePago


class Evento(ModeloDelNegocio):
    """Una jornada de venta con su apertura y su cierre.

    "Evento" es el nombre que le puso el diseño porque nació pensando en
    fiestas, pero lo que representa es más general: **un periodo de venta que
    se abre, acumula pedidos y se cierra cuadrando la caja**. Una fiesta del
    sábado es un evento; el día de hoy en una licorería que abre a diario
    también. Sin él no habría contra qué agrupar los pedidos ni cómo cerrar
    una caja.

    Puede no tener ubicación (`ubicacion` nulo) porque un evento se puede
    planear antes de decidir dónde se monta la barra.
    """

    class TipoEspacio(models.TextChoices):
        CERRADO = "cerrado", "Espacio cerrado"
        AIRE_LIBRE = "aire_libre", "Al aire libre"

    class Estado(models.TextChoices):
        PLANEADO = "planeado", "Planeado"
        EN_CURSO = "en_curso", "En curso"
        CERRADO = "cerrado", "Cerrado"
        CANCELADO = "cancelado", "Cancelado"

    ubicacion = models.ForeignKey(
        "inventario.Ubicacion",
        on_delete=models.PROTECT,
        related_name="eventos",
        verbose_name="ubicación",
        null=True,
        blank=True,
        help_text="Dónde se monta la barra. Puede definirse después de planear el evento.",
    )
    nombre = models.CharField("nombre", max_length=150)
    tipo_espacio = models.CharField(
        "tipo de espacio",
        max_length=20,
        choices=TipoEspacio.choices,
        default=TipoEspacio.CERRADO,
    )
    fecha_inicio = models.DateTimeField("fecha de inicio")
    fecha_fin = models.DateTimeField(
        "fecha de fin",
        null=True,
        blank=True,
        help_text="Vacío mientras el evento no ha terminado.",
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PLANEADO,
    )

    class Meta:
        db_table = "eventos"
        ordering = ["-fecha_inicio"]
        verbose_name = "evento"
        verbose_name_plural = "eventos"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(fecha_fin__isnull=True)
                    | models.Q(fecha_fin__gt=models.F("fecha_inicio"))
                ),
                name="evento_fechas_coherentes",
                violation_error_message="El evento no puede terminar antes de empezar.",
            ),
            # Lo que hace segura la apertura automática de la jornada: dos
            # peticiones simultáneas del primer pedido del día abrirían dos
            # eventos y partirían el cierre de caja en dos informes sin que
            # nadie se entere. El servicio además bloquea la fila de la
            # ubicación; esto protege los caminos que no pasan por él (el admin
            # de Django, un script, `psql`).
            #
            # La condición sobre `ubicacion` hace falta porque un evento
            # `planeado` todavía no tiene dónde montarse, y varios sin
            # ubicación no se estorban entre sí.
            #
            # El estado va como texto y no como `Estado.EN_CURSO` porque el
            # cuerpo de `Meta` no ve las clases anidadas de `Evento`. Si algún
            # día cambia el valor del enum, la prueba de esta restricción es la
            # que avisa.
            models.UniqueConstraint(
                fields=["ubicacion"],
                condition=models.Q(estado="en_curso", ubicacion__isnull=False),
                name="evento_una_sola_jornada_en_curso_por_ubicacion",
                violation_error_message="Esa ubicación ya tiene una jornada abierta.",
            ),
        ]
        indexes = [
            # "Los eventos de este negocio, del más reciente al más viejo" es
            # la consulta de la pantalla de inicio.
            models.Index(fields=["negocio", "fecha_inicio"], name="evento_negocio_fecha_idx"),
        ]

    def __str__(self) -> str:
        return self.nombre

    @property
    def esta_abierto(self) -> bool:
        """Se le pueden cargar pedidos."""
        return self.estado == self.Estado.EN_CURSO


class PulseraNfc(ModeloDelNegocio):
    """Un chip físico del negocio, identificado por el UID que trae de fábrica.

    **La pulsera no es la identidad: apunta a ella.** En el chip no se escribe
    nada — ni el nombre, ni el documento, ni el saldo. Lo único que aporta es
    su número de serie, y ese número lleva a la cuenta abierta, que lleva al
    cliente. Por eso una pulsera perdida no filtra los datos de nadie: quien la
    encuentre tiene un número, no una cédula.

    `estado` es **solo la condición física** del chip. A quién se le asignó no
    se guarda aquí sino en `clientes_evento`, que es una fila nueva cada vez
    que la pulsera se le pone a alguien. Guardarlo aquí perdería el historial.
    """

    class Estado(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        DANADA = "dañada", "Dañada"
        PERDIDA = "perdida", "Perdida"
        RETIRADA = "retirada", "Retirada"

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.pulseras_nfc` y no `negocio.pulseranfcs`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="pulseras_nfc",
        verbose_name="negocio",
    )

    uid_tag = models.CharField(
        "UID del chip",
        max_length=60,
        help_text="Número de serie que el chip trae de fábrica. No se escribe: se lee.",
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
        help_text="Solo la condición física del chip, no a quién se le prestó.",
    )

    class Meta:
        db_table = "pulseras_nfc"
        ordering = ["uid_tag"]
        verbose_name = "pulsera NFC"
        verbose_name_plural = "pulseras NFC"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "uid_tag"],
                name="pulsera_uid_unico_por_negocio",
                violation_error_message="Ese chip ya está registrado en este negocio.",
            ),
        ]

    def __str__(self) -> str:
        return self.uid_tag

    @property
    def se_puede_asignar(self) -> bool:
        """El chip está sano y en poder del negocio."""
        return self.estado == self.Estado.DISPONIBLE


class DispositivoNfc(ModeloDelNegocio):
    """Un lector de la puerta: el aparato que consulta si una cuenta está saldada.

    Existe para que el punto de control **no lleve la sesión de una persona**.
    Un aparato colgado en la puerta de un bar lo desarma cualquiera, y lo que
    se saque de ahí no puede ser la sesión de un cajero: si alguien abre la
    caja y se lleva el token, se revoca ese y ya.

    Se guarda **solo el hash del token**, igual que en `invitaciones`: quien
    lea la base de datos no puede autenticarse con lo que encuentre. El token
    en claro se enseña una sola vez, al darlo de alta.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.dispositivos_nfc` y no `negocio.dispositivonfcs`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="dispositivos_nfc",
        verbose_name="negocio",
    )

    nombre = models.CharField(
        "nombre",
        max_length=100,
        help_text="Dónde está puesto: «Puerta principal», «Salida de la terraza».",
    )
    hash_token = models.CharField("hash del token", max_length=64)
    activo = models.BooleanField(
        "activo",
        default=True,
        help_text="Desactivar revoca el token sin perder de qué aparato era.",
    )
    ultimo_uso_en = models.DateTimeField(
        "último uso",
        null=True,
        blank=True,
        help_text="Vacío mientras no haya consultado nunca. Sirve para ver si sigue vivo.",
    )

    class Meta:
        db_table = "dispositivos_nfc"
        ordering = ["nombre"]
        verbose_name = "dispositivo NFC"
        verbose_name_plural = "dispositivos NFC"
        constraints = [
            # Único global y no por negocio, por el mismo motivo que
            # `usuarios.correo`: cuando llega la petición del lector todavía no
            # se sabe de qué negocio es — precisamente se averigua por el token.
            models.UniqueConstraint(
                fields=["hash_token"],
                name="dispositivo_nfc_token_unico",
                violation_error_message="Ese token ya está en uso.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.negocio})"


class GrupoEvento(ModeloDelNegocio):
    """La mesa, la mancha, el combo: las cuentas que llegaron juntas.

    Cuando entran quince personas y quieren una sola cuenta compartida, sus
    pulseras quedan todas bajo el mismo grupo. El grupo no acumula el consumo
    —eso lo hace cada `ClienteEvento`—; lo que aporta es el "juntas": permite
    cobrarle a todo el grupo de una vez, o persona por persona, sin cambiar el
    modelo.

    `nombre_referencia` y `mesa_zona` pueden ir vacíos: en una barra sin mesas
    numeradas no hay nada que escribir ahí, y obligar a inventarse un nombre
    solo haría cola.
    """

    class Estado(models.TextChoices):
        ABIERTO = "abierto", "Abierto"
        CERRADO = "cerrado", "Cerrado"

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.grupos_evento` y no `negocio.grupoeventos`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="grupos_evento",
        verbose_name="negocio",
    )

    evento = models.ForeignKey(
        "eventos.Evento",
        on_delete=models.PROTECT,
        related_name="grupos",
        verbose_name="evento",
    )
    nombre_referencia = models.CharField(
        "nombre de referencia",
        max_length=100,
        blank=True,
        help_text='Cómo lo llama el mesero: "la mesa de los primos".',
    )
    mesa_zona = models.CharField("mesa o zona", max_length=50, blank=True)
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTO,
    )

    abierto_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="grupos_abiertos",
        verbose_name="abierto por",
    )
    cerrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="grupos_cerrados",
        verbose_name="cerrado por",
        null=True,
        blank=True,
    )
    cerrado_en = models.DateTimeField(
        "cerrado en",
        null=True,
        blank=True,
        help_text="Vacío mientras el grupo siga abierto.",
    )

    class Meta:
        db_table = "grupos_evento"
        ordering = ["-creado_en"]
        verbose_name = "grupo de evento"
        verbose_name_plural = "grupos de evento"

    def __str__(self) -> str:
        return self.nombre_referencia or self.mesa_zona or f"Grupo {self.pk}"

    @property
    def esta_abierto(self) -> bool:
        """Se le pueden seguir cargando cuentas y pedidos."""
        return self.estado == self.Estado.ABIERTO


class ClienteEvento(ModeloDelNegocio):
    """La cuenta de una persona durante un evento.

    Es la fila que une las tres cosas: la persona (`cliente`), el grupo con el
    que llegó y —si la hay— la pulsera que lleva puesta. Cada vez que a alguien
    se le abre cuenta se crea una fila **nueva**; no se reutiliza la anterior.
    Así la misma pulsera puede pasar por veinte personas en una noche y el
    historial de cada una queda entero.

    `pulsera` puede ir vacía: es la cuenta que se lleva a mano, sin NFC.

    `liberada_en` vacío significa cuenta activa. Al pagar y cerrar se le pone
    la fecha, y desde ese momento la pulsera queda libre para la siguiente
    persona — el "borrado" ocurre aquí, en la base de datos; **el chip físico
    no se toca ni se reescribe jamás**.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.clientes_evento` y no `negocio.clienteeventos`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="clientes_evento",
        verbose_name="negocio",
    )

    grupo_evento = models.ForeignKey(
        "eventos.GrupoEvento",
        on_delete=models.PROTECT,
        related_name="cuentas",
        verbose_name="grupo",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="cuentas_evento",
        verbose_name="cliente",
    )
    pulsera = models.ForeignKey(
        "eventos.PulseraNfc",
        on_delete=models.PROTECT,
        related_name="asignaciones",
        verbose_name="pulsera",
        null=True,
        blank=True,
        help_text="Vacío = cuenta sin pulsera, se lleva a mano.",
    )
    limite_alerta = models.DecimalField(
        "límite de alerta",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monto a partir del cual se avisa. Vacío = sin límite.",
    )

    asignada_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="cuentas_asignadas",
        verbose_name="asignada por",
    )
    liberada_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="cuentas_liberadas",
        verbose_name="liberada por",
        null=True,
        blank=True,
    )
    liberada_en = models.DateTimeField(
        "liberada en",
        null=True,
        blank=True,
        help_text="Vacío = la cuenta sigue abierta.",
    )

    class Meta:
        db_table = "clientes_evento"
        ordering = ["-creado_en"]
        verbose_name = "cuenta de evento"
        verbose_name_plural = "cuentas de evento"
        constraints = [
            # LA MÁS IMPORTANTE DE LA APP: una pulsera no puede estar puesta a
            # dos personas al mismo tiempo. Puede reasignarse mil veces —cada
            # vez es una fila nueva—, pero solo una puede estar sin liberar.
            models.UniqueConstraint(
                fields=["pulsera"],
                condition=models.Q(liberada_en__isnull=True, pulsera__isnull=False),
                name="pulsera_con_una_sola_asignacion_activa",
                violation_error_message="Esa pulsera ya está asignada a una cuenta abierta.",
            ),
            models.CheckConstraint(
                condition=models.Q(limite_alerta__isnull=True) | models.Q(limite_alerta__gte=0),
                name="cliente_evento_limite_no_negativo",
                violation_error_message="El límite de alerta no puede ser negativo.",
            ),
            # O están los dos datos de la liberación, o no está ninguno: una
            # cuenta liberada sin saber por quién no sirve para nada.
            models.CheckConstraint(
                condition=(
                    models.Q(liberada_en__isnull=True, liberada_por__isnull=True)
                    | models.Q(liberada_en__isnull=False, liberada_por__isnull=False)
                ),
                name="cliente_evento_liberacion_coherente",
                violation_error_message="Al liberar una cuenta hay que registrar quién la liberó.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cliente} — grupo {self.grupo_evento_id}"

    @property
    def esta_activa(self) -> bool:
        """La cuenta sigue abierta: se le pueden cargar pedidos."""
        return self.liberada_en is None


class PedidoEvento(ModeloDelNegocio):
    """Una comanda: lo que alguien pidió en la barra, de una sola vez.

    Va atada a una persona concreta (`cliente_evento`) y no al grupo, para
    saber quién pidió qué aunque después paguen entre todos.

    `cliente_evento` vacío es la **venta de mostrador**: quien pide una
    cerveza, paga y se va. No hay cuenta que cobrar después, así que obligarlo
    a registrarse solo haría cola en la barra. El inventario se descuenta
    igual; lo único que no se sabe es a quién se le vendió.

    Por eso `evento` está aquí y no solo a través de la cuenta: la venta de
    mostrador no tiene cuenta, y aun así hay que saber en qué jornada se
    vendió para que el cierre de caja cuadre.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.pedidos_evento` y no `negocio.pedidoeventos`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="pedidos_evento",
        verbose_name="negocio",
    )

    evento = models.ForeignKey(
        "eventos.Evento",
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="evento",
    )
    cliente_evento = models.ForeignKey(
        "eventos.ClienteEvento",
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="cuenta",
        null=True,
        blank=True,
        help_text="Vacío = venta de mostrador: se paga al instante y no hay cuenta.",
    )
    mesero = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pedidos_evento_tomados",
        verbose_name="mesero",
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    class Meta:
        db_table = "pedidos_evento"
        ordering = ["-creado_en"]
        verbose_name = "pedido de evento"
        verbose_name_plural = "pedidos de evento"

    def __str__(self) -> str:
        return f"Pedido {self.pk} — {self.get_estado_display()}"

    @property
    def es_venta_de_mostrador(self) -> bool:
        """Nadie tiene cuenta abierta: se paga al instante."""
        return self.cliente_evento_id is None


class DetallePedidoEvento(ModeloDelNegocio):
    """Una línea de una comanda: qué producto, cuántos y a cuánto.

    `precio_unitario` se copia del producto a propósito, no se consulta al
    mostrar: es la **foto del precio al momento de la venta**. Si no,
    subir mañana el precio de la cerveza cambiaría los pedidos cerrados de
    ayer y ningún cierre de caja volvería a cuadrar.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.detalles_pedido_evento` y no `negocio.detallepedidoeventos`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="detalles_pedido_evento",
        verbose_name="negocio",
    )

    # CASCADE y no PROTECT: una línea no significa nada sin su comanda. Es la
    # única relación de la app donde el hijo no existe sin el padre.
    pedido_evento = models.ForeignKey(
        "eventos.PedidoEvento",
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="pedido",
    )
    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        related_name="detalles_pedido_evento",
        verbose_name="producto",
    )
    cantidad = models.DecimalField("cantidad", max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(
        "precio unitario",
        max_digits=12,
        decimal_places=2,
        help_text="Foto del precio al momento de vender, no el precio de hoy.",
    )

    class Meta:
        db_table = "detalle_pedido_evento"
        ordering = ["id"]
        verbose_name = "detalle de pedido de evento"
        verbose_name_plural = "detalles de pedido de evento"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name="detalle_evento_cantidad_positiva",
                violation_error_message="La cantidad debe ser mayor que cero.",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name="detalle_evento_precio_no_negativo",
                violation_error_message="El precio no puede ser negativo.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} × {self.producto}"

    @property
    def importe(self) -> Decimal:
        """Lo que cuesta esta línea: cantidad por precio."""
        return self.cantidad * self.precio_unitario


class AlertaConsumo(ModeloDelNegocio):
    """Cuándo una cuenta cruzó su umbral de consumo, y qué se hizo al respecto.

    Existe como tabla y no como un simple aviso en pantalla porque el aviso se
    va con el turno y la responsabilidad no: queda quién lo atendió, cuándo y
    qué decidió. En un negocio que vende alcohol, eso es justamente lo que hay
    que poder demostrar después.

    `atendida_en` vacío = la alerta sigue sin atender.
    """

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.alertas_consumo` y no `negocio.alertaconsumos`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="alertas_consumo",
        verbose_name="negocio",
    )

    cliente_evento = models.ForeignKey(
        "eventos.ClienteEvento",
        on_delete=models.PROTECT,
        related_name="alertas",
        verbose_name="cuenta",
    )
    monto_acumulado = models.DecimalField(
        "monto acumulado",
        max_digits=12,
        decimal_places=2,
        help_text="Cuánto llevaba consumido la cuenta cuando saltó la alerta.",
    )
    umbral_superado = models.DecimalField(
        "umbral superado",
        max_digits=12,
        decimal_places=2,
        help_text=(
            "El límite que se cruzó. Se copia para que cambiarlo después no reescriba la historia."
        ),
    )

    atendida_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="alertas_atendidas",
        verbose_name="atendida por",
        null=True,
        blank=True,
    )
    accion_tomada = models.CharField(
        "acción tomada",
        max_length=200,
        blank=True,
        help_text="Vacío mientras la alerta no se atienda.",
    )
    atendida_en = models.DateTimeField(
        "atendida en",
        null=True,
        blank=True,
        help_text="Vacío = sin atender.",
    )
    fecha = models.DateTimeField(
        "fecha",
        default=timezone.now,
        help_text="Cuándo saltó la alerta.",
    )

    class Meta:
        db_table = "alertas_consumo"
        ordering = ["-fecha"]
        verbose_name = "alerta de consumo"
        verbose_name_plural = "alertas de consumo"
        constraints = [
            # O están los dos datos de la atención, o no está ninguno: una
            # alerta atendida sin saber por quién no sirve de nada.
            models.CheckConstraint(
                condition=(
                    models.Q(atendida_en__isnull=True, atendida_por__isnull=True)
                    | models.Q(atendida_en__isnull=False, atendida_por__isnull=False)
                ),
                name="alerta_atencion_coherente",
                violation_error_message="Al atender una alerta hay que registrar quién la atendió.",
            ),
        ]

    def __str__(self) -> str:
        return f"Alerta de {self.monto_acumulado} — cuenta {self.cliente_evento_id}"

    @property
    def esta_atendida(self) -> bool:
        """Alguien ya se hizo cargo de la alerta."""
        return self.atendida_en is not None


class PagoEvento(ModeloDelNegocio):
    """Dinero recibido, y contra qué se recibió.

    Hay tres formas de pagar y una fila solo puede ser **una** de ellas:

    1. el grupo completo → `grupo_evento`, sin cuenta ni pedido;
    2. una persona su parte → `grupo_evento` + `cliente_evento`;
    3. una venta de mostrador → `pedido_evento`, sin grupo.

    La restricción `pago_evento_tiene_un_solo_destino` lo obliga. Sin ella una
    fila podría decir que es de un grupo *y* de un pedido a la vez, y ningún
    reporte de caja cuadraría.
    """

    # Los métodos son los mismos que en el canal mayorista y cambian a la
    # vez, así que la lista vive una sola vez en `nucleo/opciones.py`.
    Metodo = MetodoDePago

    # Se redeclara el campo heredado solo para que la relación inversa se lea
    # `negocio.pagos_evento` y no `negocio.pagoeventos`.
    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="pagos_evento",
        verbose_name="negocio",
    )

    evento = models.ForeignKey(
        "eventos.Evento",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="evento",
    )
    grupo_evento = models.ForeignKey(
        "eventos.GrupoEvento",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="grupo",
        null=True,
        blank=True,
    )
    cliente_evento = models.ForeignKey(
        "eventos.ClienteEvento",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="cuenta",
        null=True,
        blank=True,
        help_text="Solo cuando una persona del grupo paga su parte.",
    )
    pedido_evento = models.ForeignKey(
        "eventos.PedidoEvento",
        on_delete=models.PROTECT,
        related_name="pagos",
        verbose_name="pedido",
        null=True,
        blank=True,
        help_text="Solo en la venta de mostrador, que se paga sin abrir cuenta.",
    )

    monto = models.DecimalField("monto", max_digits=12, decimal_places=2)
    metodo = models.CharField(
        "método de pago",
        max_length=20,
        choices=MetodoDePago.choices,
        default=MetodoDePago.EFECTIVO,
    )
    referencia_transaccion = models.CharField(
        "referencia de la transacción",
        max_length=100,
        blank=True,
        help_text="Número de aprobación o comprobante. Vacío en los pagos en efectivo.",
    )
    recibido_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pagos_recibidos",
        verbose_name="recibido por",
    )
    fecha = models.DateTimeField(
        "fecha",
        default=timezone.now,
        help_text="Cuándo se recibió el dinero, que no siempre es cuándo se registró.",
    )

    class Meta:
        db_table = "pagos_evento"
        ordering = ["-fecha"]
        verbose_name = "pago de evento"
        verbose_name_plural = "pagos de evento"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gt=0),
                name="pago_evento_monto_positivo",
                violation_error_message="El monto de un pago tiene que ser mayor que cero.",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(grupo_evento__isnull=False, pedido_evento__isnull=True)
                    | models.Q(
                        grupo_evento__isnull=True,
                        cliente_evento__isnull=True,
                        pedido_evento__isnull=False,
                    )
                ),
                name="pago_evento_tiene_un_solo_destino",
                violation_error_message=(
                    "Un pago salda un grupo, la parte de una persona o una venta "
                    "de mostrador, nunca dos cosas a la vez."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.monto} por {self.get_metodo_display()}"

    @property
    def es_de_mostrador(self) -> bool:
        """Salda una venta que se pagó al instante, sin cuenta abierta."""
        return self.pedido_evento_id is not None


# Cuatro modelos de esta app tienen un campo `estado` y sus listas de valores no
# son la misma. Sin estos nombres el esquema de la API los bautiza
# `Estado58fEnum`, que no le dice nada a quien genera el cliente del frontend.
# Se exponen a nivel de módulo porque `ENUM_NAME_OVERRIDES` resuelve
# `modulo.atributo`, no atributos de una clase anidada.
ESTADOS_DE_EVENTO = Evento.Estado.choices
ESTADOS_DE_GRUPO = GrupoEvento.Estado.choices
ESTADOS_DE_PEDIDO_EVENTO = PedidoEvento.Estado.choices
ESTADOS_DE_PULSERA = PulseraNfc.Estado.choices
