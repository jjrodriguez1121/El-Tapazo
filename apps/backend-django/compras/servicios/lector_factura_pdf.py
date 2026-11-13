"""Lee los renglones de una factura de proveedor a partir del texto de su PDF.

Funciones puras, sin base de datos. Sigue el enfoque del lector de facturas de
GearShift, adaptado a texto plano (`pypdf` ya entrega un renglón por línea):

1. Los números de un renglón se distinguen por **aritmética**, no por la
   columna: cantidad × costo unitario debe dar el total del renglón (también
   con el IVA incluido o con el descuento/IVA de otra columna). Las columnas
   numéricas que sobran (código, % IVA, % descuento) no cuadran y se ignoran.
2. Lo que está a la izquierda de esos números es la descripción; si empieza
   con un código del proveedor (`MP-0141`, `10234`), se separa.
3. Un renglón sin números justo debajo de un producto es el resto de su nombre.
4. La tabla termina en el primer renglón que empieza con SUBTOTAL, IVA o TOTAL.
"""

import io
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAXIMO_DE_PAGINAS = 15
CARACTERES_MINIMOS = 20
CENTAVOS = Decimal("0.01")
CIEN = Decimal("100")
#: Un total que difiere de cantidad × unitario en más de esto no cuadra.
TOLERANCIA_DEL_TOTAL = Decimal("0.005")
#: El total puede traer el IVA del renglón (19 %, 8 %, 5 %).
FACTORES_DEL_TOTAL = (Decimal("1"), Decimal("1.19"), Decimal("1.08"), Decimal("1.05"))

_MILES_CON_PUNTO = re.compile(r"^\d{1,3}(\.\d{3})+$")
_MILES_CON_COMA = re.compile(r"^\d{1,3}(,\d{3})+$")
_CANTIDAD_CON_UNIDAD = re.compile(
    r"^(\d+(?:[.,]\d+)?)\s*(?:UN|UND|UNID|UNIDAD|UNIDADES|PZA|PZ|KG|LT|LTS|GL|CJ|PAQ|BULTO)\.?$"
)
_ENCABEZADO_DE_TABLA = re.compile(
    r"\b(DESCRIPCION|DETALLE|PRODUCTO|ARTICULO|CONCEPTO)\b.*\b(CANT|CANTIDAD|UNIDADES)\b"
)
_INICIO_DEL_RESUMEN = re.compile(
    r"^(SUB\s*TOTAL|IVA|TOTAL|RETE|DESCUENTO|SON\b|OBSERV|FORMA DE PAGO)"
)
_NIT = re.compile(r"(?:\bNIT\b|\bN\.I\.T\.?)\s*[:.]?\s*(\d[\d.\- ]{5,17}\d)")
_NUMERO_FACTURA = re.compile(
    r"FACTURA(?:\s+(?:DE\s+VENTA|ELECTRONICA))*(?:\s*(?:NO|N°|NUMERO|#))?\.?\s*[:.]?\s*"
    r"([A-Z]{0,6}\s?-?\s?\d{2,12})"
)
_NUMERO_FACTURA_SUELTO = re.compile(r"\bNO\.\s*([A-Z]{1,6}-\d{2,12})\b")
#: Primera palabra de la descripción que en realidad es el código del proveedor.
_CODIGO_INICIAL = re.compile(r"^(?:[A-Z]{1,5}-\d{2,}[A-Z0-9-]*|\d{4,}[A-Z]?|\d{2,}-\d+)$")
_NUMERO_DE_RENGLON = re.compile(r"^\d{1,3}$")
_SUFIJO_DE_EMPRESA = re.compile(r"\b(S\.?A\.?S\.?|LTDA\.?|S\.?A\.?|E\.?U\.?)(?=\s|$)")


class FacturaIlegible(Exception):
    """El archivo no se pudo leer como factura; el mensaje se muestra tal cual."""


@dataclass(slots=True)
class LineaLeida:
    descripcion: str
    cantidad: Decimal
    costo_unitario: Decimal
    total_impreso: Decimal | None
    codigo: str = ""
    #: Si cantidad × unitario dio el total.
    cuadra: bool = True


@dataclass(slots=True)
class FacturaLeida:
    numero_factura: str = ""
    nit: str = ""
    nombre_proveedor: str = ""
    lineas: list[LineaLeida] = field(default_factory=list)


