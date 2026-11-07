"""Datos de prueba de la app `eventos`."""

from decimal import Decimal

import factory
from django.utils import timezone

from catalogo.pruebas.fabricas import FabricaDeProducto
from clientes.pruebas.fabricas import FabricaDeCliente
from eventos.models import (
    ClienteEvento,
    DetallePedidoEvento,
    DispositivoNfc,
    Evento,
    GrupoEvento,
    PedidoEvento,
    PulseraNfc,
)
from inventario.pruebas.fabricas import FabricaDeUbicacion
from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.pruebas.fabricas import FabricaDeUsuario
from usuarios.tokens import generar_token_de_invitacion


class FabricaDeEvento(factory.django.DjangoModelFactory):
    """Una jornada planeada. Para una en curso: `FabricaDeEvento(estado=...)`."""

    class Meta:
        model = Evento

    negocio = factory.SubFactory(FabricaDeNegocio)
    ubicacion = factory.SubFactory(FabricaDeUbicacion, negocio=factory.SelfAttribute("..negocio"))
    nombre = factory.Sequence(lambda n: f"Jornada de prueba {n}")
    fecha_inicio = factory.LazyFunction(timezone.now)
    estado = Evento.Estado.PLANEADO


class FabricaDePulsera(factory.django.DjangoModelFactory):
    class Meta:
        model = PulseraNfc

    negocio = factory.SubFactory(FabricaDeNegocio)
    uid_tag = factory.Sequence(lambda n: f"04A2B3C4D5E6{n:02X}")
    estado = PulseraNfc.Estado.DISPONIBLE


class FabricaDeDispositivoNfc(factory.django.DjangoModelFactory):
    """Un lector de puerta. El token en claro queda en `token_en_claro`."""

    class Meta:
        model = DispositivoNfc

    negocio = factory.SubFactory(FabricaDeNegocio)
    nombre = factory.Sequence(lambda n: f"Puerta {n}")
    activo = True

    @classmethod
    def _create(cls, modelo, *args, **kwargs):
        # Solo se genera si la prueba no trae uno suyo: si se pisara siempre,
        # no habría forma de provocar el choque de tokens repetidos.
        token = None
        if "hash_token" not in kwargs:
            token, kwargs["hash_token"] = generar_token_de_invitacion()
        dispositivo = super()._create(modelo, *args, **kwargs)
        dispositivo.token_en_claro = token
        return dispositivo


class FabricaDeGrupo(factory.django.DjangoModelFactory):
    """La mesa, la mancha: el grupo que llegó junto."""

    class Meta:
        model = GrupoEvento

    negocio = factory.SubFactory(FabricaDeNegocio)
    evento = factory.SubFactory(FabricaDeEvento, negocio=factory.SelfAttribute("..negocio"))
    mesa_zona = factory.Sequence(lambda n: f"Mesa {n}")
    estado = GrupoEvento.Estado.ABIERTO
    abierto_por = factory.SubFactory(FabricaDeUsuario, negocio=factory.SelfAttribute("..negocio"))


class FabricaDeCuenta(factory.django.DjangoModelFactory):
    """La cuenta de una persona durante un evento. Sin pulsera por defecto."""

    class Meta:
        model = ClienteEvento

    negocio = factory.SubFactory(FabricaDeNegocio)
    grupo_evento = factory.SubFactory(FabricaDeGrupo, negocio=factory.SelfAttribute("..negocio"))
    cliente = factory.SubFactory(FabricaDeCliente, negocio=factory.SelfAttribute("..negocio"))
    asignada_por = factory.SubFactory(FabricaDeUsuario, negocio=factory.SelfAttribute("..negocio"))


class FabricaDePedidoEvento(factory.django.DjangoModelFactory):
    """Una comanda. Sin `cliente_evento` sería venta de mostrador."""

    class Meta:
        model = PedidoEvento

    negocio = factory.SubFactory(FabricaDeNegocio)
    evento = factory.SubFactory(FabricaDeEvento, negocio=factory.SelfAttribute("..negocio"))
    cliente_evento = factory.SubFactory(FabricaDeCuenta, negocio=factory.SelfAttribute("..negocio"))
    mesero = factory.SubFactory(FabricaDeUsuario, negocio=factory.SelfAttribute("..negocio"))
    estado = PedidoEvento.Estado.PENDIENTE


class FabricaDeDetallePedidoEvento(factory.django.DjangoModelFactory):
    """Una línea de comanda, con el precio ya congelado."""

    class Meta:
        model = DetallePedidoEvento

    negocio = factory.SubFactory(FabricaDeNegocio)
    pedido_evento = factory.SubFactory(
        FabricaDePedidoEvento, negocio=factory.SelfAttribute("..negocio")
    )
    producto = factory.SubFactory(FabricaDeProducto, negocio=factory.SelfAttribute("..negocio"))
    cantidad = Decimal("1.00")
    precio_unitario = Decimal("5000.00")
