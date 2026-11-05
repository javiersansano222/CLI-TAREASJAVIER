"""Menú interactivo que se abre al ejecutar `tareas` sin argumentos."""

from __future__ import annotations

import random
import shlex
import sys
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

consola = Console()

COLORES = {
    "rojo": ("red", "rojo"),
    "normal": ("bright_cyan", "normal"),
    "cian": ("bright_cyan", "normal"),
    "cyan": ("bright_cyan", "normal"),
    "azul": ("blue", "azul"),
    "verde": ("green", "verde"),
    "amarillo": ("yellow", "amarillo"),
}
_color_actual = "bright_cyan"
_menu_activo = False


def color_actual() -> str:
    """Devuelve el color Rich que está usando el menú."""
    return _color_actual


def menu_activo() -> bool:
    """Indica si el menú interactivo está abierto."""
    return _menu_activo


def cambiar_color(nombre: str) -> str:
    """Cambia el color del menú y devuelve el nombre elegido."""
    clave = nombre.strip().lower()
    if clave not in COLORES:
        raise ValueError(
            "color no válido; usa rojo, normal, azul, verde o amarillo"
        )
    global _color_actual
    codigo, etiqueta = COLORES[clave]
    _color_actual = codigo
    return etiqueta


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


def _pintar_menu(app: typer.Typer) -> None:
    color = color_actual()
    consola.print(
        Panel.fit(
            f"[bold {color}]Menú de tareas[/bold {color}]\n"
            "Escribe una orden y sus opciones, por ejemplo:\n"
            f"  [{color}]capturas --simular[/{color}]\n"
            f"  [{color}]informe --top 3[/{color}]\n"
            f"  [{color}]salir[/{color}] para terminar\n"
            f"  [{color}]hola[/{color}] para ver el banner de bienvenida",
            border_style=color,
        )
    )

    # Mostrar una guía rápida con los comandos más importantes
    guia_rapida = Table(
        title="Guía rápida de comandos",
        title_style=f"bold {color}",
        header_style=f"bold {color}",
    )
    guia_rapida.add_column("Comando", style="bold")
    guia_rapida.add_column("Descripción")
    
    comandos_guia = [
        ("hola", "Muestra el banner de bienvenida ASCII"),
        ("chuleta", "Muestra una chuleta rápida de Git y comandos de Linux"),
        ("sistema", "Muestra el tamaño del disco y la memoria en uso"),
        ("capturas", "Envía a la papelera las capturas antiguas"),
        ("temporales", "Envía a la papelera los temporales antiguos"),
        ("informe", "Muestra un resumen de la carpeta de descargas"),
        ("imagenes", "Lista o comprime imágenes"),
        ("validar", "Valida que acciones.json cumple el esquema"),
        ("acciones", "Lista las acciones definidas en acciones.json"),
        ("ejecutar <nombre> --simular", "Ejecuta una acción (simulada)"),
        ("cambio", "Cambia el color del menú (rojo, normal, azul, verde, amarillo)"),
        ("cita", "Muestra una cita motivacional aleatoria"),
    ]
    
    for comando, desc in comandos_guia:
        guia_rapida.add_row(comando, desc)
    
    consola.print(guia_rapida)

    # Tabla de todas las órdenes disponibles
    tabla = Table(
        title="Órdenes disponibles (todas)",
        title_style=f"bold {color}",
        header_style=f"bold {color}",
    )
    tabla.add_column("Orden", style="bold")
    tabla.add_column("Qué hace")
    for info in app.registered_commands:
        if info.hidden:
            continue
        tabla.add_row(_nombre_orden(info), _descripcion_orden(info))
    consola.print(tabla)


def _mostrar_cita_motivacional() -> None:
    """Muestra una cita motivacional aleatoria al usuario."""
    citas = [
        "El único modo de hacer un gran trabajo es amar lo que haces. - Steve Jobs",
        "La vida es lo que pasa mientras estás ocupado haciendo otros planes. - John Lennon",
        "No cuentes con el mañana, haz hoy lo que puedas. - Johann Wolfgang von Goethe",
        "La mejor manera de predecir el futuro es creándolo. - Peter Drucker",
        "No esperes. El tiempo nunca será justo ni perfecto. - Anonymous",
        "Tu tiempo es limitado, no lo desperdicies viviendo la vida de otros. - Steve Jobs",
        "El futuro pertenece a aquellos que creen en la belleza de sus sueños. - Eleanor Roosevelt",
        "El éxito no es la clave de la felicidad. La felicidad es la clave del éxito. - Albert Schweitzer",
        "El que no siembra vientos, no recoge tempestades. - Proverbio",
        "La persistencia es el camino del éxito. - Anonymous",
    ]
    
    cita = random.choice(citas)
    color = color_actual()
    consola.print(
        Panel.fit(
            f"[bold {color}]¡Una palabra de motivación!\n[/bold {color}]{cita}",
            border_style=color,
            padding=(1, 2),
        )
    )


def _bucle_menu(app: typer.Typer) -> None:
    _pintar_menu(app)
    # Mostrar una cita motivacional al inicio del menú
    _mostrar_cita_motivacional()
    color_anterior = color_actual()

    while True:
        color = color_actual()
        try:
            linea = consola.input(f"[bold {color}]tareas>[/bold {color}] ").strip()
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

        if partes and partes[0].startswith("/"):
            partes[0] = partes[0].lstrip("/")
        if partes and partes[0].lower() == "tareas":
            partes = partes[1:]
        if partes:
            _ejecutar(app, partes)
            if color_actual() != color_anterior:
                color_anterior = color_actual()
                consola.print()
                _pintar_menu(app)


def menu_interactivo(app: typer.Typer) -> None:
    """Muestra las órdenes disponibles y ejecuta la que escriba el usuario."""
    global _menu_activo
    _menu_activo = True
    try:
        _bucle_menu(app)
    finally:
        _menu_activo = False
