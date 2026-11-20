"""Menú interactivo que se abre al ejecutar `tareas` sin argumentos."""

from __future__ import annotations

import random
import shlex
import sys
from typing import Any

import typer
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tareas import __version__

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

# Órdenes agrupadas por lo que el usuario quiere hacer, no por orden alfabético.
# Si una orden nueva no aparece aquí, cae en «OTRAS»: nunca desaparece del menú.
CATEGORIAS: dict[str, tuple[str, ...]] = {
    "ARCHIVOS": (
        "organizar",
        "mover",
        "capturas",
        "temporales",
        "imagenes",
        "listar",
    ),
    "SISTEMA": (
        "doctor",
        "sistema",
        "mirar-espacio",
        "informe",
        "validar",
        "acciones",
        "ejecutar",
    ),
    "APRENDER": (
        "chuleta",
        "tema",
        "cambio",
        "hola",
        "cita",
    ),
}

# Estas dos van en una línea aparte, más compacta, para no llenar la pantalla.
EXTRAS: dict[str, tuple[str, ...]] = {
    "SEGURIDAD": ("historial", "deshacer"),
    "IA": ("comprobar-ia", "ia sugerir", "ia explicar"),
}

EJEMPLOS: tuple[tuple[str, str, str], ...] = (
    ("1", "informe", "Ver Descargas (solo lectura)"),
    ("2", "organizar --simular", "Ordenar sin tocar nada"),
    ("3", "historial", "Ver lo último (y deshacer)"),
)

# Los números del bloque «Empieza por aquí» también ejecutan la orden.
ATAJOS_INICIO: dict[str, tuple[str, ...]] = {
    "1": ("informe",),
    "2": ("organizar", "--simular"),
    "3": ("historial",),
}

CONSEJOS: tuple[str, ...] = (
    "prueba --simular primero; no toca nada",
    "historial enseña lo último; deshacer lo revierte",
    "capturas y temporales usan la papelera, no borran para siempre",
    "mover nunca sobrescribe: crea «nombre (1)»",
    "edita acciones.json y compruébalo con validar",
    "si algo no funciona, doctor revisa el entorno",
)

# Descripciones de una o dos palabras para que el menú quepa de una vez.
DESCRIPCIONES_CORTAS: dict[str, str] = {
    "organizar": "ordena",
    "mover": "traslada",
    "capturas": "limpia",
    "temporales": "limpia",
    "imagenes": "comprime",
    "listar": "muestra",
    "doctor": "diagnostica",
    "sistema": "disco/RAM",
    "mirar-espacio": "mide",
    "informe": "resumen",
    "validar": "revisa",
    "acciones": "lista",
    "ejecutar": "lanza",
    "chuleta": "Git/Linux",
    "tema": "colores",
    "cambio": "menú",
    "hola": "bienvenida",
    "cita": "frase",
    "historial": "lotes",
    "deshacer": "revierte",
    "comprobar-ia": "prueba",
    "ia sugerir": "propone",
    "ia explicar": "explica",
}


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


def _ordenes_menu(app: typer.Typer) -> list[tuple[str, str]]:
    """Todas las órdenes, bajando un nivel dentro de las subapps (p. ej. «ia»)."""
    ordenes: list[tuple[str, str]] = []
    for info in app.registered_commands:
        if info.hidden:
            continue
        ordenes.append((_nombre_orden(info), _descripcion_orden(info)))
    for info in app.registered_groups:
        if info.hidden:
            continue
        prefijo = info.name or (
            info.typer_instance.info.name if info.typer_instance.info.name else ""
        )
        ayuda = " ".join((info.help or info.typer_instance.info.help or "").split())
        if ayuda:
            ordenes.append((prefijo, ayuda))
        for sub in info.typer_instance.registered_commands:
            if sub.hidden:
                continue
            ordenes.append(
                (f"{prefijo} {_nombre_orden(sub)}", _descripcion_orden(sub))
            )
    return ordenes


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


# Los paneles no se estiran más allá de este ancho: en una terminal de 120
# columnas quedaban cajas larguísimas con medio panel vacío.
ANCHO_MAXIMO = 84


def _caja() -> box.Box:
    """Cajas con esquinas redondeadas, o ASCII si el terminal es antiguo."""
    return box.ASCII if getattr(consola, "legacy_windows", False) else box.ROUNDED


def _ancho_util() -> int:
    """Ancho del panel: el de la terminal, sin pasar de ANCHO_MAXIMO."""
    return min(consola.width or 80, ANCHO_MAXIMO)


def _descripcion_corta(nombre: str, descripcion: str) -> str:
    """Versión de una o dos palabras de la ayuda, para que quepa en el panel."""
    corta = DESCRIPCIONES_CORTAS.get(nombre)
    if corta:
        return corta
    texto = " ".join(descripcion.split()).split(".")[0]
    return texto if len(texto) <= 24 else texto[:23] + "…"


