"""Calcula un resumen de solo lectura de una carpeta."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .capturas import es_captura
from .errores import TareasError


@dataclass(frozen=True)
class Fichero:
    """Datos mínimos de un fichero para el informe."""

    ruta: Path
    tamano: int
    modificado: float


@dataclass(frozen=True)
class Tipo:
    """Resumen de los ficheros que comparten extensión."""

    extension: str
    ficheros: int
    tamano: int


@dataclass(frozen=True)
class Resumen:
    """Todo lo que necesita la orden informe para pintar la salida."""

    ruta: Path
    ficheros: int
    carpetas: int
    tamano: int
    tipos: list[Tipo]
    capturas: int
    capturas_pendientes: int
    mas_antiguos: list[Fichero]
    mas_grandes: list[Fichero]


def analizar(carpeta: Path, top: int = 5, horas: int = 5) -> Resumen:
    """Recorre el primer nivel de la carpeta y devuelve sus datos."""
    if not carpeta.is_dir():
        raise TareasError(f"La carpeta «{carpeta}» no existe o no es una carpeta.")

    try:
        entradas = list(carpeta.iterdir())
    except OSError as exc:
        raise TareasError(f"No se puede leer la carpeta «{carpeta}»: {exc}") from None

    ficheros: list[Fichero] = []
    carpetas = 0
    for ruta in entradas:
        try:
            if ruta.is_symlink():
                continue
            if ruta.is_dir():
                carpetas += 1
                continue
            if not ruta.is_file():
                continue
            datos = ruta.stat()
        except OSError:
            continue
        ficheros.append(Fichero(ruta, datos.st_size, datos.st_mtime))

    por_tipo: dict[str, list[int]] = {}
    for fichero in ficheros:
        extension = fichero.ruta.suffix.lower() or "(sin extensión)"
        datos = por_tipo.setdefault(extension, [0, 0])
        datos[0] += 1
        datos[1] += fichero.tamano

    tipos = [
        Tipo(extension, datos[0], datos[1])
        for extension, datos in por_tipo.items()
    ]
    tipos.sort(key=lambda tipo: (-tipo.tamano, tipo.extension))

    limite = time.time() - horas * 3600
    capturas = [fichero for fichero in ficheros if es_captura(fichero.ruta)]
    pendientes = sum(fichero.modificado <= limite for fichero in capturas)

    return Resumen(
        ruta=carpeta,
        ficheros=len(ficheros),
        carpetas=carpetas,
        tamano=sum(fichero.tamano for fichero in ficheros),
        tipos=tipos[:top],
        capturas=len(capturas),
        capturas_pendientes=pendientes,
        mas_antiguos=sorted(
            ficheros,
            key=lambda fichero: (fichero.modificado, fichero.ruta.name.lower()),
        )[:top],
        mas_grandes=sorted(
            ficheros,
            key=lambda fichero: (-fichero.tamano, fichero.ruta.name.lower()),
        )[:top],
    )
