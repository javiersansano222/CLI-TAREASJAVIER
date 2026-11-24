"""Pruebas de buscar.py: coincidencias, filtros y casos feos."""

from __future__ import annotations

import os
import time

import pytest

from tareas import buscar
from tareas.errores import TareasError


def _toca(ruta, contenido="x"):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_subcadena_sin_asteriscos_encuentra_nombres_compuestos(tmp_path):
    _toca(tmp_path / "apuntes de redes.docx")
    _toca(tmp_path / "foto.jpg")

    resultados = buscar.buscar("redes", carpeta=tmp_path)

    assert [c.ruta.name for c in resultados] == ["apuntes de redes.docx"]


def test_asterisco_actua_como_global(tmp_path):
    _toca(tmp_path / "IMG_2041.jpg")
    _toca(tmp_path / "IMG_2042.jpg")
    _toca(tmp_path / "otro.txt")

    resultados = buscar.buscar("IMG_*.jpg", carpeta=tmp_path)

    assert sorted(c.ruta.name for c in resultados) == ["IMG_2041.jpg", "IMG_2042.jpg"]


def test_regex_con_flag(tmp_path):
    _toca(tmp_path / "a1.txt")
    _toca(tmp_path / "a2.txt")
    _toca(tmp_path / "ab.txt")

    resultados = buscar.buscar("a[0-9]\\.txt", carpeta=tmp_path, regex=True)

    assert sorted(c.ruta.name for c in resultados) == ["a1.txt", "a2.txt"]


def test_ext_filtro_normaliza_punto_y_mayusculas(tmp_path):
    _toca(tmp_path / "factura.PDF")
    _toca(tmp_path / "nota.txt")

    resultados = buscar.buscar("factura", carpeta=tmp_path, extensiones=["PDF"])

    assert [c.ruta.name for c in resultados] == ["factura.PDF"]


def test_ext_multiple(tmp_path):
    _toca(tmp_path / "a.pdf")
    _toca(tmp_path / "b.jpg")
    _toca(tmp_path / "c.txt")

    resultados = buscar.buscar("a", carpeta=tmp_path, extensiones=["pdf", "jpg"])
    assert sorted(c.ruta.name for c in resultados) == ["a.pdf"]


def test_texto_vacio_es_error(tmp_path):
    with pytest.raises(TareasError, match="Dime qué busco"):
        buscar.buscar("   ", carpeta=tmp_path)


def test_carpeta_inexistente_es_error(tmp_path):
    with pytest.raises(TareasError):
        buscar.buscar("x", carpeta=tmp_path / "no-existe")


def test_regex_rota_es_error(tmp_path):
    with pytest.raises(TareasError, match="expresión regular"):
        buscar.buscar("[(", carpeta=tmp_path, regex=True)


def test_ext_sin_puntos_es_error(tmp_path):
    with pytest.raises(TareasError):
        buscar.buscar("x", carpeta=tmp_path, extensiones=["."])


def test_omite_carpetas_ruidosas(tmp_path):
    _toca(tmp_path / "src" / "nota.txt")
    _toca(tmp_path / ".venv" / "nota.txt")

    resultados = buscar.buscar("nota", carpeta=tmp_path)

    assert [str(c.ruta.relative_to(tmp_path)) for c in resultados] == [
        "src/nota.txt"
    ]


def test_sin_resultados_devuelve_lista_vacia(tmp_path):
    (tmp_path / "nada.txt").write_text("nada", encoding="utf-8")
    assert buscar.buscar("fantasma", carpeta=tmp_path) == []


def test_ordenar_por_fecha_descendente(tmp_path):
    uno = _toca(tmp_path / "uno.txt")
    dos = _toca(tmp_path / "dos.txt")
    viejo = time.time() - 10_000
    os.utime(uno, (viejo, viejo))

    resultados = buscar.buscar(".txt", carpeta=tmp_path)
    assert [c.ruta.name for c in resultados] == ["dos.txt", "uno.txt"]
