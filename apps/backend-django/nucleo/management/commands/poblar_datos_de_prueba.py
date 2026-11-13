"""Llena un negocio con datos de prueba en todos los módulos.

    ./dev.sh manage poblar_datos_de_prueba
    ./dev.sh manage poblar_datos_de_prueba --correo otro@admin.com --minimo 150

Crea, como mínimo `--minimo` (100) registros de cada módulo del menú:
categorías, proveedores, productos (con imagen), clientes, compras de contado,
compras a crédito (cuentas por pagar), ventas de contado, ventas a crédito
(cuentas por cobrar) y PQRs. Además abona parte de la cartera y deja una
factura de proveedor en PDF para probar el buscador de coincidencias.

Todo pasa por la **misma API** que usa el frontend (con `APIClient`), así que
el stock, el kardex, los totales y la cartera quedan como si alguien los
hubiera registrado a mano. Después se reparten las fechas en los últimos
meses para que el tablero tenga historia.

Solo corre con DEBUG activo y en un negocio sin categorías: no se mezcla con
datos reales. Todo va en una transacción: si algo falla no queda nada a medias.
"""

import base64
import io
import random
import unicodedata
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
from rest_framework.test import APIClient

from catalogo.models import Categoria, Impuesto, Producto, Proveedor
from clientes.models import Cliente
from compras.models import Compra, CuentaPorPagar, DetalleCompra, PagoCompra
from inventario.models import Existencia, MovimientoInventario
from pqrs.models import Pqr, PqrSeguimiento
from usuarios.models import Usuario
from ventas.models import CuentaPorCobrar, DetalleVenta, MetodoPago, PagoVenta, Venta

API = "/api/v1"
DIAS_DE_HISTORIA = 120
RUTA_FACTURA = Path(settings.MEDIA_ROOT) / "pruebas" / "factura-proveedor-prueba.pdf"

