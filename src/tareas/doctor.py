"""Comprobaciones de solo lectura: «tareas doctor» diagnostica el entorno."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from . import config as configuracion
from .errores import ConfigError
from .rutas import carpeta_descargas

ESTADOS = ("ok", "aviso", "error")
SIMBOLO = {"ok": "✔", "aviso": "⚠", "error": "✘"}
COLOR = {"ok": "green", "aviso": "yellow", "error": "red"}

PRUEBAS = Path.home() / "pruebas-tareas"


@dataclass(frozen=True)
class Comprobacion:
    """Resultado de una comprobación: nombre, estado (ok/aviso/error) y detalle."""

    nombre: str
    estado: str
    detalle: str


def comprobar_config(ruta: Path) -> tuple[Comprobacion, list[dict[str, Any]]]:
    """Valida acciones.json; si falla devuelve la acción vacía y el ✘ correspondiente."""
    try:
        acciones = configuracion.cargar(ruta)
    except ConfigError as exc:
        return (
            Comprobacion("acciones.json", "error", str(exc)),
            [],
        )
    return (
        Comprobacion(
            "acciones.json",
            "ok",
            f"{len(acciones)} acciones válidas en {ruta}",
        ),
        acciones,
    )


def comprobar_dependencias() -> list[Comprobacion]:
    """Busca las dependencias opcionales sin importarlas, para no romper al diagnosticar."""
    modulos = {
        "send2trash": ("send2trash", "capturas y temporales no podrán usar la papelera"),
        "PIL": ("Pillow", "imagenes no podrá comprimir ni convertir"),
        "psutil": ("psutil", "sistema no podrá leer disco y memoria"),
        "pypdf": ("pypdf", "resumir-apuntes no podrá leer PDF"),
    }
    comprobaciones: list[Comprobacion] = []
    for modulo, (nombre, motivo) in modulos.items():
        if find_spec(modulo) is None:
            comprobaciones.append(
                Comprobacion(
                    f"Dependencia {nombre}",
                    "aviso",
                    f"falta {modulo}: {motivo}",
                )
            )
        else:
            comprobaciones.append(
                Comprobacion(f"Dependencia {nombre}", "ok", "instalada")
            )
    return comprobaciones


def comprobar_descargas() -> Comprobacion:
    """Comprueba que la carpeta de descargas detectada existe y se puede leer."""
    try:
        ruta = carpeta_descargas()
    except OSError as exc:
        return Comprobacion("Descargas", "error", f"no se puede resolver: {exc}")
    if not ruta.is_dir():
        return Comprobacion(
            "Descargas",
            "error",
            f"«{ruta}» no existe o no es una carpeta",
        )
    try:
        next(ruta.iterdir(), None)
    except OSError as exc:
        return Comprobacion("Descargas", "error", f"no se puede leer «{ruta}»: {exc}")
    return Comprobacion("Descargas", "ok", str(ruta))


def comprobar_origenes(acciones: list[dict[str, Any]]) -> list[Comprobacion]:
    """Comprueba el origen declarado de cada acción; si falta, es un aviso."""
    comprobaciones: list[Comprobacion] = []
    for accion in acciones:
        nombre = accion["nombre"]
        origen = accion.get("origen")
        if not isinstance(origen, str) or not origen.strip():
            comprobaciones.append(
                Comprobacion(
                    f"Origen «{nombre}»",
                    "aviso",
                    "sin origen: deberás indicar la carpeta en la orden",
                )
            )
            continue
        ruta = Path(origen).expanduser()
        if ruta.is_dir():
            comprobaciones.append(
                Comprobacion(f"Origen «{nombre}»", "ok", str(ruta))
            )
        else:
            comprobaciones.append(
                Comprobacion(
                    f"Origen «{nombre}»",
                    "aviso",
                    f"«{ruta}» no existe: esa acción no encontrará ficheros",
                )
            )
    return comprobaciones


def comprobar_ia() -> Comprobacion:
    """Aviso si faltan las variables de entorno para las órdenes con IA."""
    import os

    from .ia import cargar_dotenv

    cargar_dotenv()
    faltan = [
        variable
        for variable in ("CENTRO_IA_KEY", "CENTRO_IA_URL")
        if not os.environ.get(variable, "").strip()
    ]
    if not faltan:
        return Comprobacion("IA del centro", "ok", "variables configuradas")
    return Comprobacion(
        "IA del centro",
        "aviso",
        f"falta {', '.join(faltan)}: «tareas ia ...» no estará disponible",
    )


def comprobar_pruebas() -> Comprobacion:
    """Comprueba que existe la carpeta de pruebas recomendada."""
    if PRUEBAS.is_dir():
        return Comprobacion("pruebas-tareas", "ok", str(PRUEBAS))
    return Comprobacion(
        "pruebas-tareas",
        "aviso",
        f"falta {PRUEBAS}: crea una carpeta de pruebas antes de lanzar acciones reales",
    )


def diagnosticar(ruta_config: Path) -> list[Comprobacion]:
    """Reúne todas las comprobaciones; si la config falla, corta el resto de checks."""
    config, acciones = comprobar_config(ruta_config)
    comprobaciones: list[Comprobacion] = [config]

    if config.estado == "error":
        return comprobaciones

    comprobaciones.extend(comprobar_dependencias())
    comprobaciones.append(comprobar_descargas())
    comprobaciones.extend(comprobar_origenes(acciones))
    comprobaciones.append(comprobar_ia())
    comprobaciones.append(comprobar_pruebas())
    return comprobaciones
