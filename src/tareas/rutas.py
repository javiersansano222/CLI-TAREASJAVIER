"""Rutas habituales del sistema, sin dependencias opcionales."""

from __future__ import annotations

import itertools
import os
from pathlib import Path
import unicodedata

NOMBRES_DESCARGAS = (
    "Downloads",
    "Descargas",
    "Baixades",
    "Téléchargements",
    "Scaricati",
)

# Cómo se llama cada carpeta personal en otros idiomas. Sirve para que un
# acciones.json escrito con «~/Descargas» funcione en un Windows en inglés.
EQUIVALENTES: dict[str, tuple[str, ...]] = {
    "descargas": ("Downloads", "Baixades"),
    "downloads": ("Descargas", "Baixades"),
    "baixades": ("Downloads", "Descargas"),
    "imagenes": ("Pictures", "Imatges", "Images"),
    "pictures": ("Imágenes", "Imatges", "Images"),
    "imatges": ("Pictures", "Imágenes"),
    "escritorio": ("Desktop", "Escriptori", "Bureau"),
    "desktop": ("Escritorio", "Escriptori", "Bureau"),
    "escriptori": ("Desktop", "Escritorio"),
    "documentos": ("Documents",),
    "documents": ("Documentos",),
    "musica": ("Music",),
    "music": ("Música", "Musica"),
    "videos": ("Videos",),
    "plantillas": ("Templates",),
    "templates": ("Plantillas",),
    "capturas": ("Screenshots", "Capturas de pantalla"),
    "capturas de pantalla": ("Screenshots",),
    "screenshots": ("Capturas", "Capturas de pantalla"),
}


def _sin_tildes(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar «Imágenes» con «imagenes»."""
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(
        letra for letra in descompuesto if unicodedata.category(letra) != "Mn"
    )


def resolver_carpeta(origen: str | Path) -> Path:
    """Expande ~ y, si la carpeta no existe, prueba su nombre en otro idioma.

    Si no hay equivalente o ninguno existe, devuelve la ruta original: quien
    decide si eso es un problema es la orden, no esta función.
    """
    ruta = Path(origen).expanduser()
    if ruta.exists():
        return ruta
    try:
        partes = ruta.relative_to(Path.home()).parts
    except ValueError:
        return ruta
    if not partes:
        return ruta

    opciones = [
        [parte, *EQUIVALENTES.get(_sin_tildes(parte), ())]
        for parte in partes
    ]
    for combinacion in itertools.product(*opciones):
        candidata = Path.home().joinpath(*combinacion)
        if candidata.exists():
            return candidata
    return ruta


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