def normalizar_factura(texto: str) -> str:
    """Mayúsculas, sin tildes y con un solo espacio: la forma en que se comparan."""
    descompuesto = unicodedata.normalize("NFKD", texto or "")
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes).strip().upper()


def leer_valor(texto: str) -> Decimal | None:
    """Lee un número escrito a la colombiana o a la inglesa; `None` si no es uno.

    `18.500` y `18,500` son dieciocho mil quinientos; `18.500,50` y `18,500.50`
    también. Un solo separador que no separa grupos de tres es el decimal.
    """
    limpio = texto.replace("$", "").replace(" ", "").strip()
    if not limpio or not re.fullmatch(r"[\d.,]+", limpio) or not re.search(r"\d", limpio):
        return None
    tiene_punto, tiene_coma = "." in limpio, "," in limpio
    if tiene_punto and tiene_coma:
        decimal = "." if limpio.rfind(".") > limpio.rfind(",") else ","
        miles = "," if decimal == "." else "."
        limpio = limpio.replace(miles, "").replace(decimal, ".")
    elif tiene_punto:
        limpio = limpio.replace(".", "") if _MILES_CON_PUNTO.match(limpio) else limpio
    elif tiene_coma:
        limpio = (
            limpio.replace(",", "") if _MILES_CON_COMA.match(limpio) else limpio.replace(",", ".")
        )
    try:
        return Decimal(limpio).quantize(CENTAVOS)
    except InvalidOperation:
        return None


def _leer_numero(ficha: str) -> Decimal | None:
    """Un número, también con su unidad pegada (`10UND`, `2,5KG`)."""
    valor = leer_valor(ficha)
    if valor is not None:
        return valor
    encontrado = _CANTIDAD_CON_UNIDAD.match(normalizar_factura(ficha))
    return leer_valor(encontrado[1]) if encontrado else None


def _cuadra(
    cantidad: Decimal, unitario: Decimal, total: Decimal, porcentajes: tuple[Decimal, ...]
) -> bool:
    """Si cantidad × unitario da el total (con IVA, o con el descuento/IVA de otra columna)."""
    if cantidad <= 0 or unitario < 0 or total <= 0:
        return False
    base = cantidad * unitario
    tolerancia = max(Decimal("1"), TOLERANCIA_DEL_TOTAL * total)
    if any(abs(base * factor - total) <= tolerancia for factor in FACTORES_DEL_TOTAL):
        return True
    descuentos = (Decimal(0), *porcentajes)
    ivas = (Decimal(0), *porcentajes)
    return any(
        abs(base * (1 - descuento / CIEN) * (1 + iva / CIEN) - total) <= tolerancia
        for descuento in descuentos
        for iva in ivas
        if descuento or iva
    )


def _elegir_cifras(numericas: list[tuple[int, Decimal]]):
    """Busca qué números del renglón son cantidad, unitario y total.

    El total es el de más a la derecha de los tres; cantidad y unitario pueden
    venir en cualquier orden. Si varios tríos cuadran gana el que tiene la
    cantidad menor que el unitario, luego cantidad entera, luego el total más a
    la derecha. Devuelve `(cantidad, unitario, total, posiciones)` o `None`.
    """
    mejor = None
    cuantas = len(numericas)
    for i in range(cuantas):
        for j in range(i + 1, cuantas):
            for k in range(j + 1, cuantas):
                for primero, segundo in ((i, j), (j, i)):
                    (pos_c, cantidad), (pos_u, unitario), (pos_t, total) = (
                        numericas[primero],
                        numericas[segundo],
                        numericas[k],
                    )
                    otros = tuple(
                        valor
                        for posicion, (_, valor) in enumerate(numericas)
                        if posicion not in (primero, segundo, k) and 0 < valor <= CIEN
                    )
                    if not _cuadra(cantidad, unitario, total, otros):
                        continue
                    clave = (
                        int(cantidad <= unitario),
                        int(cantidad == cantidad.to_integral_value()),
                        k,
                    )
                    if mejor is None or clave > mejor[0]:
                        mejor = (clave, (cantidad, unitario, total, {pos_c, pos_u, pos_t}))
    return mejor[1] if mejor else None


