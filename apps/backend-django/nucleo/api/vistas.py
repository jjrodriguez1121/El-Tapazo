"""Piezas de la capa HTTP que comparten todas las apps."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request


class MixinDelNegocio:
    """Expone `self.negocio_id`: el negocio de quien hace la petición.

    **Este es el único sitio del que sale un `negocio_id`.** Nunca se toma de
    la URL ni del cuerpo de la petición: si el cliente lo manda, se ignora. Es
    lo que impide que alguien lea o toque los datos de otro negocio cambiando
    un id (*IDOR*), y por eso conviene que haya un solo punto que auditar.

    Las vistas se lo pasan tal cual a los servicios y selectores, que lo
    reciben como argumento obligatorio y lo meten en el `filter()`.
    """

    request: Request

    @property
    def negocio_id(self) -> int:
        usuario = self.request.user
        negocio_id = getattr(usuario, "negocio_id", None)
        if not negocio_id:
            # El staff de la plataforma no pertenece a ningún negocio. Sin este
            # freno la consulta filtraría por `NULL` —que no devuelve nada— y
            # una escritura acabaría en `IntegrityError`, o sea un 500 donde lo
            # correcto es un 403.
            raise PermissionDenied("Esta operación es de un negocio, y tu cuenta no tiene uno.")
        return negocio_id
