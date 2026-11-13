"""Busca en la web la foto de un producto y la deja lista para guardar.

Port del buscador de imágenes del catálogo de GearShift (GEA-95, GEA-195,
GEA-221, ADR-048), adaptado a El Tapaso:

- Busca gratis con la librería `ddgs` contra Bing, sin clave de API, con el
  mercado de Colombia (`mkt=es-CO&cc=CO`): ddgs no le pasa la región a Bing.
  Si con el mercado no llega nada, repite sin él.
- Descarta el contenido adulto por título y enlaces, y los resultados que no
  comparten ni una palabra con el producto.
- Ordena por relevancia: cuántas palabras del nombre aparecen en el título o
  en la ruta de la página; una guía o un artículo de blog va al final.
- A diferencia de GearShift, que guarda solo el enlace, aquí la imagen se
  **descarga** y se guarda como data URL JPEG cuadrada (así ya se guardan las
  fotos que sube el usuario): no depende de que el sitio de origen siga en pie
  ni deje enlazar sus fotos. Si una descarga falla se prueba con la siguiente.
"""

import base64
import io
import logging
import re
import unicodedata
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

REGION = "co-es"
TIEMPO_LIMITE = 12
#: Resultados que se piden al buscador: Bing devuelve una página de 35.
CANDIDATOS = 35
#: Cuántas fotos se intenta descargar antes de rendirse con un producto.
INTENTOS_DE_DESCARGA = 6
TAMANO_MAXIMO_DESCARGA = 6 * 1024 * 1024
LADO_DE_LA_IMAGEN = 400
CALIDAD_JPEG = 82
LARGO_MAXIMO_DE_BUSQUEDA = 150
NAVEGADOR = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


class BuscadorNoDisponible(Exception):
    """El buscador falló (red, tiempo o respuesta ilegible)."""


class BuscadorLimitado(BuscadorNoDisponible):
    """El buscador está limitando las consultas por un rato."""


@dataclass(slots=True)
class ResultadoDeImagen:
    url_imagen: str
    url_miniatura: str
    titulo: str
    url_pagina: str


# --------------------------------------------------------------------------- #
# Reglas: contenido adulto y relevancia (image_search_rules de GearShift)
# --------------------------------------------------------------------------- #
_PALABRA = re.compile(r"[a-z0-9]+")

PREFIJOS_BLOQUEADOS = (
    "porn", "xxx", "desnud", "nude", "nudis", "erotic", "erotis", "hentai", "onlyfans", "nsfw",
    "lenceri", "lingerie", "tanga", "sexy", "sexo", "sexual", "playboy", "camgirl", "fetich",
    "fetish", "bdsm",
)  # fmt: skip
PALABRAS_BLOQUEADAS = frozenset({"sex", "milf", "culo", "tetas", "puta", "putas"})
DOMINIOS_BLOQUEADOS = (
    "porn", "xxx", "xvideos", "xhamster", "xnxx", "redtube", "onlyfans", "hentai", "eporner",
    "erome", "rule34", "chaturbate", "spankbang", "brazzers", "stripchat", "nsfw",
)  # fmt: skip
RELLENO = frozenset(
    {"de", "del", "la", "las", "el", "los", "para", "con", "y", "o", "u", "en", "por", "a", "al",
     "un", "una", "unos", "unas", "x"}
)  # fmt: skip
#: Títulos de guía o blog ("Cómo preparar un mojito…"): no son la foto del producto.
PALABRAS_DE_GUIA = frozenset(
    {"como", "guia", "tutorial", "consejos", "tips", "paso", "pasos", "tipos", "diferencias",
     "cuando", "video", "videos", "receta", "recetas"}
)  # fmt: skip
CASTIGO_DE_GUIA = 0.5
_PREFIJO_MINIMO = 4


def plegar(texto: str | None) -> str:
    """Minúsculas y sin tildes: "Águila" → "aguila"."""
    descompuesto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def palabras(texto: str | None) -> list[str]:
    return _PALABRA.findall(plegar(texto))


