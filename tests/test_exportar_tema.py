"""Pruebas de exportar_tema.py: los ficheros que entienden los terminales."""

from __future__ import annotations

import json
import plistlib

import pytest

from tareas.errores import TareasError
from tareas.exportar_tema import (
    CLAVES_ITERM,
    CLAVES_WINDOWS,
    esquema_windows,
    guardar,
    preajuste_iterm,
    script_gnome,
)
from tareas.terminal import PALETAS


@pytest.fixture
def paleta():
    return PALETAS["medianoche"]


def test_esquema_windows_tiene_todas_las_claves(paleta):
    """Windows Terminal espera fondo, texto, cursor y 16 colores con sus nombres."""
    esquema = json.loads(esquema_windows(paleta))
    assert esquema["name"] == f"tareas {paleta.nombre}"
    assert esquema["background"] == paleta.fondo
    assert esquema["foreground"] == paleta.texto
    assert esquema["cursorColor"] == paleta.cursor
    for clave, color in zip(CLAVES_WINDOWS, paleta.ansi):
        assert esquema[clave] == color


def test_preajuste_iterm_es_un_plist_valido(paleta):
    """El .itermcolors se puede leer con plistlib, que es lo que hace iTerm2."""
    datos = plistlib.loads(preajuste_iterm(paleta).encode("utf-8"))
    assert set(CLAVES_ITERM) <= set(datos)
    for clave in CLAVES_ITERM:
        assert 0 <= datos[clave]["Red Component"] <= 1
    assert datos["Background Color"]["Red Component"] == pytest.approx(0.043, abs=0.01)
    assert datos["Foreground Color"]["Color Space"] == "sRGB"


def test_script_gnome_lleva_los_16_colores(paleta):
    """El script de gsettings manda fondo, texto, cursor y la paleta completa."""
    script = script_gnome(paleta)
    assert script.startswith("#!/bin/sh")
    assert script.count("gsettings set") == 6
    for color in paleta.ansi:
        assert color in script
    assert "ProfilesList default" in script


def test_guardar_escribe_los_tres_ficheros(tmp_path, paleta):
    """Exportar deja un fichero por terminal, con el nombre del tema."""
    ficheros = guardar(paleta, tmp_path / "temas")
    nombres = sorted(fichero.name for fichero in ficheros)
    assert nombres == [
        "tareas-medianoche-gnome.sh",
        "tareas-medianoche-windows-terminal.json",
        "tareas-medianoche.itermcolors",
    ]
    assert all(fichero.is_file() for fichero in ficheros)


def test_guardar_en_ruta_imposible_da_error_humano(tmp_path, paleta):
    """Si el destino no se puede crear, se explica sin traceback."""
    estorbo = tmp_path / "estorbo"
    estorbo.write_text("soy un fichero", encoding="utf-8")
    with pytest.raises(TareasError) as error:
        guardar(paleta, estorbo / "temas")
    assert "No se pudo crear la carpeta" in str(error.value)
