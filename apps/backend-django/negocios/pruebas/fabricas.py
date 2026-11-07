"""Datos de prueba de la app `negocios`."""

import factory

from negocios.models import Negocio


class FabricaDeNegocio(factory.django.DjangoModelFactory):
    class Meta:
        model = Negocio

    nombre_comercial = factory.Sequence(lambda n: f"Bar El Tapaso {n}")
    nit = factory.Sequence(lambda n: f"9001234{n:03d}")
    estado = Negocio.Estado.ACTIVO
