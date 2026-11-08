"""Crea el negocio El Tapaso y su administrador inicial de desarrollo."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalogo.models import Impuesto
from negocios.models import Negocio
from usuarios.models import Rol, Usuario
from ventas.models import MetodoPago

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
        for nombre in ("Efectivo", "Transferencia", "Tarjeta", "Nequi", "Daviplata"):
            MetodoPago.objects.get_or_create(
                negocio=negocio,
                nombre=nombre,
                defaults={"estado": True},
            )
        for nombre, porcentaje, tratamiento in (
            ("IVA 19 %", 19, Impuesto.TipoTratamiento.GRAVADO),
            ("IVA 5 %", 5, Impuesto.TipoTratamiento.GRAVADO),
            ("IVA 0 %", 0, Impuesto.TipoTratamiento.EXENTO),
            ("Exento", 0, Impuesto.TipoTratamiento.EXENTO),
            ("No gravado", 0, Impuesto.TipoTratamiento.NO_GRAVADO),
        ):
            Impuesto.objects.get_or_create(
                negocio=negocio,
                nombre=nombre,
                defaults={
                    "porcentaje": porcentaje,
                    "tipo_tratamiento": tratamiento,
                    "activo": True,
                },
            )

        if Usuario.objects.filter(correo=CORREO_ADMINISTRADOR).exists():
            self.stdout.write(
                "Datos iniciales: el negocio y el administrador ya existen."
            )
            return

        Usuario.objects.create_user(
            correo=CORREO_ADMINISTRADOR,
            password=CONTRASENA_ADMINISTRADOR,
            nombre="Administrador",
            apellido="El Tapaso",
            negocio=negocio,
            rol=Rol.ADMINISTRADOR,
            correo_verificado_en=timezone.now(),
        )
        creado = "el negocio y su administrador" if negocio_creado else "el administrador"
        self.stdout.write(
            self.style.SUCCESS(
                f"Datos iniciales: se creó {creado} "
                f"({CORREO_ADMINISTRADOR} / {CONTRASENA_ADMINISTRADOR})."
            )
        )
