"""Invita al primer administrador de un negocio.

Es el huevo y la gallina del modelo: un negocio nuevo no tiene todavía ningún
administrador que pueda invitar a nadie. Lo resuelve el staff de la plataforma
desde la terminal, que es quien da de alta los negocios.

    ./dev.sh manage invitar_administrador --negocio 1 --correo ana@bar.com

A partir de ahí, ese administrador invita a su equipo desde la aplicación.
"""

from django.core.management.base import BaseCommand, CommandError

from negocios.excepciones import NegocioNoEncontrado
from nucleo.excepciones import ErrorDeNegocio
from usuarios.models import Rol, Usuario
from usuarios.servicios import invitaciones as servicio


class Command(BaseCommand):
    help = "Invita al primer administrador de un negocio (staff de la plataforma)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--negocio",
            type=int,
            required=True,
            help="Id numérico del negocio: el que aparece en su URL del admin de Django.",
        )
        parser.add_argument("--correo", required=True, help="Correo del administrador.")
        parser.add_argument(
            "--invita",
            help="Correo del staff que invita. Por defecto, el primer superusuario.",
        )
        parser.add_argument(
            "--mostrar-enlace",
            action="store_true",
            help="Imprime el enlace en pantalla, por si el correo no salió.",
        )

    def handle(self, *args, **opciones) -> None:
        staff = self._obtener_staff(opciones["invita"])
        try:
            invitacion = servicio.crear_invitacion(
                negocio_id=opciones["negocio"],
                correo=opciones["correo"],
                rol=Rol.ADMINISTRADOR,
                invitada_por_id=staff.pk,
            )
        except NegocioNoEncontrado as exc:
            raise CommandError(
                f"No hay ningún negocio con el id {opciones['negocio']}. Créalo en el admin "
                "de Django (Negocios › Añadir) y usa el número que aparece en su URL."
            ) from exc
        except ErrorDeNegocio as exc:
            raise CommandError(exc.mensaje) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Invitación enviada a {invitacion.correo} "
                f"para {invitacion.negocio.nombre_comercial}. "
                f"Vence el {invitacion.expira_en:%d/%m/%Y}."
            )
        )
        if opciones["mostrar_enlace"]:
            self.stdout.write(
                "El enlace se imprimió en el correo. Si usas el backend de consola, "
                "búscalo en los logs del backend: ./dev.sh logs backend"
            )

    def _obtener_staff(self, correo: str | None) -> Usuario:
        consulta = Usuario.objects.filter(is_superuser=True)
        staff = consulta.filter(correo=correo).first() if correo else consulta.first()
        if staff is None:
            raise CommandError("No hay staff de plataforma. Créalo con: ./dev.sh superuser")
        return staff
