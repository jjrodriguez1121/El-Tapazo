"""Datos de prueba de la app `catalogo`.

Ojo con el `SelfAttribute("..negocio")`: sin él, cada `SubFactory` se inventaría
su propio negocio y un producto acabaría con la categoría del negocio 1 y su
`negocio_id` del 2. Las pruebas de aislamiento pasarían por la razón
equivocada — porque nada coincide nunca, no porque el filtro funcione.
"""

from decimal import Decimal

import factory

from catalogo.models import Categoria, Producto, Proveedor
from negocios.pruebas.fabricas import FabricaDeNegocio


class FabricaDeCategoria(factory.django.DjangoModelFactory):
    class Meta:
        model = Categoria

    negocio = factory.SubFactory(FabricaDeNegocio)
    nombre = factory.Sequence(lambda n: f"Cervezas {n}")
    activa = True


class FabricaDeProveedor(factory.django.DjangoModelFactory):
    class Meta:
        model = Proveedor

    negocio = factory.SubFactory(FabricaDeNegocio)
    razon_social = factory.Sequence(lambda n: f"Distribuidora {n} S.A.S.")
    nit = factory.Sequence(lambda n: f"8001234{n:03d}")
    activo = True


class FabricaDeProducto(factory.django.DjangoModelFactory):
    class Meta:
        model = Producto

    negocio = factory.SubFactory(FabricaDeNegocio)
    categoria = factory.SubFactory(FabricaDeCategoria, negocio=factory.SelfAttribute("..negocio"))
    sku = factory.Sequence(lambda n: f"CER-{n:04d}")
    nombre = factory.Sequence(lambda n: f"Cerveza {n}")
    costo = Decimal("2000.00")
    precio_evento = Decimal("5000.00")
    precio_mayorista = Decimal("3500.00")
    activo = True
