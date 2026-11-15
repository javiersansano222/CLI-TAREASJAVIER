"""Convierte un tema en ficheros que entienden los terminales de verdad.

Una secuencia OSC solo dura lo que dura la sesión. Para que el cambio sea
permanente hay que importar el tema en la configuración del emulador, y cada
uno usa su formato: Windows Terminal (JSON), iTerm2 (plist) y GNOME
Terminal/Tilix (gsettings por script).
"""

from __future__ import annotations

import json
from pathlib import Path

from .errores import TareasError
from .terminal import Paleta, a_rgb

# Nombres que espera el esquema de Windows Terminal.
CLAVES_WINDOWS = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "purple",
    "cyan",
    "white",
    "brightBlack",
    "brightRed",
    "brightGreen",
    "brightYellow",
    "brightBlue",
    "brightPurple",
    "brightCyan",
    "brightWhite",
)

# Nombres que espera iTerm2 para los 16 colores.
CLAVES_ITERM = (
    "Ansi 0 Color",
    "Ansi 1 Color",
    "Ansi 2 Color",
    "Ansi 3 Color",
    "Ansi 4 Color",
    "Ansi 5 Color",
    "Ansi 6 Color",
    "Ansi 7 Color",
    "Ansi 8 Color",
    "Ansi 9 Color",
    "Ansi 10 Color",
    "Ansi 11 Color",
    "Ansi 12 Color",
    "Ansi 13 Color",
    "Ansi 14 Color",
    "Ansi 15 Color",
)


def esquema_windows(paleta: Paleta) -> str:
    """Esquema JSON para pegar en «schemes» de Windows Terminal."""
    esquema: dict[str, str] = {
        "name": f"tareas {paleta.nombre}",
        "background": paleta.fondo,
        "foreground": paleta.texto,
        "cursorColor": paleta.cursor,
    }
    for clave, color in zip(CLAVES_WINDOWS, paleta.ansi):
        esquema[clave] = color
    return json.dumps(esquema, indent=4, ensure_ascii=False) + "\n"


def _color_iterm(color: str) -> str:
    rojo, verde, azul = (canal / 255 for canal in a_rgb(color))
    return (
        "<dict>\n"
        "\t\t\t<key>Alpha Component</key>\n"
        "\t\t\t<real>1.0</real>\n"
        "\t\t\t<key>Blue Component</key>\n"
        f"\t\t\t<real>{azul:.4f}</real>\n"
        "\t\t\t<key>Color Space</key>\n"
        "\t\t\t<string>sRGB</string>\n"
        "\t\t\t<key>Green Component</key>\n"
        f"\t\t\t<real>{verde:.4f}</real>\n"
        "\t\t\t<key>Red Component</key>\n"
        f"\t\t\t<real>{rojo:.4f}</real>\n"
        "\t\t</dict>"
    )


def preajuste_iterm(paleta: Paleta) -> str:
    """Fichero .itermcolors para importar en iTerm2."""
    partes = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
        '<plist version="1.0">',
        "<dict>",
    ]
    for clave, color in zip(CLAVES_ITERM, paleta.ansi):
        partes.append(f"\t<key>{clave}</key>")
        partes.append("\t" + _color_iterm(color))
    for clave, color in (
        ("Background Color", paleta.fondo),
        ("Cursor Color", paleta.cursor),
        ("Foreground Color", paleta.texto),
    ):
        partes.append(f"\t<key>{clave}</key>")
        partes.append("\t" + _color_iterm(color))
    partes.extend(["</dict>", "</plist>", ""])
    return "\n".join(partes)


def script_gnome(paleta: Paleta) -> str:
    """Script de gsettings para GNOME Terminal, Tilix o Xfce."""
    colores = ", ".join(f"'{color}'" for color in paleta.ansi)
    lineas = [
        "#!/bin/sh",
        f"# Tema «{paleta.nombre}» para GNOME Terminal / Tilix.",
        "# Ejecútalo una vez; para volver atrás, elige otro perfil en el terminal.",
        'PERFIL=$(gsettings get org.gnome.Terminal.ProfilesList default | tr -d "\'")',
        'RUTA="org.gnome.Terminal.Legacy.Profile:/org/gnome/terminal/legacy/profiles:/:$PERFIL/"',
        f'gsettings set "$RUTA" background-color "{paleta.fondo}"',
        f'gsettings set "$RUTA" foreground-color "{paleta.texto}"',
        'gsettings set "$RUTA" use-theme-colors false',
        'gsettings set "$RUTA" cursor-colors-set true',
        f'gsettings set "$RUTA" cursor-background-color "{paleta.cursor}"',
        f'gsettings set "$RUTA" palette "[{colores}]"',
        'echo "Tema aplicado al perfil $PERFIL."',
    ]
    return "\n".join(lineas) + "\n"


def guardar(paleta: Paleta, carpeta: Path) -> list[Path]:
    """Escribe los tres ficheros del tema y devuelve sus rutas."""
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise TareasError(
            f"No se pudo crear la carpeta «{carpeta}»: {error}"
        ) from None

    ficheros = {
        f"tareas-{paleta.nombre}-windows-terminal.json": esquema_windows(paleta),
        f"tareas-{paleta.nombre}.itermcolors": preajuste_iterm(paleta),
        f"tareas-{paleta.nombre}-gnome.sh": script_gnome(paleta),
    }
    escritos: list[Path] = []
    for nombre, contenido in ficheros.items():
        destino = carpeta / nombre
        try:
            destino.write_text(contenido, encoding="utf-8")
        except OSError as error:
            raise TareasError(
                f"No se pudo escribir «{destino}»: {error}"
            ) from None
        escritos.append(destino)
    return escritos
