"""Reglas del buscador de fotos de producto (sin red: buscador y descarga falsos)."""

import io

from PIL import Image

from catalogo.servicios.imagenes_web import (
    ResultadoDeImagen,
    a_data_url,
    buscar_imagenes,
    es_adulto,
    foto_de_producto,
    mercado_de_bing,
    relevancia,
    terminos,
)


def _resultado(titulo, imagen="https://tienda.co/foto.jpg", pagina="https://tienda.co/p"):
    return ResultadoDeImagen(imagen, "", titulo, pagina)


def _jpeg(ancho=300, alto=200):
    salida = io.BytesIO()
    Image.new("RGB", (ancho, alto), (200, 30, 30)).save(salida, format="JPEG")
    return salida.getvalue()


def test_mercado_de_bing_para_colombia():
    assert mercado_de_bing("co-es") == {"mkt": "es-CO", "cc": "CO"}
    assert mercado_de_bing("wt-wt") == {}


def test_es_adulto_por_titulo_y_por_dominio():
    assert es_adulto("Lencería sexy roja")
    assert es_adulto("Botella", "https://www.xvideos.com/algo")
    assert not es_adulto("Cerveza Águila lata", "https://essex.ac.uk/foto")


def test_relevancia_lee_titulo_y_ruta_de_la_pagina():
    lista = terminos("Cerveza Águila Lata 330ml")
    assert relevancia(lista, "Cerveza Aguila lata 330ml") == 1
    assert relevancia(lista, "", "https://tienda.co/productos/cerveza-aguila") == 0.5
    assert relevancia(lista, "Calendario 2026") == 0


def test_buscar_imagenes_descarta_adulto_e_irrelevante_y_ordena():
    def buscador(_consulta):
        return [
            _resultado("Calendario de paisajes"),
            _resultado("Cómo servir una cerveza águila"),
            _resultado("Cerveza Águila lata 330ml"),
            _resultado("Cerveza sexy"),
        ]

    titulos = [r.titulo for r in buscar_imagenes("Cerveza Águila Lata 330ml", buscador)]
    assert titulos == ["Cerveza Águila lata 330ml", "Cómo servir una cerveza águila"]


def test_a_data_url_deja_un_jpeg_cuadrado():
    url = a_data_url(_jpeg())
    assert url.startswith("data:image/jpeg;base64,")


def test_foto_de_producto_prueba_la_siguiente_si_una_descarga_falla():
    def buscador(_consulta):
        return [
            _resultado("Ron Medellín 750ml", imagen="https://a.co/rota.jpg"),
            _resultado("Ron Medellín añejo 750ml", imagen="https://b.co/buena.jpg"),
        ]

    def descargador(url):
        if "rota" in url:
            raise OSError("404")
        return _jpeg()

    assert foto_de_producto("Ron Medellín 750ml", buscador, descargador).startswith("data:")


def test_foto_de_producto_sin_resultados_es_none():
    assert foto_de_producto("Algo", lambda _c: [], lambda _u: b"") is None
