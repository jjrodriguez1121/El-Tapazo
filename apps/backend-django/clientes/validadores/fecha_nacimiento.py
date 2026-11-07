"""Cordura de la fecha de nacimiento.

Lo que **no** valida es la mayoría de edad, y es a propósito: la decisión 7 del
plan de negocio dice que ser menor de edad avisa pero no bloquea, y además una
comprobación así caducaría sola — quien hoy tiene 17 mañana tiene 18.
"""

from datetime import date

from django.utils import timezone

from clientes.excepciones import FechaDeNacimientoInvalida
from clientes.models import FECHA_NACIMIENTO_MINIMA


def validar_fecha_de_nacimiento(fecha: date) -> None:
    """Descarta fechas imposibles: del futuro o anteriores a 1900.

    Raises:
        FechaDeNacimientoInvalida.
    """
    if fecha <= FECHA_NACIMIENTO_MINIMA or fecha > timezone.localdate():
        raise FechaDeNacimientoInvalida(fecha=fecha.isoformat())
