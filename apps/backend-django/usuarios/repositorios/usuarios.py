"""Consultas al ORM sobre `usuarios`. Ningún otro sitio escribe `Usuario.objects`."""

from django.db.models import QuerySet
from django.utils import timezone

from usuarios.models import Usuario


def obtener_por_correo(*, correo: str) -> Usuario | None:
    """El usuario con ese correo, o `None`. El correo es único global."""
    return Usuario.objects.select_related("negocio").filter(correo=correo.lower()).first()


def obtener_por_id(*, usuario_id: int) -> Usuario | None:
    return Usuario.objects.select_related("negocio").filter(pk=usuario_id).first()


def existe_con_correo(*, correo: str) -> bool:
    return Usuario.objects.filter(correo=correo.lower()).exists()


def del_negocio(*, negocio_id: int) -> QuerySet[Usuario]:
    """Todos los usuarios de un negocio. Filtrar por negocio nunca es opcional."""
    return Usuario.objects.filter(negocio_id=negocio_id)


def crear_verificado(
    *,
    correo: str,
    contrasena: str,
    negocio_id: int,
    rol: str,
    datos_personales: dict,
) -> Usuario:
    """Crea el usuario con el correo ya verificado.

    Solo lo llama el servicio que acepta una invitación, y por eso nace
    verificado: para llegar hasta aquí la persona abrió el enlace que se
    mandó a ese correo, que es exactamente lo que la verificación comprueba.
    """
    return Usuario.objects.create_user(
        correo=correo,
        password=contrasena,
        negocio_id=negocio_id,
        rol=rol,
        correo_verificado_en=timezone.now(),
        **datos_personales,
    )
