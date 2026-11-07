"""Deja la base de desarrollo lista para entrar con su catálogo de ejemplo.

Lo corre el entrypoint del contenedor después de `migrate`, así que tras
levantar el proyecto por primera vez —o tras borrar la base— siempre hay con
qué iniciar sesión:

    negocio:     El Tapaso
    correo:      admin@gmail.com
    contraseña:  admin123

Se puede correr cuantas veces se quiera: si el negocio o el usuario ya existen
no los toca, ni siquiera la contraseña. Solo funciona con DEBUG activo: esa
contraseña no puede llegar nunca a producción.

    ./dev.sh manage crear_datos_iniciales
"""

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalogo.models import Categoria, Producto
from inventario.models import Existencia
from negocios.models import Negocio
from usuarios.models import Rol, Usuario

NOMBRE_NEGOCIO = "El Tapaso"
NIT_NEGOCIO = "900000000-0"
CORREO_ADMINISTRADOR = "admin@gmail.com"
CONTRASENA_ADMINISTRADOR = "admin123"

CATEGORIA_DATOS = [
    ("Cervezas", ["Águila", "Águila Light", "Águila Cero", "Club Colombia Dorada", "Club Colombia Roja", "Club Colombia Negra", "Poker", "Costeña", "Costeñita", "Andina", "Andina Light", "3 Cordilleras", "BBC"], 4500, "CER"),
    ("Gaseosas", ["Colombiana", "Manzana Postobón", "Uva Postobón", "Naranja Postobón", "Pepsi", "Pepsi Zero", "Coca-Cola", "Coca-Cola Zero", "Sprite", "Quatro", "Kola Roman", "Bretaña"], 2500, "GAS"),
    ("Energizantes", ["Vive 100", "Vive 100 Zero", "Speed Max", "Volt", "Peak", "Amper"], 6500, "ENE"),
    ("Aguas", ["Agua Cristal", "Agua Cristal con Gas", "Agua Brisa", "Agua Brisa con Gas", "Agua Manantial", "Agua Hatsu"], 2000, "AGU"),
    ("Aguardientes", ["Aguardiente Antioqueño", "Aguardiente Antioqueño Sin Azúcar", "Aguardiente Amarillo de Manzanares", "Aguardiente Néctar", "Aguardiente Néctar Club Verde", "Aguardiente Cristal", "Aguardiente Tapa Roja"], 28000, "AGR"),
    ("Ron", ["Ron Medellín Añejo", "Ron Medellín Extra Añejo", "Ron Viejo de Caldas", "Ron Viejo de Caldas Carta de Oro", "Ron Viejo de Caldas Tradicional", "Ron Caldas"], 26000, "RON"),
]


class Command(BaseCommand):
    help = "Crea el negocio El Tapaso y su administrador de desarrollo si no existen."

    @transaction.atomic
    def handle(self, *args, **opciones) -> None:
        if not settings.DEBUG:
            raise CommandError(
                "Solo se crean datos iniciales con DEBUG activo: la contraseña es de desarrollo."
            )

        negocio, negocio_creado = Negocio.objects.get_or_create(
            nit=NIT_NEGOCIO,
            defaults={"nombre_comercial": NOMBRE_NEGOCIO},
        )

        productos_creados = 0
        for nombre_categoria, nombres_productos, precio_base, prefijo_sku in CATEGORIA_DATOS:
            categoria, _ = Categoria.objects.get_or_create(
                negocio=negocio,
                nombre=nombre_categoria,
                defaults={"activa": True},
            )
            for indice, nombre_producto in enumerate(nombres_productos, start=1):
                _, creado = Producto.objects.get_or_create(
                    negocio=negocio,
                    sku=f"{prefijo_sku}-{indice:03d}",
                    defaults={
                        "nombre": nombre_producto,
                        "categoria": categoria,
                        "costo": Decimal(str(precio_base)) * Decimal("0.70"),
                        "precio_venta": Decimal(precio_base + (indice - 1) * 500),
                        "activo": True,
                    },
                )
                productos_creados += int(creado)
                producto = Producto.objects.get(
                    negocio=negocio,
                    sku=f"{prefijo_sku}-{indice:03d}",
                )
                Existencia.objects.get_or_create(
                    negocio=negocio,
                    producto=producto,
                    defaults={
                        "cantidad_disponible": [18, 4, 0, 32, 8, 15, 2, 25][
                            (indice - 1) % 8
                        ],
                        "cantidad_minima": 5,
                    },
                )

        if Usuario.objects.filter(correo=CORREO_ADMINISTRADOR).exists():
            self.stdout.write(
                "Datos iniciales: ya existían; catálogo revisado "
                f"({productos_creados} productos creados)."
            )
            return

        Usuario.objects.create_user(
            correo=CORREO_ADMINISTRADOR,
            password=CONTRASENA_ADMINISTRADOR,
            nombre="Administrador",
            apellido="El Tapaso",
            negocio=negocio,
            rol=Rol.ADMINISTRADOR,
            # Nadie va a abrir un enlace de verificación en admin@gmail.com.
            correo_verificado_en=timezone.now(),
        )
        creado = "el negocio y su administrador" if negocio_creado else "el administrador"
        self.stdout.write(
            self.style.SUCCESS(
                f"Datos iniciales: se creó {creado} "
                f"({CORREO_ADMINISTRADOR} / {CONTRASENA_ADMINISTRADOR})."
            )
        )
