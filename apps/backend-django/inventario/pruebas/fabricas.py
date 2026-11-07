"""Datos de prueba de la app `inventario`."""

from decimal import Decimal

import factory

from catalogo.pruebas.fabricas import FabricaDeProducto
from inventario.models import Existencia, Ubicacion
from negocios.pruebas.fabricas import FabricaDeNegocio


class FabricaDeUbicacion(factory.django.DjangoModelFactory):
    class Meta:
        model = Ubicacion

    negocio = factory.SubFactory(FabricaDeNegocio)
    nombre = factory.Sequence(lambda n: f"Bodega {n}")
    tipo = Ubicacion.Tipo.BODEGA
    activa = True


class FabricaDeExistencia(factory.django.DjangoModelFactory):
    """Un saldo de un producto en una ubicación, los tres del mismo negocio."""

    class Meta:
        model = Existencia

    negocio = factory.SubFactory(FabricaDeNegocio)
    # `..negocio` sube al negocio de ESTA fábrica. Sin eso, cada SubFactory se
    # inventa el suyo y la fila queda repartida entre tres negocios distintos.
    producto = factory.SubFactory(FabricaDeProducto, negocio=factory.SelfAttribute("..negocio"))
    ubicacion = factory.SubFactory(FabricaDeUbicacion, negocio=factory.SelfAttribute("..negocio"))
    cantidad_disponible = Decimal("100.00")
    cantidad_minima = Decimal("0.00")