def separar_codigo_inicial(descripcion: str) -> tuple[str, str]:
    """`"MP-0141 Cerveza Águila"` → `("MP-0141", "Cerveza Águila")`.

    Un número de renglón antes del código se descarta: `"6 MP-0121 Hielo"`.
    """
    texto = descripcion.strip()
    primero, _, resto = texto.partition(" ")
    if _NUMERO_DE_RENGLON.match(primero) and resto.strip():
        texto = resto.strip()
        primero, _, resto = texto.partition(" ")
    if resto.strip() and _CODIGO_INICIAL.match(normalizar_factura(primero)):
        return primero, resto.strip()
    return "", texto


def _leer_renglon(renglon: str) -> LineaLeida | None:
    fichas = renglon.split()
    numericas = [
        (posicion, valor)
        for posicion, ficha in enumerate(fichas)
        if (valor := _leer_numero(ficha)) is not None
    ]
    cifras = _elegir_cifras(numericas)
    if cifras is None:
        return None
    cantidad, unitario, total, posiciones = cifras
    primera_cifra = min(posiciones)
    descripcion = " ".join(fichas[:primera_cifra]).strip()
    codigo, descripcion = separar_codigo_inicial(descripcion)
    if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{2}", descripcion):
        return None
    return LineaLeida(descripcion, cantidad, unitario, total, codigo)


def _leer_lineas(renglones: list[str]) -> list[LineaLeida]:
    inicio = next(
        (
            i + 1
            for i, r in enumerate(renglones)
            if _ENCABEZADO_DE_TABLA.search(normalizar_factura(r))
        ),
        0,
    )
    lineas: list[LineaLeida] = []
    for renglon in renglones[inicio:]:
        normalizado = normalizar_factura(renglon)
        if _INICIO_DEL_RESUMEN.match(normalizado):
            if lineas:
                break
            continue
        leida = _leer_renglon(renglon)
        if leida is not None:
            lineas.append(leida)
            continue
        # Un renglón de solo palabras bajo un producto es el resto de su nombre.
        if (
            lineas
            and len(renglon) <= 60
            and not any(_leer_numero(f) is not None for f in renglon.split())
            and not _ENCABEZADO_DE_TABLA.search(normalizado)
        ):
            lineas[-1].descripcion = f"{lineas[-1].descripcion} {renglon}".strip()
    return lineas


def _nombre_del_proveedor(renglones: list[str]) -> str:
    for renglon in renglones[:8]:
        if _SUFIJO_DE_EMPRESA.search(normalizar_factura(renglon)):
            return renglon.strip()[:150]
    return ""


def extraer_renglones(contenido: bytes) -> list[str]:
    if not contenido.startswith(b"%PDF"):
        raise FacturaIlegible("El archivo no es un PDF.")
    try:
        lector = PdfReader(io.BytesIO(contenido))
        if lector.is_encrypted:
            raise FacturaIlegible("El PDF está protegido con contraseña.")
        texto = "\n".join(
            (pagina.extract_text() or "") for pagina in lector.pages[:MAXIMO_DE_PAGINAS]
        )
    except PdfReadError as error:
        raise FacturaIlegible(
            "No se pudo abrir el archivo: parece dañado o no es un PDF."
        ) from error

    renglones = [re.sub(r"\s+", " ", r).strip() for r in texto.splitlines()]
    renglones = [r for r in renglones if r]
    if sum(len(r) for r in renglones) < CARACTERES_MINIMOS:
        raise FacturaIlegible(
            "Este PDF no trae texto: parece un escaneo o una foto. "
            "Sube la factura electrónica original."
        )
    return renglones


def leer_factura(renglones: list[str]) -> FacturaLeida:
    unido = " \n".join(normalizar_factura(r) for r in renglones)
    nit = _NIT.search(unido)
    numero = _NUMERO_FACTURA.search(unido) or _NUMERO_FACTURA_SUELTO.search(unido)
    return FacturaLeida(
        numero_factura=re.sub(r"\s+", "", numero[1])[:50] if numero else "",
        nit=re.sub(r"[^\d-]", "", nit[1]) if nit else "",
        nombre_proveedor=_nombre_del_proveedor(renglones),
        lineas=_leer_lineas(renglones),
    )
