"""Selecciona ficheros y ejecuta la acción que pida el usuario."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from .acciones import Accion, Resultado
from .errores import TareasError


class Motor:
    """Interpreta las acciones validadas y las aplica sobre una carpeta."""

    def __init__(self, acciones: list[dict[str, Any]]) -> None:
        self.acciones: dict[str, Accion] = {
            accion["nombre"]: Accion.desde_config(accion) for accion in acciones
        }

    def obtener(self, nombre: str) -> Accion:
        """Devuelve una acción por su nombre o un error humano si no existe."""
        accion = self.acciones.get(nombre)
        if accion is None:
            raise TareasError(
                f"No hay ninguna acción «{nombre}». "
                "Mira la lista con: tareas acciones"
            )
        return accion

    @staticmethod
    def seleccionar(carpeta: Path, filtro: dict[str, Any]) -> list[Path]:
        """Devuelve solo los ficheros que cumplen todos los filtros."""
        extensiones = {extension.lower() for extension in filtro.get("extensiones", [])}
        patron = re.compile(filtro["patron"]) if "patron" in filtro else None
        dias = filtro.get("mas_antiguo_que_dias")
        megas = filtro.get("mayor_que_mb")
        ahora = time.time()

        try:
            entradas = sorted(
                carpeta.iterdir(),
                key=lambda ruta: (ruta.name.lower(), ruta.name),
            )
        except OSError as exc:
            raise TareasError(
                f"No se puede leer la carpeta «{carpeta}»: {exc}"
            ) from None

        elegidos: list[Path] = []
        for ruta in entradas:
            try:
                if not ruta.is_file():
                    continue
                datos = ruta.stat()
            except OSError:
                continue

            if extensiones and ruta.suffix.lower() not in extensiones:
                continue
            if patron is not None and not patron.search(ruta.name):
                continue
            if dias is not None and ahora - datos.st_mtime <= dias * 86400:
                continue
            if megas is not None and datos.st_size <= megas * 1024 * 1024:
                continue

            elegidos.append(ruta)

        return elegidos

    def ejecutar(
        self,
        nombre: str,
        carpeta: Path | None,
        simular: bool,
    ) -> list[Resultado]:
        """Ejecuta una acción concreta sobre la carpeta indicada o su origen."""
        accion = self.obtener(nombre)
        ruta = carpeta if carpeta is not None else accion.config.get("origen", ".")
        ruta = Path(ruta).expanduser()

        if not ruta.is_dir():
            raise TareasError(f"La carpeta «{ruta}» no existe o no es una carpeta.")

        ficheros = self.seleccionar(ruta, accion.config.get("filtro", {}))
        return accion.ejecutar(ficheros, simular)
