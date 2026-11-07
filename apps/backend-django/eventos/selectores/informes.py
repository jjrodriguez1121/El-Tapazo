"""Lo que vendió y cobró la barra en un rango de fechas.

El informe **de una jornada** —el cierre de caja— vive en `eventos.py` y mira
un evento concreto. Este mira un rango de fechas y existe para que `negocios`
pueda componer el resumen por canal sin escribir consultas de esta app: cada
app calcula lo suyo con sus propios repositorios.
"""

from datetime import date
from decimal import Decimal

from eventos.repositorios import pagos as repositorio_de_pagos
from eventos.repositorios import pedidos as repositorio
from eventos.selectores.saldos import CENTAVOS, TIPO_DEL_IMPORTE


def ventas_del_canal(*, negocio_id: int, desde: date, hasta: date) -> dict[str, Decimal]:
    """Lo vendido y lo cobrado en la barra entre dos fechas, las dos incluidas.

    Los dos números no tienen por qué coincidir, y ahí está la gracia: lo
    vendido es lo que salió por la barra, lo cobrado es lo que entró en caja.
    """
    vendido = repositorio.vendido_entre(
        negocio_id=negocio_id, desde=desde, hasta=hasta, tipo_del_importe=TIPO_DEL_IMPORTE
    )
    cobrado = repositorio_de_pagos.cobrado_entre(negocio_id=negocio_id, desde=desde, hasta=hasta)
    return {"vendido": vendido.quantize(CENTAVOS), "cobrado": cobrado.quantize(CENTAVOS)}
