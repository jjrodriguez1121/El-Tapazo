"""Alta, cambio y baja de proveedores."""

from catalogo.excepciones import NitDeProveedorDuplicado
from catalogo.models import Proveedor
from catalogo.repositorios import proveedores as repositorio
from catalogo.selectores import obtener_proveedor

# Lo que se puede escribir de un proveedor. La razón social va aparte porque es
# obligatoria; el resto puede ir vacío.
CAMPOS_OPCIONALES = (
    "nit",
    "nombre_contacto",
    "telefono",
    "correo",
    "ciudad",
    "direccion",
)


def crear_proveedor(*, negocio_id: int, razon_social: str, **opcionales: str) -> Proveedor:
    """Registra una empresa a la que se le compra mercancía.

    Raises:
        NitDeProveedorDuplicado: ya hay uno con ese NIT. Sin NIT nunca choca.
    """
    datos = _limpiar(razon_social=razon_social, **opcionales)
    if repositorio.existe_nit(negocio_id=negocio_id, nit=datos["nit"]):
        raise NitDeProveedorDuplicado
    return repositorio.crear(negocio_id=negocio_id, datos=datos)


def actualizar_proveedor(
    *, proveedor_id: int, negocio_id: int, razon_social: str, **opcionales: str
) -> Proveedor:
    """Raises: NoEncontradoEnEsteNegocio, NitDeProveedorDuplicado."""
    proveedor = obtener_proveedor(proveedor_id=proveedor_id, negocio_id=negocio_id)
    datos = _limpiar(razon_social=razon_social, **opcionales)
    if repositorio.existe_nit(negocio_id=negocio_id, nit=datos["nit"], excluyendo_id=proveedor_id):
        raise NitDeProveedorDuplicado

    for campo, valor in datos.items():
        setattr(proveedor, campo, valor)
    proveedor.save(update_fields=[*datos, "actualizado_en"])
    return proveedor


def desactivar_proveedor(*, proveedor_id: int, negocio_id: int) -> Proveedor:
    """Deja de aparecer para comprarle, sin borrar las compras que ya se le hicieron.

    Raises:
        NoEncontradoEnEsteNegocio.
    """
    proveedor = obtener_proveedor(proveedor_id=proveedor_id, negocio_id=negocio_id)
    proveedor.activo = False
    proveedor.save(update_fields=["activo", "actualizado_en"])
    return proveedor


def _limpiar(*, razon_social: str, **opcionales: str) -> dict:
    datos = {"razon_social": razon_social.strip()}
    for campo in CAMPOS_OPCIONALES:
        datos[campo] = opcionales.get(campo, "").strip()
    return datos