def es_adulto(titulo: str, *enlaces: str) -> bool:
    def palabra_bloqueada(palabra: str) -> bool:
        return palabra in PALABRAS_BLOQUEADAS or palabra.startswith(PREFIJOS_BLOQUEADOS)

    if any(palabra_bloqueada(p) for p in palabras(titulo)):
        return True
    for enlace in enlaces:
        host = plegar(urlsplit(enlace or "").hostname)
        if any(palabra_bloqueada(p) for p in palabras(enlace)) or any(
            parte in host for parte in DOMINIOS_BLOQUEADOS
        ):
            return True
    return False


def terminos(texto: str) -> list[str]:
    return [p for p in dict.fromkeys(palabras(texto)) if p not in RELLENO]


def _singular(palabra: str) -> str:
    return palabra[:-1] if len(palabra) > 3 and palabra.endswith("s") else palabra


def _coincide(termino: str, palabra: str) -> bool:
    if _singular(termino) == _singular(palabra):
        return True
    corta, larga = sorted((termino, palabra), key=len)
    return len(corta) >= _PREFIJO_MINIMO and larga.startswith(corta)


def relevancia(lista_de_terminos: list[str], titulo: str, *enlaces: str) -> float:
    """De 0 a 1: cuántos términos del producto muestra el resultado (título y rutas)."""
    if not lista_de_terminos:
        return 1.0
    vistas = set(palabras(titulo))
    for enlace in enlaces:
        vistas.update(palabras(urlsplit(enlace or "").path))
    halladas = sum(1 for t in lista_de_terminos if any(_coincide(t, p) for p in vistas))
    return halladas / len(lista_de_terminos)


def es_guia(titulo: str) -> bool:
    return any(p in PALABRAS_DE_GUIA for p in palabras(titulo))


# --------------------------------------------------------------------------- #
# Buscador: Bing a través de ddgs (DdgsImageProvider de GearShift)
# --------------------------------------------------------------------------- #
def mercado_de_bing(region: str) -> dict[str, str]:
    """`co-es` → `{"mkt": "es-CO", "cc": "CO"}`; `{}` si la región no sirve."""
    pais, _, idioma = region.strip().lower().partition("-")
    if len(pais) != 2 or len(idioma) != 2 or not (pais + idioma).isalpha() or pais == "wt":
        return {}
    return {"mkt": f"{idioma}-{pais.upper()}", "cc": pais.upper()}


