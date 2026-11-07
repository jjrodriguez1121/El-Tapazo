"""Consultas al ORM sobre `existencias`, el saldo cacheado del kardex.

Dos cosas de este módulo no son estilo, son corrección:

* `bloquear` toma **una fila concreta** por su clave única. Nunca se hace
  `select_for_update()` sobre un queryset filtrado: ahí el orden en que se
  toman los bloqueos lo elige el planificador y deja de ser predecible, que es
  justo lo que evita los interbloqueos.

* `sumar` escribe con `update()` y `F()`, nunca con `save()`. Con `save()`
  habría que leer el saldo en Python, sumarle y volver a escribir, y dos ventas
  simultáneas se pisarían. Además, asignar `F(...)` a un atributo y luego
  leerlo no devuelve un `Decimal` sino una expresión, y cualquier cuenta con
  ella genera SQL en silencio.
"""

from decimal import Decimal

from django.db.models import F, QuerySet, Sum
from django.utils import timezone

from inventario.models import Existencia


def bloquear(*, producto_id: int, ubicacion_id: int, negocio_id: int) -> Existencia | None:
    """La fila del saldo, bloqueada hasta el final de la transacción.

    Devuelve `None` si no existe todavía. **Ojo: un `select_for_update()` sobre
    una fila que no existe no bloquea nada**, así que quien cree la fila no
    está protegido por este bloqueo sino por la restricción
    `existencia_unica_por_producto_y_ubicacion`.
    """
    return (
        Existencia.objects.select_for_update()
        .filter(producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id)
        .first()
    )


def obtener(*, producto_id: int, ubicacion_id: int, negocio_id: int) -> Existencia | None:
    """Lectura sin bloquear. Para consultar, nunca para decidir si hay stock."""
    return Existencia.objects.filter(
        producto_id=producto_id, ubicacion_id=ubicacion_id, negocio_id=negocio_id
    ).first()


def crear_en_cero(*, producto_id: int, ubicacion_id: int, negocio_id: int) -> Existencia:
    return Existencia.objects.create(
        producto_id=producto_id,
        ubicacion_id=ubicacion_id,
        negocio_id=negocio_id,
        cantidad_disponible=Decimal("0.00"),
    )


def sumar(*, existencia_id: int, cantidad: Decimal) -> None:
    """Suma al saldo en una sola sentencia atómica.

    `actualizado_en` va explícito porque un `update()` **no dispara
    `auto_now`**: sin esta línea la columna se quedaría congelada en la fecha
    de creación y nadie lo notaría hasta que alguien preguntara cuándo se movió.
    """
    Existencia.objects.filter(pk=existencia_id).update(
        cantidad_disponible=F("cantidad_disponible") + cantidad,
        actualizado_en=timezone.now(),
    )


def fijar_saldo(*, existencia_id: int, cantidad: Decimal) -> None:
    """Escribe el saldo tal cual. Solo lo usa la reconstrucción desde el kardex."""
    Existencia.objects.filter(pk=existencia_id).update(
        cantidad_disponible=cantidad, actualizado_en=timezone.now()
    )


def fijar_cantidad_minima(*, existencia_id: int, cantidad_minima: Decimal) -> None:
    Existencia.objects.filter(pk=existencia_id).update(
        cantidad_minima=cantidad_minima, actualizado_en=timezone.now()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[Existencia]:
    return Existencia.objects.filter(negocio_id=negocio_id)


def de_una_ubicacion(*, ubicacion_id: int, negocio_id: int) -> QuerySet[Existencia]:
    return Existencia.objects.filter(ubicacion_id=ubicacion_id, negocio_id=negocio_id)


def valor_total(*, negocio_id: int, tipo_del_importe) -> Decimal | None:
    """Lo que vale el inventario a precio de costo. Lo multiplica la base."""
    return Existencia.objects.filter(negocio_id=negocio_id).aggregate(
        total=Sum(
            F("cantidad_disponible") * F("producto__costo"),
            output_field=tipo_del_importe,
        )
    )["total"]
