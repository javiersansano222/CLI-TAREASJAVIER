"""Disco y memoria del equipo para `tareas sistema`."""

from __future__ import annotations

import shutil
from pathlib import Path

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def _tamano(bytes_: float) -> str:
    """Convierte bytes en una unidad legible."""
    if bytes_ < 1024:
        return f"{bytes_:.0f} B"
    valor = float(bytes_)
    for unidad in ("KB", "MB", "GB", "TB"):
        valor /= 1024
        if valor < 1024:
            return f"{valor:.1f} {unidad}"
    return f"{valor:.1f} PB"


def _porcentaje(usado: int, total: int) -> str:
    if total <= 0:
        return "—"
    return f"{usado / total * 100:.1f}%"


def mostrar_sistema(consola: Console) -> None:
    """Muestra el uso del disco de la carpeta personal y de la memoria RAM."""
    ruta = Path.home()
    try:
        disco = shutil.disk_usage(ruta)
        memoria = psutil.virtual_memory()
    except OSError as error:
        consola.print(f"[red]✘ No se pudo leer el sistema: {error}[/red]")
        return

    consola.print(
        Panel.fit(
            "Uso del disco de tu carpeta personal y de la memoria RAM.",
            title="Sistema",
            border_style="cyan",
        )
    )

    tabla_disco = Table(title="Disco")
    tabla_disco.add_column("Ruta", style="bold")
    tabla_disco.add_column("Total")
    tabla_disco.add_column("Usado")
    tabla_disco.add_column("Libre")
    tabla_disco.add_column("Uso")
    tabla_disco.add_row(
        str(ruta),
        _tamano(disco.total),
        _tamano(disco.used),
        _tamano(disco.free),
        _porcentaje(disco.used, disco.total),
    )
    consola.print(tabla_disco)

    tabla_memoria = Table(title="Memoria RAM")
    tabla_memoria.add_column("Total", style="bold")
    tabla_memoria.add_column("Usada")
    tabla_memoria.add_column("Disponible")
    tabla_memoria.add_column("Uso")
    tabla_memoria.add_row(
        _tamano(memoria.total),
        _tamano(memoria.used),
        _tamano(memoria.available),
        f"{memoria.percent:.1f}%",
    )
    consola.print(tabla_memoria)

    if memoria.total == 0:
        consola.print("[yellow]No se pudo obtener el tamaño de la memoria.[/yellow]")
