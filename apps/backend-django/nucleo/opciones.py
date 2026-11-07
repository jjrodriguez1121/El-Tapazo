"""Listas de valores que usan dos o más apps.

Aquí solo entra lo que **cambia a la vez en todas partes**. Si mañana el
negocio empieza a aceptar Daviplata, lo acepta en el bar y en el mayoreo el
mismo día: es un solo conocimiento y vive en un solo sitio.
"""

from django.db import models


class MetodoDePago(models.TextChoices):
    """Cómo entró el dinero. Igual en el bar (`pagos_evento`) y en el canal
    mayorista (`pagos_distribucion`)."""

    EFECTIVO = "efectivo", "Efectivo"
    TARJETA = "tarjeta", "Tarjeta"
    NEQUI = "nequi", "Nequi"
    TRANSFERENCIA = "transferencia", "Transferencia"
    OTRO = "otro", "Otro"
