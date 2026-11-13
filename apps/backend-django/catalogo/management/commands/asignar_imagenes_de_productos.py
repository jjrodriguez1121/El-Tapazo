"""Busca en la web una foto para cada producto del catálogo y la guarda.

    ./dev.sh manage asignar_imagenes_de_productos                 # solo los que no tienen foto
    ./dev.sh manage asignar_imagenes_de_productos --reemplazar    # todos
    ./dev.sh manage asignar_imagenes_de_productos --negocio 2 --limite 20

Port de `assign_product_images` de GearShift. Se puede cortar y volver a
correr: sin `--reemplazar` sigue con los que aún no tienen foto. Si el buscador
limita las consultas, espera y reintenta el mismo producto.
"""

import time

from django.core.management.base import BaseCommand

from catalogo.models import Producto
from catalogo.servicios.imagenes_web import BuscadorLimitado, BuscadorNoDisponible, foto_de_producto

REINTENTOS_SI_LIMITA = 3
ESPERA_SI_LIMITA = 20


def asignar_foto(producto: Producto, *, espera=time.sleep) -> str:
    """Busca y guarda la foto de un producto. Devuelve `con_foto`, `sin_resultados` o `fallo`."""
    for intento in range(REINTENTOS_SI_LIMITA + 1):
        try:
            imagen = foto_de_producto(producto.nombre)
        except BuscadorLimitado:
            if intento < REINTENTOS_SI_LIMITA:
                espera(ESPERA_SI_LIMITA)
                continue
            return "fallo"
        except BuscadorNoDisponible:
            return "fallo"
        if imagen is None:
            return "sin_resultados"
        Producto.objects.filter(id=producto.id).update(imagen=imagen)
        return "con_foto"
    return "fallo"


class Command(BaseCommand):
    help = "Busca en la web (Bing vía ddgs) una foto para cada producto y la guarda."

    def add_arguments(self, parser):
        parser.add_argument(
            "--negocio", type=int, default=None, help="Id del negocio. Sin él, todos."
        )
        parser.add_argument("--limite", type=int, default=None, help="Máximo de productos.")
        parser.add_argument(
            "--reemplazar", action="store_true", help="También los que ya tienen foto."
        )

    def handle(self, *args, **opciones):
        productos = Producto.objects.order_by("id")
        if opciones["negocio"]:
            productos = productos.filter(negocio_id=opciones["negocio"])
        if not opciones["reemplazar"]:
            productos = productos.filter(imagen="")
        if opciones["limite"]:
            productos = productos[: opciones["limite"]]

        textos = {"con_foto": "con foto", "sin_resultados": "sin resultados",
                  "fallo": "el buscador no respondió"}  # fmt: skip
        cuenta = dict.fromkeys(textos, 0)
        for numero, producto in enumerate(productos, 1):
            resultado = asignar_foto(producto)
            cuenta[resultado] += 1
            self.stdout.write(f"{numero}. {producto.nombre}: {textos[resultado]}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Fotos: {cuenta['con_foto']} guardadas, {cuenta['sin_resultados']} sin "
                f"resultados, {cuenta['fallo']} sin respuesta del buscador."
            )
        )