def _datos_categorias(app: typer.Typer) -> list[tuple[str, list[tuple[str, str]]]]:
    """Agrupa las órdenes reales de Typer; las nuevas caen en «OTRAS»."""
    disponibles = dict(_ordenes_menu(app))
    usadas = {"version", "ia"}
    datos: list[tuple[str, list[tuple[str, str]]]] = []

    for nombre, comandos in CATEGORIAS.items():
        filas = [
            (comando, _descripcion_corta(comando, disponibles[comando]))
            for comando in comandos
            if comando in disponibles
        ]
        usadas.update(comando for comando, _ in filas)
        if filas:
            datos.append((nombre, filas))

    for comandos in EXTRAS.values():
        usadas.update(comandos)

    otras = [
        (nombre, _descripcion_corta(nombre, descripcion))
        for nombre, descripcion in disponibles.items()
        if nombre not in usadas
    ]
    if otras:
        datos.append(("OTRAS", otras))

    return datos


def _bloque_categoria(
    nombre: str, filas: list[tuple[str, str]], color: str
) -> Group:
    """Título de categoría, una raya y sus órdenes con la descripción al lado."""
    tabla = Table.grid(padding=(0, 1))
    tabla.add_column(style="bold white", no_wrap=True)
    # `fold` en vez de recortar con «…»: si una descripción larga no cabe
    # (órdenes sin clasificar), baja de línea en lugar de perderse.
    tabla.add_column(style="dim", overflow="fold")
    for comando, descripcion in filas:
        tabla.add_row(comando, descripcion)
    return Group(
        Text(nombre, style=f"bold {color}"),
        Text("─" * len(nombre), style=color),
        tabla,
    )


def _pintar_cabecera(color: str) -> None:
    consola.print(
        Panel(
            Text("Ordena, limpia y entiende tus ficheros sin miedo.", style="white"),
            title=Text(f"tareas {__version__}", style=f"bold {color}"),
            border_style=color,
            box=_caja(),
            padding=(0, 1),
            width=_ancho_util(),
        )
    )


def _pintar_empieza(color: str) -> None:
    tabla = Table.grid(padding=(0, 2))
    tabla.add_column(style=f"bold {color}", justify="right", no_wrap=True)
    tabla.add_column(style="bold white", no_wrap=True)
    tabla.add_column(style="dim")
    for numero, comando, descripcion in EJEMPLOS:
        tabla.add_row(numero, comando, descripcion)
    consola.print(
        Panel(
            tabla,
            title=Text("Empieza por aquí", style=f"bold {color}"),
            border_style=color,
            box=_caja(),
            padding=(0, 1),
            width=_ancho_util(),
        )
    )


def _pintar_categorias(app: typer.Typer, color: str) -> None:
    datos = _datos_categorias(app)
    if not datos:
        return

    ancho = _ancho_util()
    if ancho < 80:
        # Terminal estrecha: una línea por categoría, sin descripciones. Con dos
        # bloques la tercera categoría bajaba de línea y el menú no cabía.
        for nombre, filas in datos:
            consola.print(Text(nombre, style=f"bold {color}"))
            consola.print(
                Text(" · ".join(comando for comando, _ in filas), style="white")
            )
        return

    columnas = 3
    # Ancho fijo por columna: así los bloques no se separan en pantallas anchas.
    # 25 es lo que necesita el bloque más ancho («mirar-espacio diagnostica»).
    ancho_columna = max(25, ancho // columnas - 2)
    tabla = Table.grid(padding=(0, 2))
    for _ in range(columnas):
        tabla.add_column(width=ancho_columna)
    bloques: list[Any] = [
        _bloque_categoria(nombre, filas, color) for nombre, filas in datos
    ]
    for inicio in range(0, len(bloques), columnas):
        fila = bloques[inicio : inicio + columnas]
        fila.extend([""] * (columnas - len(fila)))
        tabla.add_row(*fila)
    consola.print(tabla)


def _pintar_extras(app: typer.Typer, color: str) -> None:
    disponibles = dict(_ordenes_menu(app))
    for nombre, comandos in EXTRAS.items():
        vivos = [comando for comando in comandos if comando in disponibles]
        if not vivos:
            continue
        linea = Text()
        linea.append(f"{nombre}  ", style=f"bold {color}")
        linea.append(" · ".join(vivos), style="white")
        consola.print(linea)


def _pintar_pie() -> None:
    consola.print(Text(f"Consejo: {random.choice(CONSEJOS)}", style="dim"))
    consola.print(Text("escribe una orden · ayuda · salir", style="dim"))


def _pintar_menu(app: typer.Typer) -> None:
    """Panel de mando: cabecera, ejemplos, categorías y consejo."""
    color = color_actual()
    _pintar_cabecera(color)
    _pintar_empieza(color)
    consola.print()
    _pintar_categorias(app, color)
    _pintar_extras(app, color)
    consola.print()
    _pintar_pie()


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
        if len(partes) == 1 and partes[0] in ATAJOS_INICIO:
            partes = list(ATAJOS_INICIO[partes[0]])
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
