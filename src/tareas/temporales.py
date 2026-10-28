"""Detecta ficheros temporales antiguos y los envía a la papelera."""

from __future__ import annotations

import time
from pathlib import Path

from .capturas import enviar_a_papelera
from .errores import TareasError

EXTENSIONES = {
    ".tmp",
    ".temp",
    ".bak",
    ".old",
    ".part",
    ".partial",
    ".crdownload",
    ".download",
    ".swp",
    ".swo",
}
NOMBRES = {".ds_store", "thumbs.db"}
PREFIJOS = ("~$",)
DIAS_POR_DEFECTO = 30


def es_temporal(ruta: Path) -> bool:
    """Indica si el nombre parece de un fichero temporal o de respaldo."""
    nombre = ruta.name.lower()
    return (
        ruta.suffix.lower() in EXTENSIONES
        or nombre in NOMBRES
        or nombre.endswith("~")
        or any(nombre.startswith(prefijo) for prefijo in PREFIJOS)
    )


def seleccionar(carpeta: Path, dias: int) -> list[Path]:
    """Devuelve los temporales del primer nivel con al menos los días indicados."""
    if dias < 1:
        raise TareasError("Los días deben ser 1 o más.")
    if not carpeta.is_dir():
        raise TareasError(f"La carpeta «{carpeta}» no existe o no es una carpeta.")

    limite = time.time() - dias * 86400
    try:
        entradas = sorted(
            carpeta.iterdir(),
            key=lambda ruta: (ruta.name.lower(), ruta.name),
        )
    except OSError as exc:
        raise TareasError(f"No se puede leer la carpeta «{carpeta}»: {exc}") from None

    ficheros: list[Path] = []
    for ruta in entradas:
        try:
            if ruta.is_symlink() or not ruta.is_file():
                continue
            if not es_temporal(ruta):
                continue
            datos = ruta.stat()
        except OSError:
            continue
        if datos.st_mtime > limite:
            continue
        ficheros.append(ruta)
    return ficheros
