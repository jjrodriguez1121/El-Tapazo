"""Lector de facturas en PDF y cruce de sus renglones con el catálogo (sin base de datos)."""

from decimal import Decimal

import pytest

from compras.servicios.coincidencias_factura import (
    COINCIDE,
    NUEVO,
    PROBABLE,
    EntradaDelCatalogo,
    cruzar_renglon,
    palabras,
)
from compras.servicios.lector_factura_pdf import (
    FacturaIlegible,
    extraer_renglones,
    leer_factura,
    leer_valor,
    separar_codigo_inicial,
)

FACTURA = [
    "DISTRIBUIDORA ANDINA S.A.S.",
    "NIT 900.123.456-7",
    "FACTURA ELECTRONICA DE VENTA No. FE-4521",
    "Cliente: El Tapaso",
    "Item Descripcion Cant V.Unit IVA% Total",
    "1 CER-0330 CERVEZA AGUILA LATA X 330 ML 48 2.100,00 19 119.952,00",
    "2 CERV POKER LT 330 24 2.050,00 49.200,00",
    "3 COCA-COLA PET 400ML 12 1.800,00 21.600,00",
    "4 BOLSA HIELO 5KG 3 4.000,00 12.000,00",
    "SUBTOTAL 183.600,00",
    "IVA 34.884,00",
    "TOTAL 218.484,00",
]

CATALOGO = {
    1: EntradaDelCatalogo(1, "Cerveza Águila Lata 330ml", ("CER-AGU-330",)),
    2: EntradaDelCatalogo(2, "Cerveza Poker Lata 330ml", ("CER-POK-330",)),
    3: EntradaDelCatalogo(3, "Gaseosa Coca Cola 400ml", ("GAS-COC-400",)),
    4: EntradaDelCatalogo(4, "Agua Cristal 600ml", ("AGU-CRI-600", "CRI600")),
}


def _por_codigo():
    return {"CERAGU330": {1}, "CERPOK330": {2}, "GASCOC400": {3}, "AGUCRI600": {4}, "CRI600": {4}}


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("12.500,50", Decimal("12500.50")),
        ("18,500.50", Decimal("18500.50")),
        ("100.800", Decimal("100800.00")),
        ("2,5", Decimal("2.50")),
        ("$1.800", Decimal("1800.00")),
        ("AGUILA", None),
    ],
)
def test_leer_valor_entiende_ambos_formatos(texto, esperado):
    assert leer_valor(texto) == esperado


def test_separar_codigo_inicial_quita_numero_de_renglon_y_codigo():
    assert separar_codigo_inicial("6 MP-0121 Bolsa de hielo") == ("MP-0121", "Bolsa de hielo")
    assert separar_codigo_inicial("Cerveza Aguila") == ("", "Cerveza Aguila")


def test_leer_factura_saca_encabezado_y_renglones_por_aritmetica():
    factura = leer_factura(FACTURA)

    assert factura.numero_factura == "FE-4521"
    assert factura.nit == "900123456-7"
    assert factura.nombre_proveedor == "DISTRIBUIDORA ANDINA S.A.S."
    assert [(linea.cantidad, linea.costo_unitario) for linea in factura.lineas] == [
        (Decimal("48.00"), Decimal("2100.00")),  # el total trae el IVA del 19 %
        (Decimal("24.00"), Decimal("2050.00")),
        (Decimal("12.00"), Decimal("1800.00")),
        (Decimal("3.00"), Decimal("4000.00")),
    ]
    assert factura.lineas[0].codigo == "CER-0330"
    assert factura.lineas[0].descripcion == "CERVEZA AGUILA LATA X 330 ML"


def test_gana_el_trio_que_cuadra_exacto():
    # 20 × 8.800 con 3 % de descuento y 24 % de "IVA" también da el total;
    # el trío exacto 24 × 8.800 = 211.200 debe ganar.
    factura = leer_factura(["3 CIGARRILLOS LUCKY STRIKE 20 UNIDADES 24 8.800,00 211.200,00"])

    linea = factura.lineas[0]
    assert (linea.cantidad, linea.costo_unitario) == (Decimal("24.00"), Decimal("8800.00"))
    assert linea.descripcion == "CIGARRILLOS LUCKY STRIKE 20 UNIDADES"


def test_palabras_separa_medidas_y_expande_abreviaturas():
    assert palabras("CERV POKER LT 330") == ["CERVEZA", "POKER", "L", "330"]
    assert palabras("Agua 600ml") == ["AGUA", "600", "ML"]


def test_cruce_por_nombre_parecido():
    resultado = cruzar_renglon("CERVEZA AGUILA LATA X 330 ML", "", CATALOGO, _por_codigo())
    assert resultado.estado in (COINCIDE, PROBABLE)
    assert resultado.candidatos[0][0] == 1


def test_cruce_por_codigo_manda_sobre_el_nombre():
    resultado = cruzar_renglon("AGUA BOTELLA", "CRI-600", CATALOGO, _por_codigo())
    assert resultado.estado == COINCIDE
    assert resultado.candidatos[0][0] == 4


def test_producto_que_no_esta_en_el_catalogo_es_nuevo():
    assert cruzar_renglon("BOLSA HIELO 5KG", "", CATALOGO, _por_codigo()).estado == NUEVO


def test_extraer_renglones_rechaza_lo_que_no_es_pdf():
    with pytest.raises(FacturaIlegible):
        extraer_renglones(b"no soy un pdf")
