"""Rutas habituales del sistema, sin dependencias opcionales."""

from __future__ import annotations

import os
from pathlib import Path

NOMBRES_DESCARGAS = (
    "Downloads",
    "Descargas",
    "Baixades",
    "Téléchargements",
    "Scaricati",
)


def carpeta_descargas() -> Path:
    """Devuelve la carpeta de descargas configurada o la habitual del sistema."""
    xdg = os.environ.get("XDG_DOWNLOAD_DIR", "").strip()
    if xdg:
        ruta = Path(xdg).expanduser()
        if ruta.is_dir():
            return ruta

    config = Path.home() / ".config" / "user-dirs.dirs"
    try:
        for linea in config.read_text(encoding="utf-8").splitlines():
            if not linea.startswith("XDG_DOWNLOAD_DIR="):
                continue
            valor = linea.split("=", 1)[1].strip().strip('"')
            valor = valor.replace("$HOME", str(Path.home()))
            ruta = Path(valor).expanduser()
            if ruta.is_dir():
                return ruta
    except OSError:
        pass

    for nombre in NOMBRES_DESCARGAS:
        ruta = Path.home() / nombre
        if ruta.is_dir():
            return ruta
    return Path.home() / "Downloads"
