"""Cruza los renglones de una factura con el catálogo del negocio.

Mismo criterio que el de GearShift: de lo más seguro a lo más flojo.

1. **Código**: el código impreso en el renglón (o una palabra de la descripción)
   es el SKU o el código de un producto, comparados sin espacios ni guiones.
2. **Parecido**: qué tanto se parece el texto completo del renglón al nombre
   del producto (`fuzz.ratio` y `fuzz.token_sort_ratio` sobre las palabras, sin
   las de relleno). No se usa una medida que dé 100 % por compartir una sola
   palabra.

- Desde `PARECIDO_PROBABLE` (60 %) el producto se **ofrece** y la persona decide.
- Al menos el 30 % de las palabras del renglón deben estar en el producto.
- Una medida distinta (330 contra 600) le resta 10 puntos, para que el de la
  medida correcta quede primero.
- **COINCIDE** es más estricto: 90 % de las palabras del renglón en el producto,
  índice de Dice de 0,85, sin medida distinta y con ventaja clara sobre el
  segundo. Mismo nombre (mismas palabras en cualquier orden) también coincide.
"""

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from compras.servicios.lector_factura_pdf import normalizar_factura

PARECIDO_PROBABLE = 0.6
COBERTURA_MINIMA = 0.3
CASTIGO_POR_MEDIDA = 0.10
COBERTURA_PARA_COINCIDIR = 0.9
DICE_PARA_COINCIDIR = 0.85
VENTAJA_PARA_COINCIDIR = 0.10
MAXIMO_DE_CANDIDATOS = 5
_PARECIDO_DE_ERRATA = 85
_LARGO_MINIMO_DE_ERRATA = 5
_LARGO_MINIMO_DE_PREFIJO = 3

COINCIDE = "COINCIDE"
PROBABLE = "PROBABLE"
NUEVO = "NUEVO"

#: Palabras que no dicen qué producto es.
_RELLENO = frozenset(
    {"DE", "DEL", "LA", "EL", "LOS", "LAS", "PARA", "CON", "SIN", "Y", "X", "POR", "EN", "A",
     "UN", "UNA", "UND", "UNID", "UNIDAD", "UNIDADES", "PZ", "PZA", "REF", "REFERENCIA"}
)  # fmt: skip

#: Abreviaturas que los proveedores de bebidas y abarrotes escriben igual en todas partes.
_ABREVIATURAS = {
    "CERV": "CERVEZA",
    "CERVE": "CERVEZA",
    "GASE": "GASEOSA",
    "GAS": "GASEOSA",
    "BOT": "BOTELLA",
    "BOTE": "BOTELLA",
    "MILILITROS": "ML",
    "LITRO": "L",
    "LITROS": "L",
    "LT": "L",
    "LTS": "L",
    "GRAMOS": "G",
    "GR": "G",
    "GRS": "G",
}

_SEPARADORES = re.compile(r"[^A-Z0-9]+")
_LETRA_DIGITO = re.compile(r"(?<=[A-Z])(?=\d)|(?<=\d)(?=[A-Z])")


def compactar_codigo(texto: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalizar_factura(texto))


def palabras(texto: str) -> list[str]:
    """Las palabras que dicen qué producto es.

    Mayúsculas sin tildes, letras y dígitos separados (`330ML` y `330 ml` son
    `330 ML`), abreviaturas comunes escritas completas y sin palabras de relleno
    ni letras sueltas. Las medidas (dígitos) se conservan.
    """
    resultado: list[str] = []
    for trozo in _SEPARADORES.split(normalizar_factura(texto)):
        for palabra in _LETRA_DIGITO.split(trozo):
            if not palabra or palabra in _RELLENO:
                continue
            if len(palabra) == 1 and not palabra.isdigit() and palabra != "L" and palabra != "G":
                continue
            resultado.append(_ABREVIATURAS.get(palabra, palabra))
    return resultado


def _misma_palabra(izquierda: str, derecha: str) -> bool:
    """Exacta, abreviada (`AGUI` → `AGUILA`) o con un error de tipeo."""
    if izquierda == derecha:
        return True
    if izquierda.isdigit() or derecha.isdigit():
        return False  # Una medida es exacta: 330 no es 350.
    corta, larga = sorted((izquierda, derecha), key=len)
    if len(corta) >= _LARGO_MINIMO_DE_PREFIJO and larga.startswith(corta):
        return True
    return (
        len(corta) >= _LARGO_MINIMO_DE_ERRATA
        and abs(len(izquierda) - len(derecha)) <= 2
        and fuzz.ratio(izquierda, derecha) >= _PARECIDO_DE_ERRATA
    )


@dataclass(slots=True)
class Comparacion:
    compartidas: int
    cobertura: float
    dice: float
    medida_distinta: bool