def _motor_bing(mercado: dict[str, str]) -> Any:
    """El motor de imágenes de Bing de ddgs, con el mercado y el idioma agregados."""
    from ddgs.engines.bing_images import BingImages

    extra = dict(mercado)
    idioma = extra.get("mkt", "")
    aceptar = f"{idioma},{idioma.partition('-')[0]};q=0.9,en;q=0.8" if idioma else ""

    class BingConMercado(BingImages):
        def build_payload(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            carga: dict[str, Any] = super().build_payload(*args, **kwargs)
            carga.update(extra)
            return carga

        def request(self, *args: Any, **kwargs: Any) -> Any:
            if aceptar:
                kwargs["headers"] = {"Accept-Language": aceptar}
            respuesta = self.http_client.request(*args, **kwargs)
            return respuesta.text if respuesta.status_code == 200 else None

    return BingConMercado(timeout=TIEMPO_LIMITE)


def _a_resultado(fila: Any) -> ResultadoDeImagen:
    def valor(clave: str) -> str:
        dato = fila.get(clave) if isinstance(fila, dict) else getattr(fila, clave, None)
        return str(dato or "")

    return ResultadoDeImagen(valor("image"), valor("thumbnail"), valor("title"), valor("url"))


def buscar_en_bing(consulta: str) -> list[ResultadoDeImagen]:
    from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

    try:
        mercado = mercado_de_bing(REGION)
        filas = list(_motor_bing(mercado).search(consulta, region=REGION, safesearch="on") or [])
        if not filas and mercado:
            filas = list(_motor_bing({}).search(consulta, region=REGION, safesearch="on") or [])
    except RatelimitException as error:
        raise BuscadorLimitado(str(error)) from error
    except TimeoutException as error:
        raise BuscadorNoDisponible(f"tiempo agotado: {error}") from error
    except DDGSException as error:
        if "no results" in str(error).lower():
            return []
        raise BuscadorNoDisponible(str(error)) from error
    return [_a_resultado(fila) for fila in filas[:CANDIDATOS]]


def buscar_imagenes(nombre: str, buscador=buscar_en_bing) -> list[ResultadoDeImagen]:
    """Fotos para un producto, sin contenido adulto y las más relevantes primero."""
    consulta = " ".join(nombre.split())[:LARGO_MAXIMO_DE_BUSQUEDA]
    lista = terminos(consulta)
    utiles = []
    for orden, resultado in enumerate(buscador(consulta)):
        if not resultado.url_imagen.startswith(("http://", "https://")):
            continue
        enlaces = (resultado.url_pagina, resultado.url_imagen)
        if es_adulto(resultado.titulo, *enlaces):
            continue
        puntaje = relevancia(lista, resultado.titulo, *enlaces)
        if puntaje == 0:
            continue
        if es_guia(resultado.titulo):
            puntaje *= CASTIGO_DE_GUIA
        utiles.append((-puntaje, orden, resultado))
    return [resultado for *_, resultado in sorted(utiles, key=lambda t: (t[0], t[1]))]


# --------------------------------------------------------------------------- #
# Descarga y conversión a data URL
# --------------------------------------------------------------------------- #
def descargar(url: str) -> bytes:
    peticion = urllib.request.Request(
        url, headers={"User-Agent": NAVEGADOR, "Accept": "image/avif,image/webp,image/*,*/*"}
    )
    with urllib.request.urlopen(peticion, timeout=TIEMPO_LIMITE) as respuesta:  # noqa: S310
        tipo = respuesta.headers.get("Content-Type", "")
        if tipo and not tipo.startswith("image/"):
            raise ValueError(f"no es una imagen: {tipo}")
        datos = respuesta.read(TAMANO_MAXIMO_DESCARGA + 1)
    if len(datos) > TAMANO_MAXIMO_DESCARGA:
        raise ValueError("la imagen pesa demasiado")
    return datos


def a_data_url(contenido: bytes) -> str:
    """Cuadrada de 400 px sobre fondo blanco, en JPEG, como data URL."""
    imagen = Image.open(io.BytesIO(contenido))
    imagen.load()
    if imagen.mode in ("RGBA", "LA", "P"):
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGBA", imagen.size, (255, 255, 255, 255))
        fondo.alpha_composite(imagen)
        imagen = fondo
    imagen = imagen.convert("RGB")
    if min(imagen.size) < 80:
        raise ValueError("la imagen es demasiado pequeña")
    imagen.thumbnail((LADO_DE_LA_IMAGEN, LADO_DE_LA_IMAGEN))
    lienzo = Image.new("RGB", (LADO_DE_LA_IMAGEN, LADO_DE_LA_IMAGEN), (255, 255, 255))
    lienzo.paste(
        imagen,
        ((LADO_DE_LA_IMAGEN - imagen.width) // 2, (LADO_DE_LA_IMAGEN - imagen.height) // 2),
    )
    salida = io.BytesIO()
    lienzo.save(salida, format="JPEG", quality=CALIDAD_JPEG, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(salida.getvalue()).decode("ascii")


def foto_de_producto(nombre: str, buscador=buscar_en_bing, descargador=descargar) -> str | None:
    """La primera foto que se pueda descargar para *nombre*, como data URL; `None` si no hay.

    Raises:
        BuscadorNoDisponible: el buscador no respondió (o está limitando).
    """
    for resultado in buscar_imagenes(nombre, buscador)[:INTENTOS_DE_DESCARGA]:
        for url in (resultado.url_imagen, resultado.url_miniatura):
            if not url:
                continue
            try:
                return a_data_url(descargador(url))
            except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as e:
                logger.info("No se pudo usar la foto %s: %s", url[:120], e)
    return None
