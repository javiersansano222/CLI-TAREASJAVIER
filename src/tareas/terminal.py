"""Paletas de color de terminal y secuencias OSC para aplicarlas.

Un programa no puede cambiar el tema del emulador para siempre: el tema vive en
la configuración del emulador (Windows Terminal, iTerm2, GNOME Terminal). Lo que
sí puede es mandar secuencias OSC, que cambian los colores de la sesión actual
en iTerm2, kitty, WezTerm, VTE y, en parte, Windows Terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import re

from .errores import TareasError

# Fin de secuencia OSC (ST). También vale BEL, pero ST lo entienden todos.
FIN = "\x1b\\"
HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class Paleta:
    """Colores de una sesión: fondo, texto, cursor y los 16 colores ANSI."""

    nombre: str
    descripcion: str
    fondo: str
    texto: str
    cursor: str
    ansi: tuple[str, ...]

    def todo(self) -> tuple[str, ...]:
        """Todos los colores de la paleta, para enseñar una muestra."""
        return (self.fondo, self.texto, self.cursor, *self.ansi)


PALETAS: dict[str, Paleta] = {
    "medianoche": Paleta(
        nombre="medianoche",
        descripcion="Azules oscuros, cómodo de noche",
        fondo="#0b1020",
        texto="#d7dcf5",
        cursor="#7aa2f7",
        ansi=(
            "#151b2e", "#f07178", "#7ee787", "#ffd479",
            "#7aa2f7", "#c099ff", "#79dafa", "#d7dcf5",
            "#3b4261", "#ff8b92", "#a6f2ab", "#ffe0a3",
            "#a7c0ff", "#d7b6ff", "#a4e9ff", "#ffffff",
        ),
    ),
    "matrix": Paleta(
        nombre="matrix",
        descripcion="Verde sobre negro, como una consola antigua",
        fondo="#050805",
        texto="#b9ffb3",
        cursor="#00ff66",
        ansi=(
            "#0b140b", "#ff5f5f", "#00c853", "#c6ff00",
            "#00b8a9", "#b388ff", "#00e5ff", "#c8ffc4",
            "#1f2b1f", "#ff8a80", "#69f0ae", "#eeff41",
            "#18ffff", "#d0b3ff", "#84ffff", "#ffffff",
        ),
    ),
    "papel": Paleta(
        nombre="papel",
        descripcion="Claro, tipo folio, para trabajar de día",
        fondo="#f6f1e7",
        texto="#2b2a27",
        cursor="#8b5a2b",
        ansi=(
            "#2b2a27", "#b3261e", "#3f7d20", "#a86b00",
            "#1f5fa9", "#7b3fa0", "#0f7b8a", "#6b6459",
            "#7a7368", "#d93025", "#4f9a2f", "#c98a00",
            "#2b7bd0", "#9a5cc4", "#1a9aa8", "#ffffff",
        ),
    ),
    "ambar": Paleta(
        nombre="ambar",
        descripcion="Naranjas de fósforo, contraste suave",
        fondo="#1b1206",
        texto="#ffd79a",
        cursor="#ffb000",
        ansi=(
            "#241a0b", "#ff6d3f", "#d7b100", "#ffb000",
            "#c98a3c", "#e07ab0", "#7fc4a8", "#ffd79a",
            "#3a2a12", "#ff8f5f", "#efd34a", "#ffc93c",
            "#e0a35c", "#f09cc4", "#a3dbc3", "#fff3dc",
        ),
    ),
    "oceano": Paleta(
        nombre="oceano",
        descripcion="Azules y turquesas, tono frío",
        fondo="#071a24",
        texto="#cfeeff",
        cursor="#38bdf8",
        ansi=(
            "#0c2430", "#ff6b6b", "#5ee6a8", "#ffd479",
            "#4fa8ff", "#b48bff", "#3ce0e6", "#cfeeff",
            "#1b3a4a", "#ff8f8f", "#83f2c0", "#ffe3a3",
            "#7cc4ff", "#cbb0ff", "#74eff3", "#ffffff",
        ),
    ),
    "contraste": Paleta(
        nombre="contraste",
        descripcion="Negro y blanco puros, para verlo todo",
        fondo="#000000",
        texto="#ffffff",
        cursor="#ffff00",
        ansi=(
            "#000000", "#ff0000", "#00ff00", "#ffff00",
            "#0000ff", "#ff00ff", "#00ffff", "#ffffff",
            "#7f7f7f", "#ff7f7f", "#7fff7f", "#ffff7f",
            "#7f7fff", "#ff7fff", "#7fffff", "#ffffff",
        ),
    ),
}


@dataclass(frozen=True)
class Soporte:
    """Qué terminal hay delante y si admite secuencias OSC."""

    soportado: bool
    terminal: str
    nota: str = ""


def normalizar_hex(valor: str) -> str:
    """Devuelve «#rrggbb» o lanza TareasError si el color no vale."""
    limpio = valor.strip()
    encontrado = HEX.match(limpio)
    if not encontrado:
        raise TareasError(
            f"«{valor}» no es un color hex: escribe seis dígitos, "
            "por ejemplo #0b1020."
        )
    return "#" + encontrado.group(1).lower()