# --------------------------------------------------------------------------- #
# Catálogo de una licorera / bar colombiano
# --------------------------------------------------------------------------- #
# familia: (prefijo SKU, color RGB, forma de la imagen, subcategorías, productos)
# Cada producto: (nombre, costo, tarifa de IVA)
FAMILIAS = {
    "Cervezas": ("CER", (214, 158, 46), "lata", [
        "Cervezas nacionales", "Cervezas importadas", "Cervezas artesanales",
        "Cervezas en lata", "Cervezas sin alcohol",
    ], [
        ("Cerveza Águila Lata 330ml", 2100, 19), ("Cerveza Águila Light Lata 330ml", 2150, 19),
        ("Cerveza Poker Lata 330ml", 2050, 19), ("Cerveza Club Colombia Dorada 330ml", 2600, 19),
        ("Cerveza Club Colombia Roja 330ml", 2600, 19), ("Cerveza Costeña Botella 350ml", 1900, 19),
        ("Cerveza Corona Botella 355ml", 3900, 19), ("Cerveza Heineken Lata 330ml", 3300, 19),
        ("Cerveza Stella Artois Botella 330ml", 4200, 19), ("Cerveza BBC Cajicá Miel 330ml", 5200, 19),
        ("Cerveza Pilsen Botella 330ml", 2000, 19), ("Cerveza Budweiser Lata 330ml", 2700, 19),
    ]),
    "Aguardientes": ("AGU", (46, 125, 50), "botella", [
        "Aguardiente antioqueño", "Aguardiente sin azúcar", "Aguardiente caucano",
        "Aguardiente en media", "Aguardiente en garrafa",
    ], [
        ("Aguardiente Antioqueño Tapa Azul 750ml", 38000, 5),
        ("Aguardiente Antioqueño Tapa Roja 750ml", 36000, 5),
        ("Aguardiente Antioqueño Media 375ml", 20000, 5),
        ("Aguardiente Néctar Club 750ml", 33000, 5),
        ("Aguardiente Amarillo de Manzanares 750ml", 39000, 5),
        ("Aguardiente Antioqueño Garrafa 2000ml", 92000, 5),
        ("Aguardiente Blanco del Valle 750ml", 34000, 5),
        ("Aguardiente Caucano 750ml", 31000, 5),
    ]),
    "Rones": ("RON", (121, 85, 72), "botella", [
        "Ron añejo", "Ron blanco", "Ron de 8 años", "Ron importado", "Ron en media",
    ], [
        ("Ron Medellín Añejo 3 Años 750ml", 41000, 5), ("Ron Medellín 8 Años 750ml", 62000, 5),
        ("Ron Viejo de Caldas 750ml", 40000, 5), ("Ron Viejo de Caldas Media 375ml", 22000, 5),
        ("Ron Bacardí Blanco 750ml", 48000, 5), ("Ron Havana Club 3 Años 700ml", 56000, 5),
        ("Ron Santa Fe 750ml", 35000, 5), ("Ron Zacapa 23 Años 750ml", 245000, 5),
    ]),
    "Whiskys": ("WHI", (161, 98, 7), "botella", [
        "Whisky escocés", "Whisky bourbon", "Whisky premium", "Whisky blended", "Whisky en media",
    ], [
        ("Whisky Old Parr 12 Años 750ml", 125000, 5), ("Whisky Buchanan's 12 Años 750ml", 135000, 5),
        ("Whisky Johnnie Walker Red Label 700ml", 78000, 5),
        ("Whisky Johnnie Walker Black Label 750ml", 140000, 5),
        ("Whisky Jack Daniel's 750ml", 115000, 5), ("Whisky Chivas Regal 12 Años 700ml", 130000, 5),
        ("Whisky Grant's 750ml", 62000, 5), ("Whisky Something Special 750ml", 68000, 5),
    ]),
    "Vinos": ("VIN", (136, 14, 79), "botella", [
        "Vino tinto", "Vino blanco", "Vino rosado", "Vino espumoso", "Sangría",
    ], [
        ("Vino Gato Negro Cabernet 750ml", 26000, 19), ("Vino Casillero del Diablo Merlot 750ml", 52000, 19),
        ("Vino Santa Rita 120 Blanco 750ml", 31000, 19), ("Vino Frontera Rosé 750ml", 24000, 19),
        ("Vino Espumoso Freixenet 750ml", 58000, 19), ("Sangría Don Simón 1000ml", 18000, 19),
    ]),
    "Tequilas y vodkas": ("TEQ", (0, 121, 107), "botella", [
        "Tequila", "Vodka", "Ginebra", "Mezcal", "Licores de crema",
    ], [
        ("Tequila José Cuervo Especial 750ml", 85000, 5), ("Tequila Olmeca Blanco 750ml", 72000, 5),
        ("Vodka Absolut 750ml", 76000, 5), ("Vodka Smirnoff 700ml", 52000, 5),
        ("Ginebra Gordon's 750ml", 64000, 5), ("Crema de Whisky Baileys 750ml", 82000, 5),
    ]),
    "Gaseosas": ("GAS", (198, 40, 40), "botella", [
        "Gaseosas cola", "Gaseosas de sabores", "Gaseosas personales", "Gaseosas familiares",
        "Gaseosas sin azúcar",
    ], [
        ("Gaseosa Coca Cola 400ml", 1800, 19), ("Gaseosa Coca Cola 1500ml", 4200, 19),
        ("Gaseosa Coca Cola Sin Azúcar 400ml", 1800, 19), ("Gaseosa Postobón Manzana 400ml", 1500, 19),
        ("Gaseosa Colombiana 400ml", 1500, 19), ("Gaseosa Sprite 400ml", 1700, 19),
        ("Gaseosa Pepsi 400ml", 1500, 19), ("Ginger Canada Dry 400ml", 1900, 19),
    ]),
    "Aguas": ("AGA", (2, 136, 209), "botella", [
        "Agua sin gas", "Agua con gas", "Agua saborizada", "Agua en bolsa", "Agua en garrafa",
    ], [
        ("Agua Cristal 600ml", 1100, 0), ("Agua Brisa con Gas 600ml", 1300, 0),
        ("Agua Manantial 600ml", 1400, 0), ("Agua Cristal Bolsa 900ml", 700, 0),
        ("Agua Brisa Limón 600ml", 1500, 0), ("Agua Cristal Garrafa 5000ml", 6500, 0),
    ]),
    "Jugos y maltas": ("JUG", (245, 124, 0), "caja", [
        "Jugos en caja", "Jugos en botella", "Maltas", "Tés fríos", "Bebidas lácteas",
    ], [
        ("Jugo Hit Mango 500ml", 1900, 19), ("Jugo Del Valle Naranja 400ml", 2100, 19),
        ("Malta Leona 330ml", 1700, 19), ("Pony Malta 330ml", 1800, 19),
        ("Té Mr Tea Limón 500ml", 1900, 19), ("Avena Alpina 250ml", 2000, 19),
    ]),
    "Energizantes": ("ENE", (69, 39, 160), "lata", [
        "Energizantes", "Hidratantes", "Bebidas isotónicas", "Energizantes sin azúcar", "Shots",
    ], [
        ("Energizante Red Bull 250ml", 4800, 19), ("Energizante Monster 473ml", 5200, 19),
        ("Energizante Vive 100 380ml", 1900, 19), ("Hidratante Gatorade Mandarina 500ml", 2900, 19),
        ("Hidratante Powerade Frutas 500ml", 2700, 19), ("Energizante Speed Max 250ml", 1500, 19),
    ]),
    "Snacks": ("SNK", (251, 192, 45), "paquete", [
        "Papas fritas", "Maní y nueces", "Chicharrones", "Galletas", "Dulces",
    ], [
        ("Papas Margarita Natural 39g", 1700, 19), ("Papas Margarita Limón 39g", 1700, 19),
        ("Doritos Mega Queso 45g", 1900, 19), ("Maní La Especial Salado 50g", 1600, 19),
        ("Chicharrón Natuchips 30g", 1500, 19), ("De Todito BBQ 45g", 2100, 19),
        ("Galletas Festival Fresa 4 Unidades", 900, 19), ("Chocolatina Jet 12g", 600, 19),
        ("Bon Bon Bum Fresa", 300, 19), ("Trident Menta 5 Unidades", 700, 19),
    ]),
    "Cigarrillos": ("CIG", (97, 97, 97), "caja", [
        "Cigarrillos rubios", "Cigarrillos mentolados", "Cigarrillos por unidad",
        "Encendedores", "Tabacos",
    ], [
        ("Cigarrillos Marlboro Rojo 20 Unidades", 9800, 0),
        ("Cigarrillos Lucky Strike 20 Unidades", 9000, 0),
        ("Cigarrillos Belmont 20 Unidades", 8200, 0), ("Encendedor Bic Maxi", 2800, 19),
        ("Cigarrillos Marlboro Ice 20 Unidades", 10200, 0),
    ]),
    "Hielo y desechables": ("HIE", (77, 182, 172), "paquete", [
        "Hielo", "Vasos desechables", "Pitillos", "Servilletas", "Bolsas",
    ], [
        ("Bolsa de Hielo 2kg", 2200, 0), ("Bolsa de Hielo 5kg", 4000, 0),
        ("Vasos Desechables 7oz x50", 4800, 19), ("Pitillos Flexibles x100", 3500, 19),
        ("Servilletas Familia x100", 2600, 19),
    ]),
    "Mezcladores": ("MEZ", (233, 30, 99), "botella", [
        "Soda", "Tónica", "Granadina", "Limonada", "Zumos para cóctel",
    ], [
        ("Soda Bretaña 300ml", 1700, 19), ("Agua Tónica Schweppes 300ml", 2300, 19),
        ("Granadina Dolores 750ml", 9500, 19), ("Zumo de Limón Natural 1000ml", 6800, 19),
    ]),
    "Licores dulces": ("LIC", (156, 39, 176), "botella", [
        "Cremas de licor", "Licores de café", "Licores de frutas", "Vermut", "Aperitivos",
    ], [
        ("Licor de Café Kahlúa 750ml", 72000, 5), ("Aperitivo Aperol 750ml", 69000, 5),
        ("Vermut Martini Rosso 750ml", 45000, 5), ("Licor Jägermeister 700ml", 88000, 5),
        ("Licor de Mora Sabajón Apóstoles 750ml", 28000, 5),
    ]),
    "Comidas rápidas": ("COM", (230, 81, 0), "caja", [
        "Empanadas", "Picadas", "Salchipapas", "Hamburguesas", "Perros calientes",
    ], [
        ("Empanada de Carne", 1200, 8), ("Picada Personal", 14000, 8),
        ("Salchipapa Sencilla", 7000, 8), ("Hamburguesa Clásica", 9500, 8),
        ("Perro Caliente Sencillo", 6000, 8),
    ]),
    "Cócteles": ("COC", (0, 150, 136), "copa", [
        "Cócteles clásicos", "Micheladas", "Cócteles sin alcohol", "Shots de la casa", "Jarras",
    ], [
        ("Michelada Clásica", 3500, 8), ("Mojito de la Casa", 9000, 8),
        ("Margarita Clásica", 10000, 8), ("Piña Colada", 9500, 8),
        ("Limonada de Coco", 5500, 8), ("Jarra de Sangría 1500ml", 22000, 8),
    ]),
    "Cafetería": ("CAF", (93, 64, 55), "taza", [
        "Café", "Aromáticas", "Chocolate", "Bebidas calientes", "Panadería",
    ], [
        ("Tinto Pequeño", 600, 8), ("Café con Leche", 1500, 8), ("Aromática de Frutas", 1000, 8),
        ("Chocolate Caliente", 2000, 8), ("Pandebono", 900, 8),
    ]),
    "Licores importados": ("IMP", (55, 71, 79), "botella", [
        "Pisco", "Cachaça", "Brandy", "Coñac", "Anís",
    ], [
        ("Pisco Capel 700ml", 58000, 5), ("Cachaça 51 965ml", 42000, 5),
        ("Brandy Domecq 750ml", 51000, 5), ("Anís Ramazzotti 700ml", 64000, 5),
    ]),
    "Promociones": ("PRO", (183, 28, 28), "caja", [
        "Combos de cerveza", "Combos de licor", "Paquetes para fiesta", "Six packs", "Ofertas",
    ], [
        ("Six Pack Cerveza Águila Lata 330ml", 12000, 19), ("Six Pack Cerveza Poker Lata 330ml", 11800, 19),
        ("Combo Aguardiente y 4 Gaseosas", 45000, 5), ("Canasta Cerveza Costeña x30", 54000, 19),
    ]),
}  # fmt: skip

