"""Consultas al ORM sobre `invitaciones`."""

from datetime import datetime

from django.db.models import QuerySet

from usuarios.models import Invitacion


def obtener_por_hash(*, hash_token: str) -> Invitacion | None:
    return (
        Invitacion.objects.select_related("negocio", "creada_por")
        .filter(hash_token=hash_token)
        .first()
    )


def obtener_del_negocio(*, invitacion_id: int, negocio_id: int) -> Invitacion | None:
    """Una invitación, siempre acotada al negocio de quien pregunta.

    Filtrar también por `negocio_id` es lo que evita que un administrador
    toque las invitaciones de otro negocio cambiando el id de la URL.
    """
    return Invitacion.objects.filter(pk=invitacion_id, negocio_id=negocio_id).first()


def del_negocio(*, negocio_id: int) -> QuerySet[Invitacion]:
    return Invitacion.objects.filter(negocio_id=negocio_id)


def hay_pendiente(*, negocio_id: int, correo: str) -> bool:
    return Invitacion.objects.filter(
        negocio_id=negocio_id, correo=correo.lower(), aceptada_en__isnull=True
    ).exists()


def crear(
    *,
    negocio_id: int,
    correo: str,
    rol: str,
    hash_token: str,
    creada_por_id: int,
    expira_en: datetime,
) -> Invitacion:
    return Invitacion.objects.create(
        negocio_id=negocio_id,
        correo=correo.lower(),
        rol=rol,
        hash_token=hash_token,
        creada_por_id=creada_por_id,
        expira_en=expira_en,
    )