def comparar_palabras(renglon: list[str], producto: list[str]) -> Comparacion:
    libres = list(producto)
    compartidas = 0
    for palabra in renglon:
        for indice, candidata in enumerate(libres):
            if _misma_palabra(palabra, candidata):
                compartidas += 1
                del libres[indice]
                break
    medidas_renglon = {p for p in renglon if p.isdigit()}
    medidas_producto = {p for p in producto if p.isdigit()}
    distinta = bool(medidas_renglon - medidas_producto) and bool(medidas_producto - medidas_renglon)
    total = len(renglon) + len(producto)
    return Comparacion(
        compartidas=compartidas,
        cobertura=compartidas / len(renglon) if renglon else 0.0,
        dice=2 * compartidas / total if total else 0.0,
        medida_distinta=distinta,
    )


def parecido_de_texto(renglon: list[str], producto: list[str]) -> float:
    izquierda, derecha = " ".join(renglon), " ".join(producto)
    return max(fuzz.ratio(izquierda, derecha), fuzz.token_sort_ratio(izquierda, derecha)) / 100


@dataclass(slots=True)
class EntradaDelCatalogo:
    producto_id: int
    nombre: str
    codigos: tuple[str, ...] = ()
    _palabras: list[str] = field(default_factory=list)

    def __post_init__(self):
        self._palabras = palabras(self.nombre)


@dataclass(slots=True)
class Resultado:
    estado: str
    #: `(producto_id, puntaje 0-100)`, el mejor primero.
    candidatos: list[tuple[int, int]] = field(default_factory=list)


def _por_codigo(codigos_leidos: list[str], por_codigo: dict[str, set[int]]) -> set[int]:
    encontrados: set[int] = set()
    for codigo in codigos_leidos:
        compacto = compactar_codigo(codigo)
        if len(compacto) >= 3:
            encontrados |= por_codigo.get(compacto, set())
    return encontrados


def _puntajes_reales(ids, renglon: list[str], catalogo: dict[int, EntradaDelCatalogo]):
    puntuados = [
        (producto_id, round(parecido_de_texto(renglon, catalogo[producto_id]._palabras) * 100))
        for producto_id in ids
    ]
    return sorted(puntuados, key=lambda par: par[1], reverse=True)


def cruzar_renglon(
    descripcion: str,
    codigo: str,
    catalogo: dict[int, EntradaDelCatalogo],
    por_codigo: dict[str, set[int]],
) -> Resultado:
    renglon = palabras(descripcion)

    # 1. Código impreso, o una palabra de la descripción que es un SKU.
    con_codigo = _por_codigo([codigo, *descripcion.split()], por_codigo)
    if con_codigo:
        candidatos = _puntajes_reales(con_codigo, renglon, catalogo)[:MAXIMO_DE_CANDIDATOS]
        # El puntaje mostrado es el parecido real de los nombres, pero el código manda.
        return Resultado(COINCIDE if len(con_codigo) == 1 else PROBABLE, candidatos)

    if not renglon:
        return Resultado(NUEVO)

    # 2. Parecido del nombre.
    puntuados = []
    mismo_nombre = []
    for entrada in catalogo.values():
        producto = entrada._palabras
        if producto and sorted(renglon) == sorted(producto):
            mismo_nombre.append(entrada.producto_id)
        comparacion = comparar_palabras(renglon, producto)
        parecido = parecido_de_texto(renglon, producto)
        if parecido >= PARECIDO_PROBABLE and comparacion.cobertura >= COBERTURA_MINIMA:
            rango = parecido - (CASTIGO_POR_MEDIDA if comparacion.medida_distinta else 0.0)
            puntuados.append((rango, comparacion, entrada.producto_id))
    if not mismo_nombre and not puntuados:
        return Resultado(NUEVO)

    puntuados.sort(key=lambda item: (item[0], item[1].cobertura), reverse=True)
    mejores = puntuados[:MAXIMO_DE_CANDIDATOS]
    candidatos = [(producto_id, round(rango * 100)) for rango, _, producto_id in mejores]
    if mismo_nombre:
        otros = [c for c in candidatos if c[0] not in mismo_nombre]
        ofrecidos = [(producto_id, 100) for producto_id in mismo_nombre] + otros
        estado = COINCIDE if len(mismo_nombre) == 1 else PROBABLE
        return Resultado(estado, ofrecidos[:MAXIMO_DE_CANDIDATOS])

    mejor_rango, mejor, _ = mejores[0]
    segundo = mejores[1][0] if len(mejores) > 1 else 0.0
    if (
        mejor.cobertura >= COBERTURA_PARA_COINCIDIR
        and mejor.dice >= DICE_PARA_COINCIDIR
        and not mejor.medida_distinta
        and mejor_rango - segundo >= VENTAJA_PARA_COINCIDIR
    ):
        return Resultado(COINCIDE, candidatos)
    return Resultado(PROBABLE, candidatos)