PROVEEDORES_BASE = [
    "Distribuidora", "Comercializadora", "Licores", "Bebidas", "Inversiones", "Mayorista",
    "Depósito", "Importadora", "Surtidora", "Representaciones",
]  # fmt: skip
PROVEEDORES_NOMBRE = [
    "Andina", "del Valle", "La Montaña", "El Dorado", "Costa Norte", "San Jorge", "Santa Fe",
    "Los Andes", "El Cafetal", "Pacífico",
]  # fmt: skip
CIUDADES = [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Manizales",
    "Cartagena", "Ibagué", "Villavicencio", "Armenia", "Neiva", "Popayán", "Pasto",
]  # fmt: skip

PQRS = [
    ("queja", "servicio", "Demora en la atención de la mesa",
     "El pedido de la mesa tardó más de cuarenta minutos en llegar y nadie nos informó."),
    ("reclamo", "productos", "Cerveza servida caliente",
     "Pedimos una canasta de cerveza y la mitad llegó sin refrigerar. Solicito el cambio."),
    ("reclamo", "productos", "Cobro de un producto no consumido",
     "En la cuenta aparece una botella de aguardiente que no pedimos. Solicito la devolución."),
    ("peticion", "servicio", "Solicitud de factura electrónica",
     "Necesito la factura electrónica de mi consumo a nombre de la empresa para el reembolso."),
    ("sugerencia", "servicio", "Ampliar el horario los domingos",
     "Sería bueno que el establecimiento abriera hasta más tarde los domingos de puente."),
    ("queja", "servicio", "Música demasiado alta",
     "El volumen de la música no permitía conversar en la zona de mesas del segundo piso."),
    ("peticion", "productos", "Disponibilidad de cerveza artesanal",
     "Quisiera saber si van a tener más referencias de cerveza artesanal de la región."),
    ("reclamo", "productos", "Producto vencido en la tienda",
     "Compré un paquete de papas y estaba vencido desde hace dos semanas. Pido el cambio."),
    ("sugerencia", "productos", "Opciones sin alcohol",
     "Recomiendo agregar más cócteles sin alcohol para quienes conducen esa noche."),
    ("queja", "servicio", "Trato poco amable en caja",
     "La persona de la caja respondió de mala manera cuando pregunté por un descuento."),
]  # fmt: skip


