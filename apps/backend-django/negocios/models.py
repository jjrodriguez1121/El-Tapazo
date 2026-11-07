"""Negocios: la raíz del modelo de datos."""

from django.db import models

from nucleo.models import ModeloConFechas


class Negocio(ModeloConFechas):
    """Un negocio (bar, distribuidora). Todo lo demás cuelga de aquí."""

    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        SUSPENDIDO = "suspendido", "Suspendido"

    nombre_comercial = models.CharField("nombre comercial", max_length=150)
    nit = models.CharField("NIT", max_length=20, unique=True)
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )

    class Meta:
        db_table = "negocios"
        ordering = ["nombre_comercial"]
        verbose_name = "negocio"
        verbose_name_plural = "negocios"

    def __str__(self) -> str:
        return self.nombre_comercial

    @property
    def esta_operativo(self) -> bool:
        """El negocio puede operar (no está suspendido)."""
        return self.estado == self.Estado.ACTIVO


# Ver el comentario de `ENUM_NAME_OVERRIDES` en `config/settings/base.py`:
# varios campos se llaman `estado` y el esquema necesita distinguirlos.
ESTADOS_DE_NEGOCIO = Negocio.Estado.choices
