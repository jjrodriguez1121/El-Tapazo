"""Pruebas de `invitar_administrador`, la puerta del primer administrador de un negocio."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from negocios.pruebas.fabricas import FabricaDeNegocio
from usuarios.models import Invitacion, Rol
from usuarios.pruebas.fabricas import FabricaDeStaffDePlataforma, FabricaDeUsuario

pytestmark = pytest.mark.django_db


def invitar(**opciones) -> None:
    call_command("invitar_administrador", stdout=StringIO(), **opciones)


def test_invita_como_administrador_al_negocio_indicado():
    FabricaDeStaffDePlataforma()
    negocio = FabricaDeNegocio()

    invitar(negocio=negocio.pk, correo="ana@bar.test")

    invitacion = Invitacion.objects.get(correo="ana@bar.test")
    assert invitacion.negocio == negocio
    assert invitacion.rol == Rol.ADMINISTRADOR


def test_con_un_negocio_que_no_existe_explica_como_crearlo_en_vez_de_reventar():
    FabricaDeStaffDePlataforma()

    with pytest.raises(CommandError, match="No hay ningún negocio con el id 999999"):
        invitar(negocio=999999, correo="ana@bar.test")

    assert not Invitacion.objects.exists()


def test_con_un_correo_que_ya_tiene_cuenta_lo_dice_sin_traza():
    FabricaDeStaffDePlataforma()
    negocio = FabricaDeNegocio()
    existente = FabricaDeUsuario()

    with pytest.raises(CommandError, match="Ya existe un usuario con ese correo"):
        invitar(negocio=negocio.pk, correo=existente.correo)
