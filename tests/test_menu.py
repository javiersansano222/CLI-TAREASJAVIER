"""Pruebas del panel de mando que se abre al ejecutar `tareas` sin argumentos."""

import pytest
from rich.console import Console

from tareas import __version__
from tareas import menu
from tareas.cli import app


def _texto(monkeypatch, ancho: int = 80) -> str:
    """Pinta el menú en una consola de prueba y devuelve el texto plano."""
    consola = Console(record=True, width=ancho, no_color=True)
    monkeypatch.setattr(menu, "consola", consola)
    menu._pintar_menu(app)
    return consola.export_text()


def test_panel_muestra_cabecera_categorias_y_pie(monkeypatch):
    texto = _texto(monkeypatch)

    assert f"tareas {__version__}" in texto
    assert "Empieza por aquí" in texto
    for categoria in ("ARCHIVOS", "SISTEMA", "APRENDER", "SEGURIDAD", "IA"):
        assert categoria in texto
    assert "escribe una orden" in texto
    assert "Consejo:" in texto
    # La tabla antigua con todas las órdenes ya no se imprime.
    assert "Órdenes disponibles" not in texto


def test_todas_las_ordenes_aparecen(monkeypatch):
    texto = _texto(monkeypatch)

    # `version` no se lista: la versión va en la cabecera.
    assert __version__ in texto
    for nombre, _ in menu._ordenes_menu(app):
        if nombre == "version":
            continue
        assert nombre in texto, f"falta «{nombre}» en el menú"


def test_ninguna_orden_se_repite_en_las_categorias():
    datos = menu._datos_categorias(app)
    nombres = [nombre for _, filas in datos for nombre, _ in filas]

    assert len(nombres) == len(set(nombres))


def test_orden_nueva_cae_en_otras(monkeypatch):
    monkeypatch.setattr(
        menu,
        "_ordenes_menu",
        lambda _app: [("nueva", "Hace algo nuevo.")],
    )

    assert menu._datos_categorias(app) == [
        ("OTRAS", [("nueva", "Hace algo nuevo")]),
    ]


def test_atajos_coinciden_con_los_ejemplos():
    for numero, comando, _ in menu.EJEMPLOS:
        assert " ".join(menu.ATAJOS_INICIO[numero]) == comando


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1", ["informe"]),
        ("2", ["organizar", "--simular"]),
        ("3", ["historial"]),
    ],
)
def test_atajos_numericos_ejecutan_la_orden(monkeypatch, entrada, esperado):
    llamadas: list[list[str]] = []
    entradas = iter([entrada, "salir"])

    class ConsolaFalsa:
        width = 80
        legacy_windows = False

        def print(self, *_args, **_kwargs):
            pass

        def input(self, *_args, **_kwargs):
            return next(entradas)

    monkeypatch.setattr(menu, "consola", ConsolaFalsa())
    monkeypatch.setattr(menu, "_pintar_menu", lambda _app: None)
    monkeypatch.setattr(
        menu, "_ejecutar", lambda _app, partes: llamadas.append(partes)
    )

    menu._bucle_menu(app)

    assert llamadas == [esperado]


def test_consejo_es_uno_de_los_definidos(monkeypatch):
    texto = _texto(monkeypatch)

    assert any(consejo in texto for consejo in menu.CONSEJOS)


def test_el_menu_cabe_en_una_pantalla(monkeypatch):
    texto = _texto(monkeypatch, ancho=80)

    assert len(texto.splitlines()) <= 26


def test_anchos_estrechos_no_rompen_el_menu(monkeypatch):
    texto = _texto(monkeypatch, ancho=60)

    assert "Empieza por aquí" in texto
    assert "escribe una orden" in texto
    assert len(texto.splitlines()) <= 26


def test_a_72_columnas_tambien_cabe(monkeypatch):
    texto = _texto(monkeypatch, ancho=72)

    assert "ARCHIVOS" in texto
    assert "escribe una orden" in texto
    assert len(texto.splitlines()) <= 26


def test_en_pantallas_anchas_no_se_estira_del_todo(monkeypatch):
    texto = _texto(monkeypatch, ancho=120)

    for linea in texto.splitlines():
        assert len(linea) <= menu.ANCHO_MAXIMO, linea
