"""Deja la base de desarrollo lista para entrar: un negocio y su administrador.

Lo corre el entrypoint del contenedor después de `migrate`, así que tras
levantar el proyecto por primera vez —o tras borrar la base— siempre hay con
qué iniciar sesión:

    negocio:     El Tapaso
    correo:      admin@gmail.com
    contraseña:  admin123

Se puede correr cuantas veces se quiera: si el negocio o el usuario ya existen
no los toca, ni siquiera la contraseña. Solo funciona con DEBUG activo: esa
contraseña no puede llegar nunca a producción.

    ./dev.sh manage crear_datos_iniciales
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from negocios.models import Negocio
from usuarios.models import Rol, Usuario

NOMBRE_NEGOCIO = "El Tapaso"
NIT_NEGOCIO = "900000000-0"
CORREO_ADMINISTRADOR = "admin@gmail.com"
CONTRASENA_ADMINISTRADOR = "admin123"


class Command(BaseCommand):
    help = "Crea el negocio El Tapaso y su administrador de desarrollo si no existen."

    @transaction.atomic
    def handle(self, *args, **opciones) -> None:
        if not settings.DEBUG:
            raise CommandError(
                "Solo se crean datos iniciales con DEBUG activo: la contraseña es de desarrollo."
            )

        negocio, negocio_creado = Negocio.objects.get_or_create(
            nit=NIT_NEGOCIO,
            defaults={"nombre_comercial": NOMBRE_NEGOCIO},
        )
        if Usuario.objects.filter(correo=CORREO_ADMINISTRADOR).exists():
            self.stdout.write("Datos iniciales: ya existían, no se tocó nada.")
            return

        Usuario.objects.create_user(
            correo=CORREO_ADMINISTRADOR,
            password=CONTRASENA_ADMINISTRADOR,
            nombre="Administrador",
            apellido="El Tapaso",
            negocio=negocio,
            rol=Rol.ADMINISTRADOR,
            # Nadie va a abrir un enlace de verificación en admin@gmail.com.
            correo_verificado_en=timezone.now(),
        )
        creado = "el negocio y su administrador" if negocio_creado else "el administrador"
        self.stdout.write(
            self.style.SUCCESS(
                f"Datos iniciales: se creó {creado} "
                f"({CORREO_ADMINISTRADOR} / {CONTRASENA_ADMINISTRADOR})."
            )
        )
