"""Modelos abstractos que heredan las demás apps."""

from django.db import models


class ModeloConFechas(models.Model):
    """Añade a cualquier modelo cuándo se creó y cuándo se actualizó."""

    creado_en = models.DateTimeField("creado en", auto_now_add=True, db_index=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        abstract = True


class ModeloDelNegocio(ModeloConFechas):
    """Modelo que pertenece a un negocio.

    Todo lo que cuelga de un negocio hereda de aquí: así la columna se llama
    igual en todas las tablas, que es de lo que depende el aislamiento por
    negocio (y, más adelante, las políticas de Row Level Security).
    """

    negocio = models.ForeignKey(
        "negocios.Negocio",
        on_delete=models.PROTECT,
        related_name="%(class)ss",
        verbose_name="negocio",
    )

    class Meta:
        abstract = True
