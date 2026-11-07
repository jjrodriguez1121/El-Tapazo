"""Consultas al ORM sobre `eventos` y `ubicaciones` para la jornada."""

from datetime import datetime

from django.db.models import QuerySet

from eventos.models import Evento
from inventario.models import Ubicacion


def obtener_del_negocio(*, evento_id: int, negocio_id: int) -> Evento | None:
    return (
        Evento.objects.select_related("ubicacion")
        .filter(pk=evento_id, negocio_id=negocio_id)
        .first()
    )


def del_negocio(*, negocio_id: int) -> QuerySet[Evento]:
    return Evento.objects.filter(negocio_id=negocio_id)


def en_curso_en(*, ubicacion_id: int, negocio_id: int) -> Evento | None:
    """La jornada abierta de esa ubicación, si la hay.

    Como mucho puede haber una: lo garantiza el índice parcial
    `evento_una_sola_jornada_en_curso_por_ubicacion`.
    """
    return Evento.objects.filter(
        ubicacion_id=ubicacion_id, negocio_id=negocio_id, estado=Evento.Estado.EN_CURSO
    ).first()


def bloquear_ubicacion(*, ubicacion_id: int, negocio_id: int) -> Ubicacion | None:
    """Bloquea la ubicación hasta el final de la transacción.

    Es el recurso que se disputan dos peticiones que quieren abrir la jornada a
    la vez, y **nada más en el sistema lo bloquea**, así que no estorba a
    ninguna otra operación: la segunda petición espera y al entrar ya encuentra
    la jornada abierta.
    """
    return (
        Ubicacion.objects.select_for_update().filter(pk=ubicacion_id, negocio_id=negocio_id).first()
    )


def crear_jornada(
    *, negocio_id: int, ubicacion_id: int, nombre: str, fecha_inicio: datetime
) -> Evento:
    return Evento.objects.create(
        negocio_id=negocio_id,
        ubicacion_id=ubicacion_id,
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        estado=Evento.Estado.EN_CURSO,
    )
