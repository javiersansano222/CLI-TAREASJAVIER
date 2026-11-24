"""Busca ficheros por nombre dentro de una carpeta, de forma recursiva.

No toca nada: solo lee nombres. La orden de la CLI decide el formato de la
tabla; aquí se filtra y se ordena. Las rutas salen resueltas (``.resolve()``)
para que la CLI pueda calcular la relativa sin que le afecte un ``.``. Si el
usuario no dice dónde, se mira en la carpeta de descargas, que es donde suele
caer lo que se baja de internet.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .errores import TareasError
from .rutas import carpeta_descargas, resolver_carpeta

MAX_RESULTADOS = 200
OMITIDAS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
EXTENSION_DEFECTO = ""


@dataclass(frozen=True)
class Coincidencia:
    """Un fichero que pasa todos los filtros, con lo que hay que enseñar."""

    ruta: Path
    tamano: int
    modificado: float


def _coincide(nombre: str, patron: str, regex: bool) -> bool:
    if regex:
        return re.search(patron, nombre, re.IGNORECASE) is not None
    # Sin asteriscos, «documento» vale tanto para «documento.pdf» como para
    # «apuntes de documento.txt»: se comporta como una subcadena.
    if any(caracter in patron for caracter in "*?["):
        return fnmatch.fnmatch(nombre.lower(), patron.lower())
    return patron.lower() in nombre.lower()


def _extension_normalizada(extra: str) -> str:
    """Acepta «pdf», «.pdf» o «.PDF» y devuelve «.pdf»."""
    extra = extra.strip().lower()
    if not extra:
        return EXTENSION_DEFECTO
    if not extra.startswith("."):
        extra = "." + extra
    if len(extra) < 2:
        raise TareasError(
            f"«{extra}» no parece una extensión. Usa pdf, .pdf, .jpg, etc."
        )
    return extra


def carpeta_busqueda(carpeta: Path | None) -> Path:
    """Carpeta donde buscar: la pedida o, si no, la de descargas."""
    if carpeta is None:
        return carpeta_descargas()
    ruta = resolver_carpeta(carpeta)
    if not ruta.is_dir():
        raise TareasError(f"«{ruta}» no existe o no es una carpeta.")
    return ruta


def buscar(
    texto: str,
    carpeta: Path | None = None,
    extensiones: list[str] | None = None,
    regex: bool = False,
) -> list[Coincidencia]:
    """Encuentra ficheros cuyo nombre encaje con «texto» bajo «carpeta».

    Los resultados se ordenan por fecha (los nuevos primero) y se corta en
    MAX_RESULTADOS para no llenar la terminal.
    """
    limpio = texto.strip()
    if not limpio:
        raise TareasError(
            "Dime qué busco, por ejemplo «tareas buscar apuntes» o "
            "«tareas buscar foto --ext .jpg»."
        )
    if regex:
        try:
            re.compile(limpio)
        except re.error as exc:
            raise TareasError(
                f"La expresión regular «{limpio}» está mal: {exc.msg} "
                f"(posición {exc.pos})."
            ) from None

    extensiones_normales = [
        _extension_normalizada(ext) for ext in (extensiones or []) if ext
    ]

    coincidencias: list[Coincidencia] = []
    base = carpeta_busqueda(carpeta).resolve()
    try:
        for ruta in base.rglob("*"):
            try:
                if not ruta.is_file():
                    continue
            except OSError:
                continue

            partes = ruta.parts[len(base.parts) - 1 :]
            if any(parte in OMITIDAS for parte in partes[:-1]):
                continue

            nombre = ruta.name
            if extensiones_normales and ruta.suffix.lower() not in extensiones_normales:
                continue
            if not _coincide(nombre, limpio, regex):
                continue

            try:
                datos = ruta.stat()
            except OSError:
                continue
            coincidencias.append(
                Coincidencia(ruta=ruta, tamano=datos.st_size, modificado=datos.st_mtime)
            )
    except OSError:
        pass

    coincidencias.sort(key=lambda c: c.modificado, reverse=True)
    return coincidencias[:MAX_RESULTADOS]
