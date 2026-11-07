"""Clientes del bar: a quién se le vende en un evento.

Una fila de aquí es una **ficha**, no una cuenta de acceso: el cliente no
inicia sesión ni tiene contraseña — para eso está `usuarios`. Lo que se guarda
es lo que hace falta para saber a quién se le vendió y si tiene edad para
comprar alcohol.

El dato nunca viaja al chip de la pulsera. El chip solo aporta su UID de
fábrica; el nombre, el documento y la fecha de nacimiento viven aquí. Por eso
una pulsera perdida no filtra los datos de nadie.
"""

from datetime import date

from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio

# Fecha de corte para descartar fechas de nacimiento imposibles o tecleadas al
# revés. No es la mayoría de edad: eso se calcula al consultar (ver `edad`).
FECHA_NACIMIENTO_MINIMA = date(1900, 1, 1)

# Años cumplidos a partir de los cuales se le puede vender alcohol en Colombia.
MAYORIA_DE_EDAD = 18


class Cliente(ModeloDelNegocio):
    """Persona que compra en el bar o en un evento.

    Se identifica por su documento, y no por el nombre, para que quien vuelve
    el sábado siguiente sea la misma ficha con su historial, en vez de "Juan",
    "Juan P" y "Juan Perez" como tres personas distintas.
    """

    class TipoDocumento(models.TextChoices):
        CEDULA = "cedula", "Cédula de ciudadanía"
        CEDULA_EXTRANJERIA = "cedula_extranjeria", "Cédula de extranjería"
        PASAPORTE = "pasaporte", "Pasaporte"
        TARJETA_IDENTIDAD = "tarjeta_identidad", "Tarjeta de identidad"

    tipo_documento = models.CharField(
        "tipo de documento",
        max_length=25,
        choices=TipoDocumento.choices,
        default=TipoDocumento.CEDULA,
    )
    numero_documento = models.CharField("número de documento", max_length=30)
    nombre = models.CharField("nombre", max_length=120)
    apellido = models.CharField("apellido", max_length=120)
    fecha_nacimiento = models.DateField(
        "fecha de nacimiento",
        help_text="Se guarda la fecha y no la edad: la edad cambia sola cada año.",
    )
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    correo = models.EmailField("correo", max_length=150, blank=True)
    notas = models.TextField("notas", blank=True)
    activo = models.BooleanField(
        "activo",
        default=True,
        help_text="Desactivar en vez de borrar: sus cuentas y pedidos lo siguen referenciando.",
    )

    class Meta:
        db_table = "clientes"
        ordering = ["apellido", "nombre"]
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "tipo_documento", "numero_documento"],
                name="cliente_documento_unico_por_negocio",
                violation_error_message="Ya hay un cliente con ese documento en este negocio.",
            ),
            # Solo cordura. La mayoría de edad NO se comprueba aquí: una
            # restricción se evalúa al insertar, y quien hoy tiene 17 mañana
            # tiene 18.
            models.CheckConstraint(
                condition=models.Q(fecha_nacimiento__gt=FECHA_NACIMIENTO_MINIMA),
                name="cliente_fecha_nacimiento_razonable",
                violation_error_message="La fecha de nacimiento no es una fecha válida.",
            ),
        ]
        indexes = [
            # Buscar un cliente por su nombre en la barra es el caso de uso
            # diario; el documento ya va indexado por la restricción de arriba.
            models.Index(
                fields=["negocio", "apellido", "nombre"],
                name="cliente_negocio_nombre_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre_completo} — {self.numero_documento}"

    @property
    def nombre_completo(self) -> str:
        """Nombre y apellido, para mostrar."""
        return f"{self.nombre} {self.apellido}"

    @property
    def edad(self) -> int:
        """Años cumplidos hoy, calculados sobre la fecha de nacimiento."""
        hoy = timezone.localdate()
        cumplio_este_ano = (hoy.month, hoy.day) >= (
            self.fecha_nacimiento.month,
            self.fecha_nacimiento.day,
        )
        return hoy.year - self.fecha_nacimiento.year - (0 if cumplio_este_ano else 1)

    @property
    def es_menor_de_edad(self) -> bool:
        """**Avisa, no bloquea.** La cuenta se abre igual y la pantalla lo pinta
        en rojo: quien decide si se le vende es la persona de la barra, no el
        sistema (decisión 7 del plan de negocio)."""
        return self.edad < MAYORIA_DE_EDAD
