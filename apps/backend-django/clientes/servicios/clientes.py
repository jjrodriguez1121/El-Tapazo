"""Alta, cambio y baja de fichas de cliente."""

from clientes.dtos import DatosDeClienteDTO
from clientes.excepciones import DocumentoDuplicado
from clientes.models import Cliente
from clientes.repositorios import clientes as repositorio
from clientes.selectores import obtener_cliente
from clientes.validadores import validar_fecha_de_nacimiento


def registrar_cliente(*, negocio_id: int, datos: DatosDeClienteDTO) -> Cliente:
    """Crea la ficha de una persona que compra en el bar.

    **Ser menor de edad no impide crear la ficha** (decisión 7): el sistema
    avisa y la pantalla lo pinta en rojo, pero quien decide si se le vende es
    la persona de la barra.

    Raises:
        FechaDeNacimientoInvalida: la fecha es imposible.
        DocumentoDuplicado: ya hay una ficha con ese documento.
    """
    validar_fecha_de_nacimiento(datos.fecha_nacimiento)
    campos = _limpiar(datos)
    if repositorio.existe_documento(
        negocio_id=negocio_id,
        tipo_documento=campos["tipo_documento"],
        numero_documento=campos["numero_documento"],
    ):
        raise DocumentoDuplicado
    return repositorio.crear(negocio_id=negocio_id, datos=campos)


def actualizar_cliente(*, cliente_id: int, negocio_id: int, datos: DatosDeClienteDTO) -> Cliente:
    """Corrige los datos de una ficha, documento incluido.

    Raises:
        NoEncontradoEnEsteNegocio, FechaDeNacimientoInvalida, DocumentoDuplicado.
    """
    cliente = obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    validar_fecha_de_nacimiento(datos.fecha_nacimiento)
    campos = _limpiar(datos)
    if repositorio.existe_documento(
        negocio_id=negocio_id,
        tipo_documento=campos["tipo_documento"],
        numero_documento=campos["numero_documento"],
        excluyendo_id=cliente_id,
    ):
        raise DocumentoDuplicado

    for campo, valor in campos.items():
        setattr(cliente, campo, valor)
    cliente.save(update_fields=[*campos, "actualizado_en"])
    return cliente


def desactivar_cliente(*, cliente_id: int, negocio_id: int) -> Cliente:
    """Saca la ficha de las búsquedas sin borrarla.

    Borrarla dejaría huérfanas sus cuentas y sus comandas, que es justo el
    historial por el que la ficha existe.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    cliente = obtener_cliente(cliente_id=cliente_id, negocio_id=negocio_id)
    cliente.activo = False
    cliente.save(update_fields=["activo", "actualizado_en"])
    return cliente


def _limpiar(datos: DatosDeClienteDTO) -> dict:
    return {
        "tipo_documento": datos.tipo_documento,
        "numero_documento": datos.numero_documento.strip(),
        "nombre": datos.nombre.strip(),
        "apellido": datos.apellido.strip(),
        "fecha_nacimiento": datos.fecha_nacimiento,
        "telefono": datos.telefono.strip(),
        "correo": datos.correo.strip(),
        "notas": datos.notas.strip(),
    }
