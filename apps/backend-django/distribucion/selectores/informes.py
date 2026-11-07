"""Lo que vendió y cobró el mayoreo en un rango de fechas.

Es el espejo de `eventos/selectores/informes.py`: cada canal calcula lo suyo
con sus propios repositorios, y `negocios` compone los dos. Así el resumen por
canal no escribe consultas de esta app, que es lo que pide la arquitectura.
"""

from datetime import date
from decimal import Decimal

from distribucion.repositorios import pagos as repositorio_de_pagos
from distribucion.repositorios import pedidos as repositorio
from distribucion.selectores.saldos import CENTAVOS


def ventas_del_canal(*, negocio_id: int, desde: date, hasta: date) -> dict[str, Decimal]:
    """Lo facturado y lo abonado por las tiendas entre dos fechas.

    Aquí los dos números se separan más que en la barra, y no es un error: el
    mayoreo vende a crédito, así que lo cobrado de un mes suele ser lo vendido
    del anterior.
    """
    vendido = repositorio.vendido_entre(negocio_id=negocio_id, desde=desde, hasta=hasta)
    cobrado = repositorio_de_pagos.cobrado_entre(negocio_id=negocio_id, desde=desde, hasta=hasta)
    return {"vendido": vendido.quantize(CENTAVOS), "cobrado": cobrado.quantize(CENTAVOS)}
