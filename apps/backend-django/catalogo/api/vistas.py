"""Capa HTTP del catálogo.

Cada vista recibe, delega y responde. Ninguna decide nada: las reglas están en
`catalogo/servicios/` y las consultas en `catalogo/selectores/`.

Todo el catálogo es **de administrador** (decisión 6 del plan de negocio): es
lo que cambia lo que el resto del equipo ve toda la noche. Y el negocio sale
siempre de `MixinDelNegocio`, nunca de la URL ni del cuerpo.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from catalogo.api import filtros, serializers
from catalogo.dtos import DatosDeProductoDTO
from catalogo.models import Categoria, Producto, Proveedor
from catalogo.selectores import productos as selector
from catalogo.servicios import categorias as servicio_de_categorias
from catalogo.servicios import ofertas as servicio_de_ofertas
from catalogo.servicios import productos as servicio
from catalogo.servicios import proveedores as servicio_de_proveedores
from nucleo.api.vistas import MixinDelNegocio
from nucleo.permisos import EsAdministrador


class _ViewSetDelCatalogo(
    MixinDelNegocio, mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    """Lo que comparten los tres recursos: permisos y de dónde sale el negocio."""

    permission_classes = [EsAdministrador]
    lookup_value_regex = "[0-9]+"


# --------------------------------------------------------------------------- #
# Categorías
# --------------------------------------------------------------------------- #
class CategoriaViewSet(_ViewSetDelCatalogo):
    """/api/v1/catalogo/categorias/"""

    serializer_class = serializers.CategoriaOutputSerializer
    filterset_class = filtros.CategoriaFiltro
    # Solo para que drf-spectacular sepa de qué modelo es el listado: el
    # queryset de verdad lo arma `get_queryset` con el negocio del usuario.
    queryset = Categoria.objects.none()

    def get_queryset(self):
        return selector.categorias_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar las categorías del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver una categoría")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Crear una categoría",
        request=serializers.CategoriaInputSerializer,
        responses={201: serializers.CategoriaOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        entrada = serializers.CategoriaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        categoria = servicio_de_categorias.crear_categoria(
            negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(
            serializers.CategoriaOutputSerializer(categoria).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Cambiar una categoría",
        request=serializers.CategoriaInputSerializer,
        responses={200: serializers.CategoriaOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        entrada = serializers.CategoriaInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        categoria = servicio_de_categorias.actualizar_categoria(
            categoria_id=int(pk), negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(serializers.CategoriaOutputSerializer(categoria).data)

    @extend_schema(
        summary="Desactivar una categoría",
        description="No se borra: los productos que ya la usan la siguen necesitando.",
        request=None,
        responses={200: serializers.CategoriaOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="desactivacion")
    def desactivacion(self, request: Request, pk: str) -> Response:
        categoria = servicio_de_categorias.desactivar_categoria(
            categoria_id=int(pk), negocio_id=self.negocio_id
        )
        return Response(serializers.CategoriaOutputSerializer(categoria).data)


# --------------------------------------------------------------------------- #
# Proveedores
# --------------------------------------------------------------------------- #
class ProveedorViewSet(_ViewSetDelCatalogo):
    """/api/v1/catalogo/proveedores/"""

    serializer_class = serializers.ProveedorOutputSerializer
    filterset_class = filtros.ProveedorFiltro
    queryset = Proveedor.objects.none()

    def get_queryset(self):
        return selector.proveedores_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar los proveedores del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver un proveedor")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Registrar un proveedor",
        request=serializers.ProveedorInputSerializer,
        responses={201: serializers.ProveedorOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        entrada = serializers.ProveedorInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        proveedor = servicio_de_proveedores.crear_proveedor(
            negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(
            serializers.ProveedorOutputSerializer(proveedor).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Cambiar un proveedor",
        request=serializers.ProveedorInputSerializer,
        responses={200: serializers.ProveedorOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        entrada = serializers.ProveedorInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        proveedor = servicio_de_proveedores.actualizar_proveedor(
            proveedor_id=int(pk), negocio_id=self.negocio_id, **entrada.validated_data
        )
        return Response(serializers.ProveedorOutputSerializer(proveedor).data)

    @extend_schema(
        summary="Desactivar un proveedor",
        request=None,
        responses={200: serializers.ProveedorOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="desactivacion")
    def desactivacion(self, request: Request, pk: str) -> Response:
        proveedor = servicio_de_proveedores.desactivar_proveedor(
            proveedor_id=int(pk), negocio_id=self.negocio_id
        )
        return Response(serializers.ProveedorOutputSerializer(proveedor).data)


# --------------------------------------------------------------------------- #
# Productos
# --------------------------------------------------------------------------- #
class ProductoViewSet(_ViewSetDelCatalogo):
    """/api/v1/catalogo/productos/"""

    serializer_class = serializers.ProductoOutputSerializer
    filterset_class = filtros.ProductoFiltro
    queryset = Producto.objects.none()

    def get_queryset(self):
        return selector.productos_del_negocio(negocio_id=self.negocio_id)

    @extend_schema(summary="Listar el catálogo del negocio")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Ver un producto")
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Crear un producto",
        request=serializers.ProductoInputSerializer,
        responses={201: serializers.ProductoOutputSerializer},
    )
    def create(self, request: Request) -> Response:
        entrada = serializers.ProductoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        producto = servicio.crear_producto(
            negocio_id=self.negocio_id,
            datos=DatosDeProductoDTO(**entrada.validated_data),
        )
        return Response(
            serializers.ProductoOutputSerializer(producto).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Cambiar un producto",
        request=serializers.ProductoInputSerializer,
        responses={200: serializers.ProductoOutputSerializer},
    )
    def update(self, request: Request, pk: str) -> Response:
        entrada = serializers.ProductoInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        producto = servicio.actualizar_producto(
            producto_id=int(pk),
            negocio_id=self.negocio_id,
            datos=DatosDeProductoDTO(**entrada.validated_data),
        )
        return Response(serializers.ProductoOutputSerializer(producto).data)

    @extend_schema(
        summary="Cambiar el precio de un producto",
        description="Va aparte del resto de datos porque queda registrado quién lo cambió.",
        request=serializers.CambioDePrecioInputSerializer,
        responses={200: serializers.ProductoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="precio")
    def precio(self, request: Request, pk: str) -> Response:
        entrada = serializers.CambioDePrecioInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        producto = servicio.cambiar_precio(
            producto_id=int(pk),
            negocio_id=self.negocio_id,
            usuario_id=request.user.id,
            **entrada.validated_data,
        )
        return Response(serializers.ProductoOutputSerializer(producto).data)

    @extend_schema(
        summary="Desactivar un producto",
        request=None,
        responses={200: serializers.ProductoOutputSerializer},
    )
    @action(detail=True, methods=["post"], url_path="desactivacion")
    def desactivacion(self, request: Request, pk: str) -> Response:
        producto = servicio.desactivar_producto(producto_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.ProductoOutputSerializer(producto).data)

    @extend_schema(
        summary="Ver el margen de venta",
        description="En porcentaje sobre el costo. `null` cuando el costo es cero.",
        responses={200: serializers.MargenDeVentaOutputSerializer},
    )
    @action(detail=True, methods=["get"], url_path="margen")
    def margen(self, request: Request, pk: str) -> Response:
        margen = selector.margen_de_venta(producto_id=int(pk), negocio_id=self.negocio_id)
        return Response(serializers.MargenDeVentaOutputSerializer(margen).data)

    @extend_schema(
        methods=["GET"],
        summary="Comparar el precio de cada proveedor",
        description="Del más barato al más caro: es para lo que existe esta lista.",
        responses={200: serializers.OfertaOutputSerializer(many=True)},
    )
    @extend_schema(
        methods=["POST"],
        summary="Registrar el precio de un proveedor",
        request=serializers.OfertaInputSerializer,
        responses={201: serializers.OfertaOutputSerializer},
    )
    @action(detail=True, methods=["get", "post"], url_path="proveedores")
    def proveedores(self, request: Request, pk: str) -> Response:
        if request.method == "POST":
            entrada = serializers.OfertaInputSerializer(data=request.data)
            entrada.is_valid(raise_exception=True)

            oferta = servicio_de_ofertas.asociar_proveedor_a_producto(
                producto_id=int(pk), negocio_id=self.negocio_id, **entrada.validated_data
            )
            return Response(
                serializers.OfertaOutputSerializer(oferta).data,
                status=status.HTTP_201_CREATED,
            )

        ofertas = selector.comparar_precios_de_proveedores(
            producto_id=int(pk), negocio_id=self.negocio_id
        )
        return Response(serializers.OfertaOutputSerializer(ofertas, many=True).data)

    @extend_schema(
        summary="Quitar el precio de un proveedor",
        description="Esta lista dice a quién se le puede comprar hoy; la historia de "
        "las compras vive en el kardex, así que aquí sí se borra la fila.",
        responses={204: None},
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"proveedores/(?P<proveedor_id>[0-9]+)",
    )
    def desasociar_proveedor(self, request: Request, pk: str, proveedor_id: str) -> Response:
        servicio_de_ofertas.desasociar_proveedor(
            producto_id=int(pk), proveedor_id=int(proveedor_id), negocio_id=self.negocio_id
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Marcar el proveedor habitual",
        description="Solo puede haber uno por producto: el anterior deja de serlo.",
        request=None,
        responses={200: serializers.OfertaOutputSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"proveedores/(?P<proveedor_id>[0-9]+)/principal",
    )
    def marcar_principal(self, request: Request, pk: str, proveedor_id: str) -> Response:
        oferta = servicio_de_ofertas.marcar_proveedor_principal(
            producto_id=int(pk), proveedor_id=int(proveedor_id), negocio_id=self.negocio_id
        )
        return Response(serializers.OfertaOutputSerializer(oferta).data)
