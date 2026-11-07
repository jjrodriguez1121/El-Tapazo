"""Fechas escritas para una persona.

Los nombres de los meses salen de una tupla y **no de `date_format` con
locale**: depender de que las traducciones de Django estén compiladas para que
una jornada se llame bien es una dependencia gratuita que falla en producción y
no en local.
"""

from datetime import date

MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def en_palabras(fecha: date) -> str:
    """`8 de septiembre`. Sin el año, que en el nombre de una jornada sobra."""
    return f"{fecha.day} de {MESES[fecha.month - 1]}"
