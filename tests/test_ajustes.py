"""Pruebas de ajustes.py: el tema elegido y los temas propios se guardan bien."""

from __future__ import annotations

import json

import pytest

from tareas import ajustes
from tareas.errores import TareasError
from tareas.terminal import PALETAS, Paleta


def test_carpeta_respeta_tareas_config(tmp_path, monkeypatch):
    """TAREAS_CONFIG manda: sirve para probar sin tocar los ajustes de verdad."""
    monkeypatch.setenv("TAREAS_CONFIG", str(tmp_path / "mi-config"))
    assert ajustes.carpeta() == tmp_path / "mi-config"
    assert ajustes.ruta() == tmp_path / "mi-config" / "ajustes.json"


def test_carpeta_usa_xdg_fuera_de_windows(tmp_path, monkeypatch):
    """En Linux y macOS los ajustes van a XDG_CONFIG_HOME/tareas."""
    monkeypatch.delenv("TAREAS_CONFIG", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    if ajustes.os.name == "nt":
        pytest.skip("en Windows la carpeta es APPDATA")
    assert ajustes.carpeta() == tmp_path / "xdg" / "tareas"


def test_leer_sin_fichero_no_falla():
    """La primera vez no hay ajustes y no es un error."""
    assert ajustes.leer() == {"version": ajustes.VERSION}


def test_leer_json_roto_no_falla(tmp_path):
    """Un ajustes.json roto se ignora: mejor empezar de cero que reventar."""
    ruta = ajustes.ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("{ esto no es json", encoding="utf-8")
    assert ajustes.leer()["version"] == ajustes.VERSION


def test_leer_json_que_no_es_objeto(tmp_path):
    """Si el JSON es una lista, tampoco se usa."""
    ruta = ajustes.ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("[1, 2, 3]", encoding="utf-8")
    assert ajustes.leer() == {"version": ajustes.VERSION}


def test_guardar_y_leer():
    """Lo guardado se recupera tal cual, con versión."""
    ruta = ajustes.guardar({"tema": "matrix"})
    assert ruta.is_file()
    assert ajustes.leer()["tema"] == "matrix"


def test_tema_elegido_sin_guardar():
    """Sin tema elegido, None (y no cadena vacía)."""
    assert ajustes.tema_elegido() is None


def test_guardar_y_olvidar_tema():
    """Se elige un tema y luego se olvida: vuelve a None."""
    ajustes.guardar_tema("oceano")
    assert ajustes.tema_elegido() == "oceano"
    ajustes.guardar_tema("")
    assert ajustes.tema_elegido() is None


def test_guardar_tema_propio_y_leerlo():
    """Un tema creado por el usuario sobrevive al cierre de la terminal."""
    base = PALETAS["matrix"]
    propia = Paleta(
        nombre="mi-tema",
        descripcion="tema propio sobre matrix",
        fondo="#001018",
        texto="#c8f0ff",
        cursor="#22d3ee",
        ansi=base.ansi,
    )
    ajustes.guardar_tema_propio(propia)

    recuperados = ajustes.temas_propios()
    assert recuperados["mi-tema"].fondo == "#001018"
    assert recuperados["mi-tema"].ansi == base.ansi
    assert ajustes.buscar_tema("MI-TEMA").cursor == "#22d3ee"


def test_tema_propio_mal_escrito_se_ignora(tmp_path):
    """Un tema con colores inválidos o sin 16 colores no rompe la tabla."""
    ruta = ajustes.ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(
            {
                "version": 1,
                "temas": {
                    "roto": {"fondo": "rojo", "texto": "#fff", "cursor": "#000"},
                    "corto": {
                        "fondo": "#000000",
                        "texto": "#ffffff",
                        "cursor": "#ffff00",
                        "ansi": ["#000000"],
                    },
                    "basura": "no es un diccionario",
                },
            }
        ),
        encoding="utf-8",
    )
    assert ajustes.temas_propios() == {}


def test_buscar_tema_de_fabrica():
    """Los seis temas de la herramienta se encuentran por su nombre."""
    assert ajustes.buscar_tema(" papel ").nombre == "papel"


def test_buscar_tema_inexistente_lista_los_disponibles():
    """El error nombra todos los temas, incluidos los propios."""
    ajustes.guardar({"version": 1, "tema": "matrix", "temas": {"mio": {
        "descripcion": "x",
        "fondo": "#000000",
        "texto": "#ffffff",
        "cursor": "#ffff00",
        "ansi": ["#000000"] * 16,
    }}})
    with pytest.raises(TareasError) as error:
        ajustes.buscar_tema("neon")
    mensaje = str(error.value)
    assert "mio" in mensaje
    for nombre in PALETAS:
        assert nombre in mensaje


def test_guardar_en_carpeta_imposible_da_error_humano(tmp_path):
    """Si no se puede escribir, se explica en vez de enseñar un traceback."""
    ajustes.ruta().parent.mkdir(parents=True, exist_ok=True)
    # Un fichero donde debería ir el JSON: escribir dentro falla.
    ajustes.ruta().mkdir()
    with pytest.raises(TareasError) as error:
        ajustes.guardar({"tema": "matrix"})
    assert "No se pudo guardar" in str(error.value)
