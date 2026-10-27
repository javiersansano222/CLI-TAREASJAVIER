"""Clases que saben aplicar una acción a una lista de ficheros."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Resultado:
    """Informe de lo que ha pasado con un fichero."""

    origen: Path
    destino: Path | None
    estado: str
    detalle: str | None = None


def destino_libre(
    destino: Path,
    reservados: set[Path] | None = None,
    desaparecidos: set[Path] | None = None,
) -> Path:
    """Devuelve una ruta libre frente al disco y a los destinos ya calculados."""
    ocupados = reservados if reservados is not None else set()
    vaciados = desaparecidos if desaparecidos is not None else set()
    libre = destino
    numero = 1
    while (
        ((libre.exists() or libre.is_symlink()) and libre not in vaciados)
        or libre in ocupados
    ):
        libre = destino.with_name(f"{destino.stem} ({numero}){destino.suffix}")
        numero += 1
    return libre


class Accion(ABC):
    """Base de todas las acciones; cada subclase se registra sola por su tipo."""

    tipo = ""
    destructiva = False
    _registro: dict[str, type[Accion]] = {}

    def __init__(self, config: dict[str, Any]) -> None:
        self.nombre: str = config["nombre"]
        self.descripcion: str = config["descripcion"]
        self.config = config
        self._reservados: set[Path] = set()
        self._desaparecidos: set[Path] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.tipo:
            Accion._registro[cls.tipo] = cls

    @property
    def confirmar(self) -> bool:
        """Indica si hay que pedir confirmación antes de ejecutar de verdad."""
        return bool(self.config.get("confirmar", True))

    @staticmethod
    def desde_config(config: dict[str, Any]) -> Accion:
        """Fábrica: convierte un diccionario del JSON en la clase que toca."""
        clase = Accion._registro.get(config["tipo"])
        if clase is None:
            raise ValueError(f"No hay ninguna clase registrada para «{config['tipo']}»")
        return clase(config)

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        """Aplica la acción a cada fichero y devuelve un resultado por fichero."""
        self._reservados = set()
        self._desaparecidos = set()
        resultados: list[Resultado] = []
        for numero, fichero in enumerate(ficheros, start=1):
            try:
                resultado = self.aplicar(fichero, numero, simular)
            except (
                OSError,
                ValueError,
                OverflowError,
                KeyError,
                IndexError,
                AttributeError,
                shutil.Error,
            ) as exc:
                detalle = str(exc) or exc.__class__.__name__
                resultado = Resultado(fichero, None, "error", detalle)
            resultados.append(resultado)
        return resultados

    def _destino_libre(self, destino: Path) -> Path:
        libre = destino_libre(destino, self._reservados, self._desaparecidos)
        self._reservados.add(libre)
        return libre

    @abstractmethod
    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        """Aplica la acción a un único fichero."""


class Mover(Accion):
    tipo = "mover"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta = Path(self.config["destino"]).expanduser()
        destino = self._destino_libre(carpeta / fichero.name)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.move(fichero, destino)
        self._desaparecidos.add(fichero)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Copiar(Accion):
    tipo = "copiar"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta = Path(self.config["destino"]).expanduser()
        destino = self._destino_libre(carpeta / fichero.name)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fichero, destino)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Renombrar(Accion):
    tipo = "renombrar"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        fecha = datetime.fromtimestamp(fichero.stat().st_mtime)
        nuevo_nombre = self.config["plantilla"].format(
            fecha=fecha,
            n=n,
            ext=fichero.suffix.lower(),
            nombre=fichero.stem,
        )
        if nuevo_nombre == fichero.name:
            return Resultado(fichero, None, "saltado")

        destino = self._destino_libre(fichero.with_name(nuevo_nombre))
        if not simular:
            fichero.rename(destino)
        self._desaparecidos.add(fichero)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Borrar(Accion):
    tipo = "borrar"
    destructiva = True

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        if not simular:
            fichero.unlink()
        self._desaparecidos.add(fichero)
        return Resultado(fichero, None, "simulado" if simular else "hecho")
