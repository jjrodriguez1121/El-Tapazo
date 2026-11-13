"""Normalización de texto para buscar productos en la pregunta del usuario."""

import re
import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con un solo espacio entre palabras."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "")
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).strip()


def palabras(texto: str) -> list[str]:
    return normalizar(texto).split()
