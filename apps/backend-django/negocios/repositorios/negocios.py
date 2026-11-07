"""Consultas al ORM sobre `negocios`.

Es el único repositorio del proyecto que **no filtra por negocio**, y no es un
olvido: aquí el negocio es la fila, no el dueño de la fila. Quien llega hasta
estas consultas es el staff de la plataforma, que está por encima de todos.
"""

from django.db.models import QuerySet

from negocios.models import Negocio


def obtener(*, negocio_id: int) -> Negocio | None:
    return Negocio.objects.filter(pk=negocio_id).first()


def todos() -> QuerySet[Negocio]:
    return Negocio.objects.all()


def existe_nit(*, nit: str, excluyendo_id: int | None = None) -> bool:
    consulta = Negocio.objects.filter(nit=nit)
    if excluyendo_id is not None:
        consulta = consulta.exclude(pk=excluyendo_id)
    return consulta.exists()


def crear(*, nombre_comercial: str, nit: str) -> Negocio:
    return Negocio.objects.create(nombre_comercial=nombre_comercial, nit=nit)
