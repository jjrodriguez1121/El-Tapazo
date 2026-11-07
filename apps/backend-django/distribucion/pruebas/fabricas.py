"""Datos de prueba de la app `distribucion`."""

from decimal import Decimal

import factory
from django.utils import timezone

from distribucion.models import ClienteDistribucion, PagoDistribucion, PedidoDistribucion
from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.pruebas.fabricas import FabricaDeAdministrador


class FabricaDeClienteDistribucion(factory.django.DjangoModelFactory):
    class Meta:
        model = ClienteDistribucion

    negocio = factory.SubFactory(FabricaDeNegocio)
    razon_social = factory.Sequence(lambda n: f"Tienda La Esquina {n}")
    nit = factory.Sequence(lambda n: f"9007654{n:03d}")
    dias_credito = 30
    activo = True


class FabricaDePedidoDistribucion(factory.django.DjangoModelFactory):
    class Meta:
        model = PedidoDistribucion

    negocio = factory.SubFactory(FabricaDeNegocio)
    cliente_distribucion = factory.SubFactory(
        FabricaDeClienteDistribucion, negocio=factory.SelfAttribute("..negocio")
    )
    usuario = factory.SubFactory(FabricaDeAdministrador, negocio=factory.SelfAttribute("..negocio"))
    estado = PedidoDistribucion.Estado.PENDIENTE
    fecha_pedido = factory.LazyFunction(timezone.now)


class FabricaDePagoDistribucion(factory.django.DjangoModelFactory):
    class Meta:
        model = PagoDistribucion

    negocio = factory.SubFactory(FabricaDeNegocio)
    pedido_distribucion = factory.SubFactory(
        FabricaDePedidoDistribucion, negocio=factory.SelfAttribute("..negocio")
    )
    recibido_por = factory.SubFactory(
        FabricaDeAdministrador, negocio=factory.SelfAttribute("..negocio")
    )
    monto = Decimal("50000.00")
    fecha = factory.LazyFunction(timezone.now)
