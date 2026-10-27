"""Menú interactivo que se abre al ejecutar `tareas` sin argumentos."""

from __future__ import annotations

import shlex
import sys
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

consola = Console()


def _nombre_orden(info: Any) -> str:
    return info.name or info.callback.__name__


def _descripcion_orden(info: Any) -> str:
    texto = info.help or info.callback.__doc__ or ""
    return " ".join(texto.split())


def _ejecutar(app: typer.Typer, partes: list[str]) -> None:
    try:
        app(args=partes, standalone_mode=False, prog_name="tareas")
    except typer.Exit:
        pass
    except typer.Abort:
        consola.print("[yellow]Cancelado.[/yellow]")
    except typer.TyperException as error:
        error.show()
    except (KeyboardInterrupt, EOFError):
        consola.print()
    except SystemExit:
        pass


def menu_interactivo(app: typer.Typer) -> None:
    """Muestra las órdenes disponibles y ejecuta la que escriba el usuario."""
    consola.print(
        Panel.fit(
            "[bold]Menú de tareas[/bold]\n"
            "Escribe una orden y sus opciones, por ejemplo:\n"
            "  [cyan]capturas --simular[/cyan]\n"
            "  [cyan]informe --top 3[/cyan]\n"
            "  [cyan]salir[/cyan] para terminar",
            border_style="bright_cyan",
        )
    )

    tabla = Table(title="Órdenes disponibles", header_style="bold cyan")
    tabla.add_column("Orden", style="bold")
    tabla.add_column("Qué hace")
    for info in app.registered_commands:
        if info.hidden:
            continue
        tabla.add_row(_nombre_orden(info), _descripcion_orden(info))
    consola.print(tabla)

    while True:
        try:
            linea = consola.input("[bold cyan]tareas>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            consola.print()
            break

        if not linea:
            continue
        if linea.lower() in {"salir", "exit", "quit", "q"}:
            consola.print("[dim]Hasta luego.[/dim]")
            break
        if linea.lower() in {"ayuda", "help", "?"}:
            _ejecutar(app, ["--help"])
            continue

        try:
            partes = shlex.split(linea, posix=sys.platform != "win32")
        except ValueError as error:
            consola.print(f"[red]✘ No entiendo la línea: {error}[/red]")
            continue

        if partes and partes[0].lower() == "tareas":
            partes = partes[1:]
        if partes:
            _ejecutar(app, partes)
