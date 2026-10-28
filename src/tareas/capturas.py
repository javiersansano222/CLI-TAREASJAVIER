"""Detecta capturas de pantalla y las envía a la papelera del sistema."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

from send2trash import send2trash

from .acciones import Resultado
from .errores import TareasError

EXTENSIONES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
PATRON_CAPTURA = re.compile(
    r"(?i)(?:screenshot|screen[ _-]?shot|"
    r"captura(?:[ _-](?:de[ _-])?pantalla)?|"
    r"capture[ _-]d[’']?[ée]cran|"
    r"снимок[ _-]экрана)"
)
DESTINO_PAPELERA = Path("Papelera del sistema")
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


def es_captura(ruta: Path) -> bool:
    """Indica si el nombre y la extensión parecen de una captura de pantalla."""
    return (
        ruta.suffix.lower() in EXTENSIONES
        and PATRON_CAPTURA.search(ruta.stem) is not None
    )


def seleccionar(carpeta: Path, horas: int) -> list[Path]:
    """Devuelve las capturas con al menos las horas indicadas."""
    limite = time.time() - horas * 3600
    try:
        entradas = sorted(
            carpeta.iterdir(),
            key=lambda ruta: (ruta.name.lower(), ruta.name),
        )
    except OSError as exc:
        raise TareasError(f"No se puede leer la carpeta «{carpeta}»: {exc}") from None

    capturas: list[Path] = []
    for ruta in entradas:
        try:
            if ruta.is_symlink() or not ruta.is_file():
                continue
            datos = ruta.stat()
        except OSError:
            continue
        if not es_captura(ruta):
            continue
        if datos.st_mtime > limite:
            continue
        capturas.append(ruta)
    return capturas


def enviar_a_papelera(ficheros: list[Path], simular: bool) -> list[Resultado]:
    """Envía cada fichero a la papelera o solo informa si se simula."""
    resultados: list[Resultado] = []
    for fichero in ficheros:
        try:
            if not simular:
                send2trash(str(fichero))
            resultados.append(
                Resultado(
                    fichero,
                    DESTINO_PAPELERA,
                    "simulado" if simular else "hecho",
                )
            )
        except (OSError, ValueError) as exc:
            detalle = str(exc) or exc.__class__.__name__
            resultados.append(Resultado(fichero, None, "error", detalle))
    return resultados
