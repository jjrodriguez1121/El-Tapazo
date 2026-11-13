from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from asistente.servicios.catalogo import contexto_del_catalogo
from asistente.servicios.groq import ErrorDelAsistente, completar
from nucleo.permisos import EsDelEquipo

MAXIMO_DE_MENSAJES = 12

INSTRUCCIONES_DEL_CHAT = """\
Eres el asistente de El Tapaso, un sistema de ventas e inventario para negocios en Colombia.
Respondes en español, de forma breve y clara, a {nombre} (rol: {rol}).
Hoy es {hoy}.

Este es el catálogo actual del negocio (precios en pesos colombianos):
{catalogo}

Reglas:
- Usa solo los datos del catálogo para hablar de productos, precios y stock. Si algo no está, dilo.
- Un producto está agotado si su stock disponible es 0, y por reponer si está en o por debajo del stock mínimo (cuando el mínimo es mayor que 0).
- No inventes productos, precios ni cantidades.
- Escribe texto plano o listas cortas con guiones. No uses tablas ni encabezados de Markdown; puedes usar **negrita**.
- Si te piden algo que no puedes hacer (registrar ventas, cambiar precios), explica en qué pantalla se hace.
"""


class MensajeSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=["usuario", "asistente"])
    contenido = serializers.CharField(max_length=2000, trim_whitespace=True)


class ChatSerializer(serializers.Serializer):
    mensajes = MensajeSerializer(many=True, allow_empty=False)

    def validate_mensajes(self, mensajes):
        if mensajes[-1]["rol"] != "usuario":
            raise serializers.ValidationError("El último mensaje debe ser del usuario.")
        return mensajes[-MAXIMO_DE_MENSAJES:]


@api_view(["POST"])
@permission_classes([EsDelEquipo])
def chat(request):
    entrada = ChatSerializer(data=request.data)
    entrada.is_valid(raise_exception=True)
    mensajes = entrada.validated_data["mensajes"]
    usuario = request.user

    sistema = INSTRUCCIONES_DEL_CHAT.format(
        nombre=usuario.nombre or usuario.correo,
        rol=usuario.get_rol_display(),
        hoy=timezone.localdate().isoformat(),
        catalogo=contexto_del_catalogo(usuario.negocio_id, mensajes[-1]["contenido"]),
    )
    conversacion = [{"role": "system", "content": sistema}] + [
        {"role": "user" if m["rol"] == "usuario" else "assistant", "content": m["contenido"]}
        for m in mensajes
    ]
    try:
        respuesta = completar(conversacion)
    except ErrorDelAsistente as error:
        return Response({"detail": str(error)}, status=503)
    return Response({"respuesta": respuesta})
