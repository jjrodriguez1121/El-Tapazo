"""Alta, cambio y baja de las tiendas cliente."""

from distribucion.dtos import DatosDeClienteDistribucionDTO
from distribucion.excepciones import NitDuplicado
from distribucion.models import ClienteDistribucion
from distribucion.repositorios import clientes as repositorio
from distribucion.selectores import obtener_cliente


def registrar_cliente(
    *, negocio_id: int, datos: DatosDeClienteDistribucionDTO
) -> ClienteDistribucion:
    """Da de alta una tienda a la que se le va a vender al por mayor.

    Raises:
        NitDuplicado: ya hay una tienda con ese NIT en el negocio.
    """
    campos = _limpiar(datos)
    if repositorio.existe_nit(negocio_id=negocio_id, nit=campos["nit"]):
        raise NitDuplicado
    return repositorio.crear(negocio_id=negocio_id, datos=campos)


def actualizar_cliente(
    *, cliente_id: int, negocio_id: int, datos: DatosDeClienteDistribucionDTO
) -> ClienteDistribucion:
    """Corrige la ficha de una tienda, NIT y plazo de crédito incluidos.

    Cambiar `dias_credito` cambia el vencimiento de los pedidos que ya estaban
    entregados y sin pagar: el plazo es de la tienda, no una foto del momento
    de vender. Si mañana se le amplía el crédito a 45 días, deja de estar en
    mora — que es justo lo que se quiere decir al ampliárselo.

    Raises:
        NoEncontradoEnEsteNegocio, NitDuplicado.
    """
    cliente = obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    campos = _limpiar(datos)
    if repositorio.existe_nit(negocio_id=negocio_id, nit=campos["nit"], excluyendo_id=cliente_id):
        raise NitDuplicado

    for campo, valor in campos.items():
        setattr(cliente, campo, valor)
    cliente.save(update_fields=[*campos, "actualizado_en"])
    return cliente


def desactivar_cliente(*, cliente_id: int, negocio_id: int) -> ClienteDistribucion:
    """Saca la tienda de las listas sin borrarla.

    Borrarla dejaría huérfanos sus pedidos históricos, que son justo lo que
    dice cuánto debe y cuánto compró.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    cliente = obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    cliente.activo = False
    cliente.save(update_fields=["activo", "actualizado_en"])
    return cliente


def _limpiar(datos: DatosDeClienteDistribucionDTO) -> dict:
    return {
        "razon_social": datos.razon_social.strip(),
        "nit": datos.nit.strip(),
        "nombre_contacto": datos.nombre_contacto.strip(),
        "telefono": datos.telefono.strip(),
        "correo": datos.correo.strip(),
        "ciudad": datos.ciudad.strip(),
        "direccion": datos.direccion.strip(),
        "dias_credito": datos.dias_credito,
    }
