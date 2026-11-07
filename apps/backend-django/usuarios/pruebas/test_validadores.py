"""Pruebas de la regla de contraseñas: seis caracteres, con letras y números."""

import pytest

from usuarios.excepciones import ContrasenaInsegura
from usuarios.validadores.contrasenas import (
    MENSAJE_SIN_LETRAS,
    MENSAJE_SIN_NUMEROS,
    validar_contrasena,
)


def test_acepta_seis_caracteres_con_letras_y_numeros():
    validar_contrasena(contrasena="bar123")


def test_acepta_letras_con_tilde_y_enie():
    validar_contrasena(contrasena="ñandú7")


def test_rechaza_una_contrasena_de_menos_de_seis_caracteres():
    with pytest.raises(ContrasenaInsegura) as error:
        validar_contrasena(contrasena="bar12")

    assert len(error.value.detalles["errores"]) == 1


def test_rechaza_una_contrasena_sin_numeros():
    with pytest.raises(ContrasenaInsegura) as error:
        validar_contrasena(contrasena="tapaso")

    assert error.value.detalles["errores"] == [MENSAJE_SIN_NUMEROS]


def test_rechaza_una_contrasena_sin_letras():
    with pytest.raises(ContrasenaInsegura) as error:
        validar_contrasena(contrasena="123456")

    assert error.value.detalles["errores"] == [MENSAJE_SIN_LETRAS]


def test_devuelve_todos_los_motivos_de_una_vez():
    with pytest.raises(ContrasenaInsegura) as error:
        validar_contrasena(contrasena="!!")

    assert len(error.value.detalles["errores"]) == 3
