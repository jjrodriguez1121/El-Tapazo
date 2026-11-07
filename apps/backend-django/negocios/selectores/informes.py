"""El resumen de ventas por canal: cuánto puso la barra y cuánto el mayoreo.

Vive aquí y no en una app `informes` porque el dato que cruza los dos canales
es **el negocio**, y porque cada canal calcula lo suyo en su propia app: este
módulo solo suma lo que le dan. Si mañana hay un tercer canal, se añade una
línea aquí y sus consultas van en su app, no en esta.

`vendido` y `cobrado` son dos números distintos a propósito. En la barra casi
coinciden —se cobra la misma noche—; en el mayoreo no, porque se vende a
crédito: lo cobrado de septiembre suele ser lo vendido de agosto.
"""

from datetime import date

from django.utils import timezone

from distribucion.selectores import informes as informes_de_mayoreo
from eventos.selectores import informes as informes_de_bar
from negocios.excepciones import RangoDeFechasInvalido

CANAL_BAR = "bar"
CANAL_MAYOREO = "mayoreo"


def resumen_de_ventas(
    *, negocio_id: int, desde: date | None = None, hasta: date | None = None
) -> dict:
    """Lo vendido y lo cobrado por cada canal en un rango de fechas.

    Sin fechas, el mes en curso: es la pregunta que se hace de verdad —"¿cómo
    vamos este mes?"— y evita que el informe recorra toda la historia cada vez
    que alguien abre la pantalla.

    Raises:
        RangoDeFechasInvalido: la fecha de inicio es posterior a la del final.
    """
    desde, hasta = _rango(desde=desde, hasta=hasta)

    bar = informes_de_bar.ventas_del_canal(negocio_id=negocio_id, desde=desde, hasta=hasta)
    mayoreo = informes_de_mayoreo.ventas_del_canal(negocio_id=negocio_id, desde=desde, hasta=hasta)
    return {
        "desde": desde,
        "hasta": hasta,
        "canales": [
            {"canal": CANAL_BAR, **bar},
            {"canal": CANAL_MAYOREO, **mayoreo},
        ],
        "vendido_total": bar["vendido"] + mayoreo["vendido"],
        "cobrado_total": bar["cobrado"] + mayoreo["cobrado"],
    }


def _rango(*, desde: date | None, hasta: date | None) -> tuple[date, date]:
    """El rango pedido, o el mes en curso.

    `timezone.localdate()` y **nunca `date.today()`**: un cierre a las once de
    la noche cae en el día siguiente en UTC, y el resumen del mes se comería el
    primero o el último día.

    Raises:
        RangoDeFechasInvalido.
    """
    hoy = timezone.localdate()
    desde = desde or hoy.replace(day=1)
    hasta = hasta or hoy
    if desde > hasta:
        raise RangoDeFechasInvalido(desde=desde.isoformat(), hasta=hasta.isoformat())
    return desde, hasta
