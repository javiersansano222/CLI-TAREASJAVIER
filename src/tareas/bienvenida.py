"""Bienvenida visual de la CLI, dibujada con caracteres de terminal."""

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

ARTE = r"""
 ██╗  ██╗ ██████╗ ██╗      █████╗
 ██║  ██║██╔═══██╗██║     ██╔══██╗
 ███████║██║   ██║██║     ███████║
 ██╔══██║██║   ██║██║     ██╔══██║
 ██║  ██║╚██████╔╝███████╗██║  ██║
 ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
"""


def mostrar_bienvenida() -> None:
    """Pinta el banner y el mensaje de bienvenida."""
    consola = Console()
    consola.print(Align.center(Text(ARTE, style="bold cyan")))
    consola.print(
        Panel.fit(
            "[bold]Bienvenido a mi terminal personalizado[/bold]\n"
            "[dim]tareas · CLI personalizado[/dim]",
            border_style="bright_cyan",
            padding=(1, 4),
        )
    )


def main() -> None:
    """Punto de entrada del ejecutable directo `hola`."""
    mostrar_bienvenida()