def _pesos(valor) -> Decimal:
    """Redondea a centenas, como se cobran los precios en Colombia."""
    return (Decimal(valor) / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 100


# --------------------------------------------------------------------------- #
# Imágenes de producto (generadas, sin descargar nada)
# --------------------------------------------------------------------------- #
def _fuente(tamano: int):
    for ruta in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(ruta).exists():
            return ImageFont.truetype(ruta, tamano)
    return ImageFont.load_default(size=tamano)


def _aclarar(color, factor):
    return tuple(int(c + (255 - c) * factor) for c in color)


def _oscurecer(color, factor):
    return tuple(int(c * (1 - factor)) for c in color)


def imagen_de_producto(nombre: str, color, forma: str) -> str:
    """Dibuja una ilustración simple del producto y la devuelve como data URL JPEG."""
    lado = 240
    imagen = Image.new("RGB", (lado, lado), _aclarar(color, 0.82))
    dibujo = ImageDraw.Draw(imagen)
    # Fondo con un degradado suave hacia abajo.
    for y in range(lado):
        dibujo.line([(0, y), (lado, y)], fill=_aclarar(color, 0.88 - 0.25 * y / lado))

    principal, sombra, brillo = color, _oscurecer(color, 0.35), _aclarar(color, 0.55)
    cx = lado // 2
    if forma == "botella":
        dibujo.rounded_rectangle([cx - 34, 70, cx + 34, 205], 18, fill=principal)
        dibujo.rectangle([cx - 13, 30, cx + 13, 76], fill=principal)
        dibujo.rectangle([cx - 15, 22, cx + 15, 36], fill=sombra)
        dibujo.rounded_rectangle([cx - 28, 110, cx + 28, 165], 6, fill=(250, 248, 240))
        dibujo.rectangle([cx - 26, 82, cx - 18, 196], fill=brillo)
    elif forma == "lata":
        dibujo.rounded_rectangle([cx - 40, 50, cx + 40, 205], 14, fill=principal)
        dibujo.ellipse([cx - 40, 40, cx + 40, 62], fill=(200, 200, 205))
        dibujo.rectangle([cx - 40, 105, cx + 40, 150], fill=(250, 248, 240))
        dibujo.rectangle([cx - 33, 60, cx - 25, 200], fill=brillo)
    elif forma == "paquete":
        dibujo.polygon(
            [(cx - 60, 60), (cx + 60, 60), (cx + 52, 205), (cx - 52, 205)], fill=principal
        )
        dibujo.rectangle([cx - 62, 50, cx + 62, 66], fill=sombra)
        dibujo.ellipse([cx - 32, 100, cx + 32, 164], fill=(250, 248, 240))
    elif forma == "copa":
        dibujo.polygon([(cx - 50, 50), (cx + 50, 50), (cx + 8, 130), (cx - 8, 130)], fill=principal)
        dibujo.rectangle([cx - 4, 128, cx + 4, 190], fill=sombra)
        dibujo.ellipse([cx - 36, 186, cx + 36, 202], fill=sombra)
        dibujo.ellipse([cx + 22, 36, cx + 46, 60], fill=(124, 179, 66))
    elif forma == "taza":
        dibujo.rounded_rectangle([cx - 50, 85, cx + 34, 185], 16, fill=principal)
        dibujo.ellipse([cx + 22, 105, cx + 62, 155], outline=principal, width=10)
        dibujo.ellipse([cx - 75, 180, cx + 60, 200], fill=sombra)
    else:  # caja
        dibujo.rectangle([cx - 52, 55, cx + 52, 205], fill=principal)
        dibujo.polygon([(cx - 52, 55), (cx - 30, 35), (cx + 74, 35), (cx + 52, 55)], fill=brillo)
        dibujo.polygon([(cx + 52, 55), (cx + 74, 35), (cx + 74, 185), (cx + 52, 205)], fill=sombra)
        dibujo.rectangle([cx - 40, 110, cx + 40, 150], fill=(250, 248, 240))

    # Iniciales de la marca sobre la etiqueta.
    palabras = [p for p in nombre.split() if p[0].isalpha() and len(p) > 2]
    marca = (palabras[1] if len(palabras) > 1 else palabras[0])[:3].upper()
    # La fuente de respaldo del contenedor no trae tildes: se dejan solo las letras base.
    marca = unicodedata.normalize("NFKD", marca).encode("ascii", "ignore").decode()
    fuente = _fuente(22)
    caja = dibujo.textbbox((0, 0), marca, font=fuente)
    y_etiqueta = {"lata": 127, "caja": 130, "paquete": 132, "botella": 137}.get(forma, 220)
    if forma in ("copa", "taza"):
        y_etiqueta = 222
    dibujo.text(
        (cx - (caja[2] - caja[0]) / 2, y_etiqueta - (caja[3] - caja[1]) / 2 - caja[1]),
        marca,
        font=fuente,
        fill=sombra if forma not in ("copa", "taza") else _oscurecer(color, 0.5),
    )

    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(salida.getvalue()).decode("ascii")


# --------------------------------------------------------------------------- #
# Factura de proveedor en PDF (texto real, sin librerías extra)
# --------------------------------------------------------------------------- #
def _escapar_pdf(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def factura_pdf(renglones: list[tuple[int, int, str, int]]) -> bytes:
    """Arma un PDF de una página con Helvetica.

    Cada renglón es `(x, y, texto, tamaño)`; el texto va en Latin-1 (WinAnsi),
    que cubre las tildes del español.
    """
    operaciones = []
    for x, y, texto, tamano in renglones:
        fuente = "/F2" if tamano >= 11 else "/F1"
        operaciones.append(f"BT {fuente} {tamano} Tf {x} {y} Td ({_escapar_pdf(texto)}) Tj ET")
    contenido = "\n".join(operaciones).encode("latin-1", errors="replace")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(contenido) + contenido + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    salida = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    posiciones = []
    for numero, objeto in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    salida += b"".join(b"%010d 00000 n \n" % posicion for posicion in posiciones)
    salida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        inicio_xref,
    )
    return salida


def _miles(valor: Decimal) -> str:
    return f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class Command(BaseCommand):
    help = "Llena un negocio con datos de prueba (mínimo 100 por módulo) usando la API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--correo", default="admin@gmail.com", help="Administrador del negocio."
        )
        parser.add_argument("--minimo", type=int, default=100, help="Registros mínimos por módulo.")
        parser.add_argument("--semilla", type=int, default=7, help="Semilla de los datos al azar.")
        parser.add_argument(
            "--reiniciar",
            action="store_true",
            help="Borra antes los datos operativos del negocio (catálogo, clientes, compras, "
            "ventas, cartera, inventario y PQRs). Usuarios, impuestos y medios de pago se quedan.",
        )

    # ------------------------------------------------------------------ #
    def handle(self, *args, **opciones):
        if not settings.DEBUG:
            raise CommandError("Solo se pueblan datos de prueba con DEBUG activo.")
        try:
            from faker import Faker
        except ImportError as error:
            raise CommandError("Falta Faker (viene con requirements/local.txt).") from error

        self.admin = Usuario.objects.filter(correo=opciones["correo"]).first()
        if not self.admin or not self.admin.negocio_id:
            raise CommandError(f"No hay un administrador con negocio para {opciones['correo']}.")
        self.negocio_id = self.admin.negocio_id
        if opciones["reiniciar"]:
            self._reiniciar()
        if Categoria.objects.filter(negocio_id=self.negocio_id).exists():
            raise CommandError(
                "Este negocio ya tiene categorías: el script solo corre sobre un negocio vacío."
            )

        self.minimo = opciones["minimo"]
        random.seed(opciones["semilla"])
        self.falso = Faker("es_CO")
        Faker.seed(opciones["semilla"])
        self.api = APIClient(SERVER_NAME="localhost")
        self.api.force_authenticate(self.admin)
        self.ahora = timezone.now()

        with transaction.atomic():
            self._metodos_de_pago()
            self._categorias()
            self._proveedores()
            self._productos()
            self._clientes()
            self._compras()
            self._ventas()
            self._abonos()
            self._pqrs()
        self._factura_de_prueba()
        self._resumen()

    @transaction.atomic
    def _reiniciar(self):
        """Borra lo operativo del negocio, de las hojas a la raíz (las FK son PROTECT)."""
        filtro = {"negocio_id": self.negocio_id}
        for modelo in (
            PqrSeguimiento, Pqr, PagoVenta, CuentaPorCobrar, MovimientoInventario, DetalleVenta,
            Venta, PagoCompra, CuentaPorPagar, DetalleCompra, Compra, Existencia, Producto,
            Cliente, Proveedor, Categoria,
        ):  # fmt: skip
            modelo.objects.filter(**filtro).delete()
        self._paso("datos anteriores del negocio borrados")

    # ------------------------------------------------------------------ #
    def _post(self, ruta: str, datos: dict, *, formato="json"):
        respuesta = self.api.post(f"{API}{ruta}", datos, format=formato)
        if respuesta.status_code >= 400:
            raise CommandError(f"POST {ruta} respondió {respuesta.status_code}: {respuesta.data}")
        return respuesta.data

    def _fecha(self, dia: int):
        """Un momento del día `dia` (0 = hace DIAS_DE_HISTORIA días), en horario del bar."""
        base = self.ahora - timedelta(days=DIAS_DE_HISTORIA - dia)
        return base.replace(hour=random.randint(10, 23), minute=random.randint(0, 59))

    def _paso(self, texto: str):
        self.stdout.write(f"  · {texto}")

    # ------------------------------------------------------------------ #
    def _metodos_de_pago(self):
        self.metodos = list(
            MetodoPago.objects.filter(negocio_id=self.negocio_id, estado=True).values_list(
                "id", flat=True
            )
        )
        if not self.metodos:
            raise CommandError("El negocio no tiene medios de pago activos.")
        self.impuestos = {}
        for impuesto in Impuesto.objects.filter(negocio_id=self.negocio_id, activo=True):
            self.impuestos.setdefault(int(impuesto.porcentaje), impuesto.id)
        if 0 not in self.impuestos:
            raise CommandError("El negocio necesita una tarifa de IVA del 0 %.")

    def _categorias(self):
        self.categorias = {}
        nombres = [(f, sub) for f, datos in FAMILIAS.items() for sub in datos[3]]
        extra = 0
        while len(nombres) < self.minimo:
            extra += 1
            nombres.append(("Promociones", f"Temporada {extra}"))
        for familia, nombre in nombres:
            creada = self._post(
                "/catalogo/categorias/",
                {"nombre": nombre, "descripcion": f"{nombre} · familia {familia.lower()}"},
            )
            self.categorias.setdefault(familia, []).append(creada["id"])
        self._paso(f"{len(nombres)} categorías")

    def _proveedores(self):
        self.proveedores = []
        usados = set()
        while len(self.proveedores) < self.minimo:
            nombre = f"{random.choice(PROVEEDORES_BASE)} {random.choice(PROVEEDORES_NOMBRE)}"
            if len(self.proveedores) >= len(PROVEEDORES_BASE) * len(PROVEEDORES_NOMBRE) // 2:
                nombre += f" {self.falso.last_name()}"
            nombre += random.choice([" S.A.S.", " Ltda.", " S.A.S."])
            if nombre in usados:
                continue
            usados.add(nombre)
            nit = f"9{random.randint(10000000, 99999999)}"
            ciudad = random.choice(CIUDADES)
            creado = self._post(
                "/catalogo/proveedores/",
                {
                    "razon_social": nombre,
                    "nit": nit,
                    "nombre_contacto": self.falso.name(),
                    "telefono": f"3{random.randint(100000000, 259999999)}",
                    "correo": f"ventas{len(self.proveedores) + 1}@{nombre.split()[0].lower()}.com.co",
                    "ciudad": ciudad,
                    "direccion": self.falso.street_address(),
                },
            )
            self.proveedores.append({"id": creado["id"], "nit": nit, "razon_social": nombre})
        self._paso(f"{len(self.proveedores)} proveedores")

    def _productos(self):
        """Prepara el catálogo. Los productos nacen en las primeras compras (así
        funciona la app: no hay alta de producto suelta)."""
        self.productos = []
        self.por_crear = []
        consecutivos = {}
        vuelta = 0
        while len(self.por_crear) < self.minimo:
            vuelta += 1
            for familia, (prefijo, color, forma, _, productos) in FAMILIAS.items():
                for nombre, costo, iva in productos:
                    if vuelta > 1:
                        if len(self.por_crear) >= self.minimo:
                            break
                        nombre, costo = f"{nombre} Pack x{vuelta + 1}", costo * (vuelta + 1)
                    consecutivos[prefijo] = consecutivos.get(prefijo, 0) + 1
                    self.por_crear.append(
                        {
                            "sku": f"{prefijo}-{consecutivos[prefijo]:03d}",
                            "nombre": nombre,
                            "familia": familia,
                            "costo": _pesos(costo),
                            # Sin tarifa de impoconsumo en el negocio: el 8 % va como no gravado.
                            "iva": iva if iva in self.impuestos else 0,
                            "imagen": imagen_de_producto(nombre, color, forma),
                        }
                    )
        random.shuffle(self.por_crear)
        self._paso(f"{len(self.por_crear)} productos con imagen por crear en las compras")

    def _completar_producto(self, producto_id: int, datos: dict):
        """Lo que la compra no fija: margen, precio redondeado, mínimos y código."""
        margen = Decimal(random.choice([25, 30, 35, 40, 45, 50]))
        precio = _pesos(datos["costo"] * (1 + margen / 100) * (1 + Decimal(datos["iva"]) / 100))
        Producto.objects.filter(id=producto_id).update(
            margen_ganancia=margen,
            precio_venta=precio,
            precio_venta_automatico=False,
            stock_minimo=random.choice([5, 6, 10, 12]),
            codigo=f"{datos['sku'][:2]}{random.randint(1000, 9999)}",
        )
        Existencia.objects.filter(producto_id=producto_id).update(
            cantidad_minima=random.choice([5, 6, 10, 12])
        )
        self.productos.append({**datos, "id": producto_id})

    def _clientes(self):
        self.clientes = []
        documentos = set()
        while len(self.clientes) < max(self.minimo, 120):
            documento = str(random.randint(10_000_000, 1_299_999_999))
            if documento in documentos:
                continue
            documentos.add(documento)
            nombre, apellido = (
                self.falso.first_name(),
                f"{self.falso.last_name()} {self.falso.last_name()}",
            )
            creado = self._post(
                "/clientes/",
                {
                    "tipo_documento": random.choice(["cedula"] * 9 + ["cedula_extranjeria"]),
                    "numero_documento": documento,
                    "nombre": nombre,
                    "apellido": apellido,
                    "fecha_nacimiento": self.falso.date_of_birth(
                        minimum_age=18, maximum_age=70
                    ).isoformat(),
                    "telefono": f"3{random.randint(000000000, 259999999):09d}",
                    "correo": f"{nombre}.{apellido.split()[0]}{random.randint(1, 99)}@correo.com".lower()
                    .replace("á", "a")
                    .replace("é", "e")
                    .replace("í", "i")
                    .replace("ó", "o")
                    .replace("ú", "u")
                    .replace("ñ", "n"),
                    "ciudad": random.choice(CIUDADES),
                    "notas": random.choice(
                        ["", "", "Cliente frecuente", "Prefiere pagar con Nequi"]
                    ),
                },
            )
            self.clientes.append({"id": creado["id"], "documento": documento,
                                  "nombre": f"{nombre} {apellido}"})  # fmt: skip
        self._paso(f"{len(self.clientes)} clientes")

    # ------------------------------------------------------------------ #
    def _compras(self):
        """Compras de contado y a crédito repartidas en la historia.

        Las primeras dejan stock de todo el catálogo para que las ventas
        siempre tengan de dónde salir.
        """
        # La mitad a crédito, con holgura para que, tras los abonos, sigan
        # abiertas al menos `minimo` cuentas por pagar.
        cantidad = self.minimo * 2 + 60
        self.cuentas_por_pagar = []
        for numero in range(cantidad):
            credito = numero % 2 == 1
            proveedor = random.choice(self.proveedores)
            nuevos = [self.por_crear.pop() for _ in range(min(5, len(self.por_crear)))]
            if nuevos:
                detalles = [
                    {
                        "producto_nuevo": {
                            "sku": n["sku"],
                            "nombre": n["nombre"],
                            "categoria_id": random.choice(self.categorias[n["familia"]]),
                            "impuesto_id": self.impuestos[n["iva"]],
                            "imagen": n["imagen"],
                        },
                        "cantidad": random.randint(36, 96),
                        "costo_unitario": str(n["costo"]),
                    }
                    for n in nuevos
                ]
            else:
                detalles = [
                    {
                        "producto_id": p["id"],
                        "cantidad": random.randint(24, 72),
                        "costo_unitario": str(
                            _pesos(p["costo"] * Decimal(random.uniform(0.95, 1.05)))
                        ),
                    }
                    for p in random.sample(self.productos, random.randint(2, 5))
                ]
            datos = {
                "proveedor_id": proveedor["id"],
                "numero_factura": f"FE-{random.randint(1000, 99999)}",
                "condicion_pago": "CREDITO" if credito else "CONTADO",
                "metodo_pago_id": None if credito else random.choice(self.metodos),
                "fecha_vencimiento": (
                    (timezone.localdate() + timedelta(days=random.randint(15, 60))).isoformat()
                    if credito
                    else None
                ),
                "estado": "RECIBIDA",
                "detalles": detalles,
            }
            compra = self._post("/compras/", datos)
            por_sku = {d["sku"]: d["producto_id"] for d in compra["detalles"]}
            for n in nuevos:
                self._completar_producto(por_sku[n["sku"]], n)
            fecha = self._fecha(min(DIAS_DE_HISTORIA - 1, numero * DIAS_DE_HISTORIA // cantidad))
            Compra.objects.filter(id=compra["id"]).update(fecha_compra=fecha)
            PagoCompra.objects.filter(compra_id=compra["id"]).update(fecha_pago=fecha)
            MovimientoInventario.objects.filter(detalle_compra__compra_id=compra["id"]).update(
                fecha=fecha
            )
            if credito:
                vence = (fecha + timedelta(days=random.choice([30, 45, 60]))).date()
                Compra.objects.filter(id=compra["id"]).update(fecha_vencimiento=vence)
                CuentaPorPagar.objects.filter(compra_id=compra["id"]).update(
                    fecha_vencimiento=vence
                )
                self.cuentas_por_pagar.append((compra["id"], fecha))
        self._paso(f"{cantidad} compras ({len(self.cuentas_por_pagar)} a crédito)")

    def _ventas(self):
        cantidad = self.minimo * 3 + 50
        self.cuentas_por_cobrar = []
        # Las ventas empiezan cuando ya hay mercancía: después de la primera semana.
        for numero in range(cantidad):
            credito = numero % 5 in (1, 3) and len(self.cuentas_por_cobrar) < cantidad
            cliente = random.choice(self.clientes) if credito or random.random() < 0.5 else None
            lineas = random.sample(self.productos, random.randint(1, 4))
            datos = {
                "tipo_pago": "credito" if credito else "contado",
                "cliente_id": cliente["id"] if cliente else None,
                "metodo_pago_id": None if credito else random.choice(self.metodos),
                "fecha_vencimiento": (
                    (timezone.localdate() + timedelta(days=random.randint(10, 45))).isoformat()
                    if credito
                    else None
                ),
                "estado_entrega": "entregada",
                "descuento_porcentaje": random.choice([0, 0, 0, 0, 5, 10]),
                "lineas": [
                    {"producto_id": p["id"], "cantidad": random.randint(1, 3)} for p in lineas
                ],
            }
            venta = self._post("/ventas/", datos)
            dia = 7 + numero * (DIAS_DE_HISTORIA - 7) // cantidad
            fecha = self._fecha(min(DIAS_DE_HISTORIA, dia))
            if fecha > self.ahora:
                fecha = self.ahora - timedelta(minutes=cantidad - numero)
            Venta.objects.filter(id=venta["id"]).update(fecha=fecha)
            PagoVenta.objects.filter(venta_id=venta["id"]).update(fecha=fecha)
            MovimientoInventario.objects.filter(detalle_venta__venta_id=venta["id"]).update(
                fecha=fecha
            )
            if credito:
                vence = (fecha + timedelta(days=random.choice([15, 30, 45]))).date()
                Venta.objects.filter(id=venta["id"]).update(fecha_vencimiento=vence)
                CuentaPorCobrar.objects.filter(venta_id=venta["id"]).update(fecha_vencimiento=vence)
                self.cuentas_por_cobrar.append((venta["id"], fecha))
        self._paso(f"{cantidad} ventas ({len(self.cuentas_por_cobrar)} a crédito)")

    def _abonos(self):
        """Abona parte de la cartera: unas cuentas quedan pagadas y otras a medias.

        Solo se saldan del todo las que sobran por encima de `minimo`, para que
        las pantallas de cartera (que muestran lo abierto) tengan al menos eso.
        """
        abonos = 0
        saldables = len(self.cuentas_por_pagar) - self.minimo
        for compra_id, fecha in self.cuentas_por_pagar:
            if random.random() < 0.4:
                continue
            cuenta = CuentaPorPagar.objects.get(compra_id=compra_id)
            saldar = saldables > 0 and random.random() < 0.5
            saldables -= int(saldar)
            monto = cuenta.saldo if saldar else _pesos(cuenta.saldo * Decimal("0.4"))
            self._post(
                f"/compras/cuentas-por-pagar/{cuenta.id}/abonos/",
                {"monto": str(monto), "metodo_pago_id": random.choice(self.metodos),
                 "referencia": f"TRF-{random.randint(10000, 99999)}"},
            )  # fmt: skip
            pago_fecha = min(self.ahora, fecha + timedelta(days=random.randint(5, 25)))
            ultimo = PagoCompra.objects.filter(compra_id=compra_id).latest("id")
            PagoCompra.objects.filter(id=ultimo.id).update(fecha_pago=pago_fecha)
            abonos += 1
        saldables = len(self.cuentas_por_cobrar) - self.minimo
        for venta_id, fecha in self.cuentas_por_cobrar:
            if random.random() < 0.4:
                continue
            cuenta = CuentaPorCobrar.objects.get(venta_id=venta_id)
            saldar = saldables > 0 and random.random() < 0.5
            saldables -= int(saldar)
            monto = cuenta.saldo if saldar else _pesos(cuenta.saldo * Decimal("0.5"))
            if monto <= 0:
                continue
            self._post(
                f"/ventas/cuentas-por-cobrar/{cuenta.id}/abonos/",
                {"monto": str(monto), "metodo_pago_id": random.choice(self.metodos)},
            )
            pago_fecha = min(self.ahora, fecha + timedelta(days=random.randint(3, 20)))
            ultimo = PagoVenta.objects.filter(venta_id=venta_id).latest("id")
            PagoVenta.objects.filter(id=ultimo.id).update(fecha=pago_fecha)
            abonos += 1
        self._paso(f"{abonos} abonos de cartera")

    def _pqrs(self):
        ventas = list(Venta.objects.filter(negocio_id=self.negocio_id).values_list("id", flat=True))
        cantidad = self.minimo + 10
        for numero in range(cantidad):
            tipo, ambito, asunto, descripcion = random.choice(PQRS)
            cliente = random.choice(self.clientes)
            pqr = self._post(
                "/pqrs/",
                {
                    "cliente": cliente["id"],
                    "nombre_solicitante": cliente["nombre"],
                    "documento_solicitante": cliente["documento"],
                    "telefono_solicitante": f"3{random.randint(100000000, 259999999)}",
                    "tipo": tipo,
                    "ambito": ambito,
                    "canal": random.choice(["telefonico", "presencial"]),
                    "asunto": asunto,
                    "descripcion": descripcion,
                },
            )
            fecha = self._fecha(
                min(DIAS_DE_HISTORIA, 10 + numero * (DIAS_DE_HISTORIA - 10) // cantidad)
            )
            fecha = min(fecha, self.ahora)
            Pqr.objects.filter(id=pqr["id"]).update(
                fecha_radicacion=fecha, venta_id=random.choice(ventas) if ventas else None
            )
            PqrSeguimiento.objects.filter(pqr_id=pqr["id"]).update(creado_en=fecha)

            # Unas se quedan radicadas, otras avanzan hasta el cierre.
            avance = random.choice([0, 1, 1, 2, 3, 3])
            ruta = f"/pqrs/{pqr['id']}/seguimientos/"
            if avance >= 1:
                self._post(ruta, {"tipo": "cambio_estado", "nuevo_estado": "en_revision"})
            if avance >= 2:
                self._post(
                    ruta,
                    {"tipo": "nota", "contenido": "Se revisó el caso con el turno de esa noche."},
                )
            if avance >= 3:
                self._post(ruta, {"tipo": "respuesta", "contenido":
                                  "Lamentamos lo ocurrido. Aplicamos un bono de consumo para su próxima visita."})  # fmt: skip
                self._post(ruta, {"tipo": "cambio_estado", "nuevo_estado": "cerrada"})
        self._paso(f"{cantidad} PQRs")

    # ------------------------------------------------------------------ #
    def _factura_de_prueba(self):
        """Factura de un proveedor real del negocio con productos del catálogo y uno nuevo."""
        proveedor = self.proveedores[0]
        elegidos = random.sample(self.productos, 6)
        nit = proveedor["nit"]
        nit_impreso = f"{nit[:3]}.{nit[3:6]}.{nit[6:]}-{random.randint(0, 9)}"
        y = 740
        renglones = [
            (50, y, proveedor["razon_social"].upper(), 14),
            (50, y - 16, f"NIT {nit_impreso}", 9),
            (50, y - 28, "Responsable de IVA - Bogotá D.C.", 9),
            (380, y, "FACTURA ELECTRÓNICA DE VENTA", 11),
            (380, y - 16, f"No. FE-{random.randint(10000, 99999)}", 11),
            (380, y - 30, f"Fecha: {timezone.localdate():%d/%m/%Y}", 9),
            (50, y - 60, "Cliente: El Tapaso", 9),
            (50, y - 88, "Item  Código  Descripción  Cant  V.Unit  Total", 9),
        ]
        y -= 106
        subtotal = Decimal(0)
        for item, producto in enumerate(elegidos, 1):
            # El proveedor escribe los nombres a su manera: mayúsculas y abreviado.
            nombre = producto["nombre"].upper().replace("CERVEZA", "CERV").replace("GASEOSA", "GAS")
            cantidad = random.choice([6, 12, 24, 36, 48])
            unitario = _pesos(producto["costo"] * Decimal("0.98"))
            total = unitario * cantidad
            subtotal += total
            # Dos con el SKU del catálogo, dos sin código y dos con el código propio
            # del proveedor: así se ven los tres caminos del buscador.
            codigo = (producto["sku"], "", f"PRV-{random.randint(1000, 9999)}")[(item - 1) // 2]
            renglon = f"{item}  {codigo}  {nombre}" if codigo else f"{item}  {nombre}"
            renglones.append(
                (50, y, f"{renglon}  {cantidad}  {_miles(unitario)}  {_miles(total)}", 9)
            )
            y -= 16
        # Uno que no está en el catálogo, para ver un "Nuevo".
        renglones.append(
            (
                50,
                y,
                f"{len(elegidos) + 1}  HL-0099  CARBÓN PARA ASADOR 3KG  4  12.500,00  50.000,00",
                9,
            )
        )
        subtotal += Decimal("50000")
        y -= 30
        iva = (subtotal * Decimal("0.19")).quantize(Decimal("0.01"))
        renglones += [
            (330, y, f"SUBTOTAL {_miles(subtotal)}", 10),
            (330, y - 16, f"IVA 19% {_miles(iva)}", 10),
            (330, y - 32, f"TOTAL {_miles(subtotal + iva)}", 11),
            (50, y - 70, "Factura de prueba generada por poblar_datos_de_prueba.", 8),
        ]  # fmt: skip
        RUTA_FACTURA.parent.mkdir(parents=True, exist_ok=True)
        RUTA_FACTURA.write_bytes(factura_pdf(renglones))
        self._paso(f"factura PDF de prueba: {RUTA_FACTURA}")

    def _resumen(self):
        self.stdout.write(self.style.SUCCESS("Datos de prueba creados."))
