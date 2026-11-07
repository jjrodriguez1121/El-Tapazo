"""Traducción JSON ↔ Python de la app `usuarios`.

Entrada y salida están separadas a propósito: lo que se recibe no tiene por
qué coincidir con lo que se devuelve. Aquí solo se valida **formato** —que el
campo venga, que sea un correo, que no pase de tantos caracteres—. Las reglas
de negocio están en `validadores/` y `servicios/`.

Los nombres de los campos van en español, como todo lo demás, y son el
contrato con el frontend: ver `docs/guias/guia-api-autenticacion.md`.
"""

from rest_framework import serializers

from usuarios.models import Invitacion, Rol, Usuario

LARGO_MAXIMO_CONTRASENA = 128


# --------------------------------------------------------------------------- #
# Salida
# --------------------------------------------------------------------------- #
class NegocioResumidoSerializer(serializers.Serializer):
    """Lo mínimo del negocio para pintar el encabezado de la aplicación."""

    id = serializers.IntegerField(read_only=True)
    nombre_comercial = serializers.CharField(read_only=True)


class UsuarioOutputSerializer(serializers.ModelSerializer):
    """Quién es el usuario. Nunca sale de aquí nada parecido a una contraseña."""

    nombre_completo = serializers.CharField(read_only=True)
    es_administrador = serializers.BooleanField(read_only=True)
    negocio = NegocioResumidoSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = (
            "id",
            "correo",
            "nombre",
            "apellido",
            "nombre_completo",
            "telefono",
            "rol",
            "es_administrador",
            "negocio",
            "correo_verificado_en",
            "fecha_alta",
        )


class SesionOutputSerializer(serializers.Serializer):
    """Lo que devuelve iniciar sesión: los dos tokens y quién entró."""

    acceso = serializers.CharField(read_only=True, source="token_de_acceso")
    refresco = serializers.CharField(read_only=True, source="token_de_refresco")
    usuario = UsuarioOutputSerializer(read_only=True)


class TokensOutputSerializer(serializers.Serializer):
    """Lo que devuelve renovar la sesión."""

    acceso = serializers.CharField(read_only=True)
    refresco = serializers.CharField(read_only=True)


class InvitacionOutputSerializer(serializers.ModelSerializer):
    """Una invitación vista por el administrador que la envió.

    El `hash_token` no aparece: no le sirve a nadie y es lo único que hay que
    proteger de esta tabla.
    """

    creada_por = serializers.CharField(source="creada_por.nombre_completo", read_only=True)
    esta_pendiente = serializers.BooleanField(read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invitacion
        fields = (
            "id",
            "correo",
            "rol",
            "creada_por",
            "expira_en",
            "aceptada_en",
            "esta_pendiente",
            "esta_vencida",
            "creado_en",
        )


class InvitacionPendienteOutputSerializer(serializers.Serializer):
    """Lo que ve quien abre el enlace, antes de aceptar.

    Solo lo necesario para que reconozca la invitación —"te invitaron a tal
    negocio como mesero"— y sepa que no se equivocó de enlace.
    """

    correo = serializers.EmailField(read_only=True)
    rol = serializers.CharField(read_only=True)
    negocio = serializers.CharField(source="negocio.nombre_comercial", read_only=True)
    expira_en = serializers.DateTimeField(read_only=True)


# --------------------------------------------------------------------------- #
# Entrada
# --------------------------------------------------------------------------- #
class InicioDeSesionInputSerializer(serializers.Serializer):
    correo = serializers.EmailField(max_length=150)
    contrasena = serializers.CharField(max_length=LARGO_MAXIMO_CONTRASENA, trim_whitespace=False)


class RefrescoInputSerializer(serializers.Serializer):
    refresco = serializers.CharField()


class CorreoInputSerializer(serializers.Serializer):
    """Lo único que se pide para recuperar la contraseña o reenviar la verificación."""

    correo = serializers.EmailField(max_length=150)


class EnlaceInputSerializer(serializers.Serializer):
    """Las dos piezas que viajan en un enlace del correo."""

    uid = serializers.CharField(max_length=32)
    token = serializers.CharField(max_length=128)


class NuevaContrasenaInputSerializer(EnlaceInputSerializer):
    contrasena = serializers.CharField(max_length=LARGO_MAXIMO_CONTRASENA, trim_whitespace=False)


class CambioDeContrasenaInputSerializer(serializers.Serializer):
    contrasena_actual = serializers.CharField(
        max_length=LARGO_MAXIMO_CONTRASENA, trim_whitespace=False
    )
    contrasena_nueva = serializers.CharField(
        max_length=LARGO_MAXIMO_CONTRASENA, trim_whitespace=False
    )


class InvitacionInputSerializer(serializers.Serializer):
    """El negocio no se pide: sale del administrador autenticado."""

    correo = serializers.EmailField(max_length=150)
    rol = serializers.ChoiceField(choices=Rol.choices)


class AceptacionDeInvitacionInputSerializer(serializers.Serializer):
    """El correo y el rol no se piden: los puso quien invitó."""

    token = serializers.CharField(max_length=128)
    nombre = serializers.CharField(max_length=120)
    apellido = serializers.CharField(max_length=120)
    telefono = serializers.CharField(max_length=20, allow_blank=True, default="")
    contrasena = serializers.CharField(max_length=LARGO_MAXIMO_CONTRASENA, trim_whitespace=False)


class TokenInputSerializer(serializers.Serializer):
    """El token de una invitación, que llega en la query de la URL."""

    token = serializers.CharField(max_length=128)
