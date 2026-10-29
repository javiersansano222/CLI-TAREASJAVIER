"""Chuleta rápida de Git y Linux para `tareas chuleta`."""

from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

SECCIONES: tuple[tuple[str, Sequence[tuple[str, str]]], ...] = (
    (
        "Git",
        (
            ("Ver el estado", "git status"),
            ("Ver cambios sin preparar", "git diff"),
            ("Ver cambios preparados", "git diff --staged"),
            ("Preparar un archivo", "git add archivo"),
            ("Preparar todo", "git add ."),
            ("Hacer un commit", 'git commit -m "mensaje"'),
            ("Ver el historial", "git log --oneline --graph --decorate -10"),
            ("Ver ramas", "git branch"),
            ("Crear y cambiar de rama", "git switch -c nombre-rama"),
            ("Cambiar de rama", "git switch nombre-rama"),
            ("Ver remotos", "git remote -v"),
            ("Traer cambios", "git pull"),
            ("Subir commits", "git push"),
            ("Descartar cambios locales", "git restore archivo"),
            ("Quitar del área preparada", "git restore --staged archivo"),
            ("Guardar cambios temporalmente", "git stash"),
            ("Recuperar cambios guardados", "git stash pop"),
            ("Clonar un repositorio", "git clone URL"),
        ),
    ),
    (
        "Linux · moverse y ver archivos",
        (
            ("Ver dónde estoy", "pwd"),
            ("Listar, incluidos ocultos", "ls -la"),
            ("Entrar en una carpeta", "cd carpeta"),
            ("Subir una carpeta", "cd .."),
            ("Ir al home", "cd ~"),
            ("Ver un archivo", "cat archivo"),
            ("Verlo por páginas", "less archivo"),
            ("Ver las primeras líneas", "head archivo"),
            ("Seguir las últimas líneas", "tail -f archivo"),
        ),
    ),
    (
        "Linux · crear, copiar, mover y borrar",
        (
            ("Crear carpetas", "mkdir -p ruta/carpeta"),
            ("Crear un archivo vacío", "touch archivo"),
            ("Copiar", "cp origen destino"),
            ("Copiar carpetas", "cp -r origen destino"),
            ("Mover o renombrar", "mv origen destino"),
            ("Borrar un archivo", "rm archivo"),
            ("Borrar una carpeta", "rm -r carpeta"),
        ),
    ),
    (
        "Linux · buscar y contar",
        (
            ("Buscar texto", 'grep -R "texto" carpeta'),
            ("Buscar archivos por nombre", 'find . -name "*.py"'),
            ("Contar líneas", "wc -l archivo"),
        ),
    ),
    (
        "Linux · permisos, disco y procesos",
        (
            ("Ver permisos", "ls -l"),
            ("Dar permiso de ejecución", "chmod +x script.sh"),
            ("Ver espacio libre", "df -h"),
            ("Ver tamaño de carpetas", "du -sh *"),
            ("Ver procesos", "ps aux"),
            ("Ver procesos en vivo", "top"),
            ("Terminar un proceso", "kill PID"),
            ("Terminar por nombre", "pkill nombre"),
        ),
    ),
    (
        "Linux · red, compresión y paquetes",
        (
            ("Ver interfaces de red", "ip a"),
            ("Comprobar conexión", "ping -c 4 host"),
            ("Ver cabeceras HTTP", "curl -I URL"),
            ("Conectar por SSH", "ssh usuario@host"),
            ("Comprimir en tar.gz", "tar -czf archivo.tar.gz carpeta"),
            ("Descomprimir tar.gz", "tar -xzf archivo.tar.gz"),
            ("Descomprimir zip", "unzip archivo.zip"),
            ("Actualizar paquetes", "sudo apt update"),
            ("Instalar un paquete", "sudo apt install paquete"),
            ("Actualizar el sistema", "sudo apt upgrade"),
        ),
    ),
)

ATAJOS = (
    "Ctrl+C cancela · Ctrl+D cierra la terminal · Ctrl+L limpia la pantalla · "
    "Tab autocompleta · history muestra el historial · !! repite la última orden."
)

AVISOS = (
    "Cuidado: rm no usa la papelera. git reset --hard, git clean -fd y "
    "git push --force pueden borrar trabajo. No uses sudo si no entiendes la orden."
)


def mostrar_chuleta(consola: Console) -> None:
    """Pinta las tablas de la chuleta en la consola indicada."""
    consola.print(
        Panel.fit(
            "Referencia rápida de Git y Linux. Escribe una orden y pulsa Intro.",
            title="Chuleta rápida",
            border_style="cyan",
        )
    )

    for titulo, filas in SECCIONES:
        tabla = Table(title=titulo)
        tabla.add_column("Para...", style="bold")
        tabla.add_column("Orden", style="cyan")
        for para, orden in filas:
            tabla.add_row(para, orden)
        consola.print(tabla)

    consola.print(f"[bold]Atajos:[/bold] {ATAJOS}")
    consola.print(f"[yellow]{AVISOS}[/yellow]")
