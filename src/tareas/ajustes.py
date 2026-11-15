"""Ajustes del usuario que sobreviven al cierre de la terminal.

Se guardan en `ajustes.json` dentro de la carpeta de configuración del sistema
y solo contienen el tema elegido y los temas que haya creado el usuario. Si el
fichero no existe o está roto, se empieza de cero: nunca se pisa sin avisar.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errores import TareasError
from .terminal import PALETAS, Paleta, buscar as buscar_de_fabrica, normalizar_hex

VERSION = 1
NOMBRE_FICHERO = "ajustes.json"


def carpeta() -> Path:
    """Dónde viven los ajustes en cada sistema."""
    propio = os.environ.get("TAREAS_CONFIG", "").strip()
    if propio:
        return Path(propio).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA", "").strip()
        if base:
            return Path(base) / "tareas"
        return Path.home() / "AppData" / "Roaming" / "tareas"
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "tareas"


def ruta() -> Path:
    """Ruta completa del fichero de ajustes."""
    return carpeta() / NOMBRE_FICHERO


def leer() -> dict:
    """Ajustes actuales; si no hay fichero o está roto, se devuelven vacíos."""
    try:
        datos = json.loads(ruta().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": VERSION}
    if not isinstance(datos, dict):
        return {"version": VERSION}
    datos.setdefault("version", VERSION)
    return datos


def guardar(datos: dict) -> Path:
    """Escribe los ajustes y devuelve la ruta; un fallo de disco es previsible."""
    destino = ruta()
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        raise TareasError(
            f"No se pudo guardar «{destino}»: {error}"
        ) from None
    return destino


def tema_elegido() -> str | None:
    """Nombre del tema guardado, o None si nunca se eligió uno."""
    tema = leer().get("tema")
    return tema if isinstance(tema, str) and tema else None


def guardar_tema(nombre: str) -> Path:
    """Recuerda el tema elegido para las próximas sesiones."""
    datos = leer()
    datos["tema"] = nombre
    return guardar(datos)


def temas_propios() -> dict[str, Paleta]:
    """Temas creados por el usuario; los mal escritos se ignoran sin romper."""
    guardados = leer().get("temas")
    if not isinstance(guardados, dict):
        return {}

    propios: dict[str, Paleta] = {}
    for nombre, datos in guardados.items():
        if not isinstance(datos, dict):
            continue
        try:
            ansi = datos["ansi"]
            if not isinstance(ansi, list) or len(ansi) != 16:
                continue
            propios[str(nombre)] = Paleta(
                nombre=str(nombre),
                descripcion=str(datos.get("descripcion", "tema propio")),
                fondo=normalizar_hex(datos["fondo"]),
                texto=normalizar_hex(datos["texto"]),
                cursor=normalizar_hex(datos["cursor"]),
                ansi=tuple(normalizar_hex(color) for color in ansi),
            )
        except (KeyError, TypeError, TareasError):
            continue
    return propios


def buscar_tema(nombre: str) -> Paleta:
    """Busca entre los temas de fábrica y los creados por el usuario."""
    propios = temas_propios()
    clave = nombre.strip().lower()
    if clave in propios:
        return propios[clave]
    try:
        return buscar_de_fabrica(clave)
    except TareasError:
        disponibles = sorted({*PALETAS, *propios})
        raise TareasError(
            f"No hay ningún tema «{nombre}». Los que hay: "
            + ", ".join(disponibles)
            + "."
        ) from None


def guardar_tema_propio(paleta: Paleta) -> Path:
    """Añade o reemplaza un tema del usuario en los ajustes."""
    datos = leer()
    temas = datos.get("temas")
    if not isinstance(temas, dict):
        temas = {}
    temas[paleta.nombre] = {
        "descripcion": paleta.descripcion,
        "fondo": paleta.fondo,
        "texto": paleta.texto,
        "cursor": paleta.cursor,
        "ansi": list(paleta.ansi),
    }
    datos["temas"] = temas
    return guardar(datos)