def a_rgb(valor: str) -> tuple[int, int, int]:
    """Convierte «#rrggbb» en una tupla (rojo, verde, azul)."""
    limpio = normalizar_hex(valor)[1:]
    return (
        int(limpio[0:2], 16),
        int(limpio[2:4], 16),
        int(limpio[4:6], 16),
    )


def a_x11(valor: str) -> str:
    """Formato que usan las secuencias OSC: rgb:rr/gg/bb."""
    rojo, verde, azul = a_rgb(valor)
    return f"rgb:{rojo:02x}/{verde:02x}/{azul:02x}"


def _osc(codigo: str, valor: str) -> str:
    return f"\x1b]{codigo};{valor}{FIN}"


def secuencia_texto(color: str) -> str:
    """Cambia el color del texto de la sesión (OSC 10)."""
    return _osc("10", a_x11(color))


def secuencia_fondo(color: str) -> str:
    """Cambia el color de fondo de la sesión (OSC 11)."""
    return _osc("11", a_x11(color))


def secuencia_cursor(color: str) -> str:
    """Cambia el color del cursor de la sesión (OSC 12)."""
    return _osc("12", a_x11(color))


def secuencias_paleta(paleta: Paleta) -> list[str]:
    """Cambia los 16 colores ANSI de la sesión (OSC 4)."""
    return [
        _osc(f"4;{indice}", a_x11(color))
        for indice, color in enumerate(paleta.ansi)
    ]


def aplicar(paleta: Paleta, con_paleta: bool = True) -> str:
    """Secuencias que cambian el fondo, el texto, el cursor y la paleta ANSI."""
    partes = [
        secuencia_fondo(paleta.fondo),
        secuencia_texto(paleta.texto),
        secuencia_cursor(paleta.cursor),
    ]
    if con_paleta:
        partes.extend(secuencias_paleta(paleta))
    return "".join(partes)


def restablecer() -> str:
    """Devuelve los colores originales del terminal (OSC 104, 110, 111 y 112)."""
    return (
        _osc("104", "")
        + _osc("110", "")
        + _osc("111", "")
        + _osc("112", "")
    )


def buscar(nombre: str) -> Paleta:
    """Devuelve la paleta con ese nombre o lanza un error con las disponibles."""
    clave = nombre.strip().lower()
    if clave not in PALETAS:
        raise TareasError(
            f"No hay ningún tema «{nombre}». Los que hay: "
            + ", ".join(sorted(PALETAS))
            + "."
        )
    return PALETAS[clave]


def detectar(entorno: dict[str, str] | None = None) -> Soporte:
    """Mira las variables del entorno para saber si el terminal admite OSC."""
    env = os.environ if entorno is None else entorno

    if env.get("TERM") == "dumb":
        return Soporte(False, "terminal sin color", "TERM=dumb no admite colores")
    if env.get("WT_SESSION"):
        return Soporte(True, "Windows Terminal")
    programa = env.get("TERM_PROGRAM", "")
    if programa == "iTerm.app":
        return Soporte(True, "iTerm2")
    if programa == "WezTerm":
        return Soporte(True, "WezTerm")
    if programa == "vscode":
        return Soporte(True, "VS Code", "el fondo puede no cambiar en el panel")
    if env.get("KITTY_WINDOW_ID") or env.get("TERM", "").startswith("xterm-kitty"):
        return Soporte(True, "kitty")
    if env.get("VTE_VERSION"):
        return Soporte(True, "GNOME Terminal / Tilix")
    if env.get("TERM", "").startswith("alacritty"):
        return Soporte(True, "Alacritty")
    if env.get("TMUX") or env.get("TERM", "").startswith("screen"):
        return Soporte(
            False,
            "tmux/screen",
            "el multiplexor se queda las secuencias; aplícalo fuera de tmux",
        )
    if env.get("TERM", "").startswith(("xterm", "rxvt")):
        return Soporte(True, "xterm")
    if os.name == "nt":
        return Soporte(
            False,
            "consola clásica de Windows",
            "usa Windows Terminal o el comando «tareas tema --exportar»",
        )
    return Soporte(False, "terminal desconocido", "no se sabe si admite OSC")
