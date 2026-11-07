"""Datos de prueba de la app `usuarios`."""

from datetime import timedelta

import factory
from django.utils import timezone

from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.models import Invitacion, Rol, Usuario
from usuarios.tokens import generar_token_de_invitacion

# Una sola contraseña para todas las pruebas: pasa los validadores de Django y
# se escribe una vez.
CONTRASENA = "Tapaso.2026.segura"


class FabricaDeUsuario(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario
        skip_postgeneration_save = True

    correo = factory.Sequence(lambda n: f"persona{n}@tapaso.test")
    nombre = "Ana"
    apellido = "Ríos"
    telefono = "3001112233"
    negocio = factory.SubFactory(FabricaDeNegocio)
    rol = Rol.MESERO
    activo = True
    correo_verificado_en = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def contrasena(self, crear: bool, valor: str | None, **kwargs) -> None:
        self.set_password(valor or CONTRASENA)
        if crear:
            self.save()


class FabricaDeAdministrador(FabricaDeUsuario):
    rol = Rol.ADMINISTRADOR


class FabricaDeStaffDePlataforma(FabricaDeUsuario):
    """Quien da de alta los negocios: existe por encima de todos y no tiene ninguno.

    Sin negocio y sin rol, que es lo que permite la restricción
    `usuario_requiere_negocio_y_rol` cuando `is_superuser` está puesto. Por eso
    ninguno de los permisos por rol le sirve: todos exigen `negocio_id`.
    """

    negocio = None
    rol = ""
    es_staff = True
    is_superuser = True


class FabricaDeInvitacion(factory.django.DjangoModelFactory):
    """Invitación pendiente. El token en claro queda en `token_en_claro`."""

    class Meta:
        model = Invitacion

    negocio = factory.SubFactory(FabricaDeNegocio)
    correo = factory.Sequence(lambda n: f"invitado{n}@tapaso.test")
    rol = Rol.MESERO
    creada_por = factory.SubFactory(FabricaDeAdministrador)
    expira_en = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))

    @classmethod
    def _create(cls, modelo, *args, **kwargs):
        token, kwargs["hash_token"] = generar_token_de_invitacion()
        invitacion = super()._create(modelo, *args, **kwargs)
        invitacion.token_en_claro = token
        return invitacion
