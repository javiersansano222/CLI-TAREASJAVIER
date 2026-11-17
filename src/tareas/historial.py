"""Historial de operaciones y forma de deshacer el último lote.

Cada línea de `historial.jsonl` es un lote: la orden que se ejecutó y las
operaciones que cambiaron algo de verdad (las simulaciones no se apuntan).
`deshacer` busca el lote reversible más reciente y lo recorre al revés:
devuelve los ficheros movidos o renombrados a su sitio y manda a la papelera
las copias o los ficheros creados. Lo que ya no existe se salta sin romper
nada. Las operaciones que no se pueden revertir (`borrar` y la papelera del
sistema) se quedan registradas y se avisa de ello sin bloquear las órdenes
anteriores.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from send2trash import send2trash

from . import ajustes
from .errores import TareasError

NOMBRE_FICHERO = "historial.jsonl"
VERSION = 1
HECHOS = ("hecho", "movido", "copiado")
REVERSIBLES = {"mover", "renombrar", "copiar", "crear"}


def ruta() -> Path:
    """Ruta del historial, en la misma carpeta que los ajustes del usuario."""
    return ajustes.carpeta() / NOMBRE_FICHERO


@dataclass(frozen=True)
class Operacion:
    """Resultado de intentar deshacer una operación concreta."""

    tipo: str
    origen: Path
    destino: Path | None
    estado: str
    detalle: str = ""


@dataclass(frozen=True)
class Informe:
    """Lo que ha pasado al deshacer un lote del historial."""

    fecha: str
    orden: str
    operaciones: list[Operacion]
    omitidos: int = 0

    @property
    def deshechas(self) -> int:
        return sum(operacion.estado == "deshecho" for operacion in self.operaciones)

    @property
    def simuladas(self) -> int:
        return sum(operacion.estado == "simulado" for operacion in self.operaciones)


def registrar(
    orden: str,
    resultados: Iterable[Any],
    tipo: str,
) -> Path | None:
    """Añade un lote al historial con lo que de verdad cambió algo.

    Devuelve la ruta del historial o None si no había nada que apuntar. Un
    fallo al escribir el historial no convierte en error una operación de
    ficheros que ya ha funcionado: el historial es una ayuda, no un requisito.
    """
    operaciones = [
        {
            "tipo": tipo,
            # Siempre absolutas: deshacer puede ejecutarse desde otra carpeta.
            "origen": str(Path(resultado.origen).expanduser().absolute()),
            "destino": (
                str(Path(resultado.destino).expanduser().absolute())
                if resultado.destino is not None
                else None
            ),
        }
        for resultado in resultados
        if resultado.estado in HECHOS
    ]
    if not operaciones:
        return None

    lote = {
        "version": VERSION,
        "fecha": datetime.now().replace(microsecond=0).isoformat(sep=" "),
        "orden": orden,
        "operaciones": operaciones,
    }
    destino = ruta()
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("a", encoding="utf-8") as fichero:
            fichero.write(json.dumps(lote, ensure_ascii=False) + "\n")
    except OSError:
        return None
    return destino


def leer() -> list[dict[str, Any]]:
    """Devuelve los lotes válidos del historial, del más antiguo al más nuevo."""
    try:
        lineas = ruta().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    lotes: list[dict[str, Any]] = []
    for linea in lineas:
        texto = linea.strip()
        if not texto:
            continue
        try:
            lote = json.loads(texto)
        except json.JSONDecodeError:
            continue
        if isinstance(lote, dict) and isinstance(lote.get("operaciones"), list):
            lotes.append(lote)
    return lotes


def reversible(lote: dict[str, Any]) -> bool:
    """Indica si el lote tiene al menos una operación que se puede revertir."""
    return any(
        isinstance(operacion, dict) and operacion.get("tipo") in REVERSIBLES
        for operacion in lote.get("operaciones", [])
    )


def deshacer(simular: bool = False) -> Informe:
    """Revierte el último lote y lo quita del historial si deshizo algo."""
    lotes = leer()
    if not lotes:
        raise TareasError("El historial está vacío: no hay nada que deshacer.")

    # Se busca el lote reversible más reciente: si lo último fue, por ejemplo,
    # una limpieza a la papelera, no tiene sentido quedarse atascado ahí y no
    # poder deshacer un movimiento anterior.
    indice = next(
        (
            posicion
            for posicion in range(len(lotes) - 1, -1, -1)
            if reversible(lotes[posicion])
        ),
        None,
    )
    if indice is None:
        lote = lotes[-1]
        operaciones = [
            _deshacer_una(operacion, simular)
            for operacion in reversed(lote.get("operaciones", []))
            if isinstance(operacion, dict)
        ]
        return Informe(
            fecha=str(lote.get("fecha", "—")),
            orden=str(lote.get("orden", "—")),
            operaciones=operaciones,
        )

    lote = lotes[indice]
    operaciones = [
        _deshacer_una(operacion, simular)
        for operacion in reversed(lote.get("operaciones", []))
        if isinstance(operacion, dict)
    ]
    informe = Informe(
        fecha=str(lote.get("fecha", "—")),
        orden=str(lote.get("orden", "—")),
        operaciones=operaciones,
        omitidos=len(lotes) - 1 - indice,
    )

    # Solo se consume el lote si de verdad se revirtió algo: si todo eran
    # operaciones imposibles de deshacer, se queda en el historial para que
    # el usuario sepa qué pasó y pueda restaurarlo a mano.
    if not simular and informe.deshechas:
        _guardar(lotes[:indice] + lotes[indice + 1 :])
    return informe


def _deshacer_una(datos: dict[str, Any], simular: bool) -> Operacion:
    """Intenta revertir una operación del lote, sin lanzar errores previsibles."""
    tipo = str(datos.get("tipo", ""))
    origen_dato = datos.get("origen")
    destino_dato = datos.get("destino")
    origen = Path(str(origen_dato)) if origen_dato else Path()
    destino = Path(str(destino_dato)) if destino_dato else None

    if tipo in {"mover", "renombrar"}:
        return _devolver(tipo, origen, destino, simular)
    if tipo in {"copiar", "crear"}:
        return _retirar(tipo, origen, destino, simular)
    return Operacion(
        tipo,
        origen,
        destino,
        "saltado",
        "esta operación no se puede deshacer",
    )


def _devolver(
    tipo: str,
    origen: Path,
    destino: Path | None,
    simular: bool,
) -> Operacion:
    """Devuelve a su sitio un fichero que se movió o se renombró."""
    if str(origen) in {"", "."}:
        return Operacion(tipo, origen, destino, "saltado", "falta la ruta original")
    if destino is None:
        return Operacion(tipo, origen, destino, "saltado", "falta la ruta de destino")
    if not destino.exists() and not destino.is_symlink():
        return Operacion(
            tipo, origen, destino, "saltado", f"ya no existe «{destino}»"
        )
    if origen.exists() or origen.is_symlink():
        return Operacion(
            tipo, origen, destino, "saltado", f"ya existe «{origen}»"
        )
    if simular:
        return Operacion(
            tipo, origen, destino, "simulado", f"volvería a «{origen}»"
        )
    try:
        origen.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destino), str(origen))
    except OSError as error:
        return Operacion(tipo, origen, destino, "error", str(error))
    return Operacion(tipo, origen, destino, "deshecho", f"vuelve a «{origen}»")


def _retirar(
    tipo: str,
    origen: Path,
    destino: Path | None,
    simular: bool,
) -> Operacion:
    """Manda a la papelera una copia o un fichero que creó la herramienta."""
    if destino is None:
        return Operacion(tipo, origen, destino, "saltado", "falta la ruta creada")
    if not destino.exists() and not destino.is_symlink():
        return Operacion(
            tipo, origen, destino, "saltado", f"ya no existe «{destino}»"
        )
    if simular:
        return Operacion(
            tipo, origen, destino, "simulado", f"iría a la papelera «{destino}»"
        )
    try:
        send2trash(str(destino))
    except (OSError, ValueError) as error:
        return Operacion(tipo, origen, destino, "error", str(error))
    return Operacion(
        tipo, origen, destino, "deshecho", f"a la papelera «{destino}»"
    )


def _guardar(lotes: list[dict[str, Any]]) -> None:
    """Reescribe el historial sin los lotes ya deshechos, de forma atómica."""
    destino = ruta()
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not lotes:
            destino.write_text("", encoding="utf-8")
            return
        temporal = destino.with_name(destino.name + ".tmp")
        temporal.write_text(
            "".join(
                json.dumps(lote, ensure_ascii=False) + "\n" for lote in lotes
            ),
            encoding="utf-8",
        )
        temporal.replace(destino)
    except OSError as error:
        raise TareasError(
            f"No se pudo actualizar «{destino}»: {error}"
        ) from None
