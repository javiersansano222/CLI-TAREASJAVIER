"""Ordena los ficheros de una carpeta en subcarpetas según su tipo.

Solo mira el primer nivel: las subcarpetas (incluidas las que crea él mismo)
no se recorren, para no mover nunca una carpeta dentro de sí misma. Nunca
sobrescribe: si el destino ya existe, añade « (1)», « (2)»… al nombre.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .acciones import Resultado, destino_libre
from .errores import TareasError

# Extensiones de cada carpeta de destino, en minúsculas y con el punto.
CATEGORIAS: dict[str, tuple[str, ...]] = {
    "Documentos": (
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md",
        ".xls", ".xlsx", ".ods", ".csv",
        ".ppt", ".pptx", ".odp", ".odg", ".epub",
    ),
    "Imagenes": (
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        ".tif", ".tiff", ".svg", ".heic", ".raw", ".psd",
    ),
    "Videos": (
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        ".webm", ".m4v", ".mpg", ".mpeg",
    ),
    "Audio": (
        ".mp3", ".wav", ".flac", ".ogg", ".m4a",
        ".aac", ".wma", ".opus", ".mid",
    ),
    "Comprimidos": (
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz",
    ),
    "Instaladores": (
        ".exe", ".msi", ".deb", ".rpm", ".dmg", ".pkg", ".appimage", ".apk", ".iso",
    ),
}

OTROS = "Otros"

EXTENSION_A_CATEGORIA: dict[str, str] = {
    extension: categoria
    for categoria, extensiones in CATEGORIAS.items()
    for extension in extensiones
}


def categoria(fichero: Path) -> str:
    """Devuelve la carpeta que le toca a un fichero por su extensión."""
    return EXTENSION_A_CATEGORIA.get(fichero.suffix.lower(), OTROS)


def seleccionar(carpeta: Path) -> list[Path]:
    """Ficheros visibles del primer nivel, ordenados por nombre."""
    if not carpeta.is_dir():
        raise TareasError(f"«{carpeta}» no existe o no es una carpeta.")
    try:
        entradas = sorted(carpeta.iterdir(), key=lambda ruta: ruta.name.lower())
    except OSError as error:
        raise TareasError(f"No se pudo leer «{carpeta}»: {error}") from None
    return [
        ruta
        for ruta in entradas
        if ruta.is_file() and not ruta.name.startswith(".")
    ]


def ejecutar(
    carpeta: Path,
    simular: bool = False,
    copiar: bool = False,
) -> list[Resultado]:
    """Mueve (o copia) cada fichero a la carpeta de su categoría."""
    resultados: list[Resultado] = []
    reservados: set[Path] = set()

    for fichero in seleccionar(carpeta):
        destino = destino_libre(
            carpeta / categoria(fichero) / fichero.name,
            reservados=reservados,
        )
        reservados.add(destino)

        if simular:
            resultados.append(Resultado(fichero, destino, "simulado"))
            continue

        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            if copiar:
                shutil.copy2(fichero, destino)
                estado = "copiado"
            else:
                shutil.move(str(fichero), str(destino))
                estado = "movido"
        except OSError as error:
            resultados.append(
                Resultado(fichero, destino, "error", detalle=f"{error}")
            )
            continue
        resultados.append(Resultado(fichero, destino, estado))

    return resultados
