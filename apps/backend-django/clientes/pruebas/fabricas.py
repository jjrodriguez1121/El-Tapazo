"""Datos de prueba de la app `clientes`."""

from datetime import date

import factory

from clientes.models import Cliente
from negocios.pruebas.fabricas import FabricaDeNegocio


class FabricaDeCliente(factory.django.DjangoModelFactory):
    """Una persona mayor de edad. Para una menor: `FabricaDeCliente(fecha_nacimiento=...)`."""

    class Meta:
        model = Cliente

    negocio = factory.SubFactory(FabricaDeNegocio)
    tipo_documento = Cliente.TipoDocumento.CEDULA
    numero_documento = factory.Sequence(lambda n: f"10{n:08d}")
    nombre = "Ana"
    apellido = "Pérez"
    fecha_nacimiento = date(1995, 6, 15)
    activo = True
