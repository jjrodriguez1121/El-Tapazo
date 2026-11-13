"""Solicitudes de servicio al cliente y su historial de gestión."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from nucleo.models import ModeloDelNegocio


class Pqr(ModeloDelNegocio):
    class Tipo(models.TextChoices):
        QUEJA = "queja", "Queja"
        RECLAMO = "reclamo", "Reclamo"
        PETICION = "peticion", "Petición"
        SUGERENCIA = "sugerencia", "Sugerencia"

    class Ambito(models.TextChoices):
        SERVICIO = "servicio", "Servicio"
        PRODUCTOS = "productos", "Productos"

    class Canal(models.TextChoices):
        TELEFONICO = "telefonico", "Telefónico"
        PRESENCIAL = "presencial", "Presencial"

    class Estado(models.TextChoices):
        RADICADA = "radicada", "Radicada"
        EN_REVISION = "en_revision", "En revisión"
        EN_GESTION = "en_gestion", "En gestión"
        RESPONDIDA = "respondida", "Respondida"
        CERRADA = "cerrada", "Cerrada"
        NO_PROCEDENTE = "no_procedente", "No procedente"

    radicado = models.CharField("radicado", max_length=20, unique=True, blank=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        related_name="pqrs",
        null=True,
        blank=True,
        verbose_name="cliente relacionado",
    )
    venta = models.ForeignKey(
        "ventas.Venta",
        on_delete=models.SET_NULL,
        related_name="pqrs",
        null=True,
        blank=True,
        verbose_name="venta relacionada",
    )
    compra = models.ForeignKey(
        "compras.Compra",
        on_delete=models.SET_NULL,
        related_name="pqrs",
        null=True,
        blank=True,
        verbose_name="compra relacionada",
    )
    nombre_solicitante = models.CharField("nombre del solicitante", max_length=180)
    documento_solicitante = models.CharField("documento del solicitante", max_length=30, blank=True)
    telefono_solicitante = models.CharField("teléfono del solicitante", max_length=30, blank=True)
    correo_solicitante = models.EmailField("correo del solicitante", max_length=150, blank=True)
    tipo = models.CharField("tipo", max_length=12, choices=Tipo.choices)
    ambito = models.CharField("ámbito", max_length=12, choices=Ambito.choices)
    canal = models.CharField("canal", max_length=12, choices=Canal.choices)
    asunto = models.CharField("asunto", max_length=180)
    descripcion = models.TextField("descripción")
    estado = models.CharField(
        "estado", max_length=20, choices=Estado.choices, default=Estado.RADICADA
    )
    fecha_radicacion = models.DateTimeField("fecha de radicación", default=timezone.now)
    fecha_cierre = models.DateTimeField("fecha de cierre", null=True, blank=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pqrs_registradas",
        verbose_name="registrada por",
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pqrs_asignadas",
        null=True,
        blank=True,
        verbose_name="responsable",
    )

    class Meta:
        db_table = "pqrs"
        ordering = ["-fecha_radicacion", "-id"]
        indexes = [
            models.Index(fields=["negocio", "estado"], name="pqr_negocio_estado_idx"),
            models.Index(fields=["negocio", "fecha_radicacion"], name="pqr_negocio_fecha_idx"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.radicado:
            self.radicado = f"PQR-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(radicado=self.radicado)

    def __str__(self):
        return self.radicado or f"PQR-{self.pk}"


class PqrSeguimiento(ModeloDelNegocio):
    class Tipo(models.TextChoices):
        RADICACION = "radicacion", "Radicación"
        NOTA = "nota", "Nota interna"
        RESPUESTA = "respuesta", "Respuesta al solicitante"
        CAMBIO_ESTADO = "cambio_estado", "Cambio de estado"
        ASIGNACION = "asignacion", "Asignación"

    pqr = models.ForeignKey(
        Pqr, on_delete=models.CASCADE, related_name="seguimientos", verbose_name="PQR"
    )
    tipo = models.CharField("tipo de seguimiento", max_length=20, choices=Tipo.choices)
    contenido = models.TextField("detalle", blank=True)
    estado_anterior = models.CharField(
        "estado anterior", max_length=20, choices=Pqr.Estado.choices, blank=True
    )
    estado_nuevo = models.CharField(
        "estado nuevo", max_length=20, choices=Pqr.Estado.choices, blank=True
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="seguimientos_pqr",
        null=True,
        blank=True,
        verbose_name="usuario",
    )
    visible_solicitante = models.BooleanField("visible al solicitante", default=False)

    class Meta:
        db_table = "pqr_seguimientos"
        ordering = ["creado_en", "id"]

    def __str__(self):
        return f"{self.pqr.radicado}: {self.get_tipo_display()}"
