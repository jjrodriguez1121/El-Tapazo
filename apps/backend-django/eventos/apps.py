from django.apps import AppConfig


class EventosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "eventos"
    verbose_name = "Eventos"

    def ready(self) -> None:
        # Registra cómo se documenta la autenticación del punto de control.
        from eventos.api import esquema  # noqa: F401
