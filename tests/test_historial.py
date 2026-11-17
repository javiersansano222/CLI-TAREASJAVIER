"""Pruebas de historial.py y de las órdenes «historial» y «deshacer»."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import historial
from tareas.acciones import Resultado
from tareas.cli import app
from tareas.errores import TareasError

runner = CliRunner()
COLORES = re.compile(r"\x1b\[[0-9;]*m")


def salida(resultado) -> str:
    """stdout + stderr sin colores y con los espacios normalizados."""
    texto = (resultado.output or "") + (getattr(resultado, "stderr", "") or "")
    return " ".join(COLORES.sub("", texto).split())


def test_registrar_apunta_solo_lo_que_cambio(tmp_path):
    """Los simulados y los errores no ensucian el historial."""
    origen = tmp_path / "a.txt"
    destino = tmp_path / "docs" / "a.txt"
    resultados = [
        Resultado(origen, destino, "movido"),
        Resultado(origen, tmp_path / "b.txt", "simulado"),
        Resultado(origen, None, "error", "sin permiso"),
    ]

    assert historial.registrar("mover", resultados, "mover") is not None
    lotes = historial.leer()

    assert len(lotes) == 1
    assert lotes[0]["orden"] == "mover"
    assert lotes[0]["operaciones"] == [
        {
            "tipo": "mover",
            "origen": str(origen),
            "destino": str(destino),
        }
    ]


def test_registrar_guarda_rutas_absolutas():
    """Aunque la orden use rutas relativas, el historial guarda rutas completas."""
    resultado = Resultado(Path("a.txt"), Path("docs") / "a.txt", "movido")

    historial.registrar("mover", [resultado], "mover")

    operacion = historial.leer()[0]["operaciones"][0]
    assert Path(operacion["origen"]).is_absolute()
    assert Path(operacion["destino"]).is_absolute()


def test_sin_operaciones_no_escribe_nada():
    """Un lote vacío no crea el fichero de historial."""
    resultado = Resultado(Path("a.txt"), Path("b.txt"), "simulado")
    assert historial.registrar("mover", [resultado], "mover") is None
    assert historial.leer() == []


def test_leer_ignora_lineas_rotas(tmp_path):
    """Una línea corrupta no impide leer el resto del historial."""
    ruta = historial.ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    valido = json.dumps(
        {"version": 1, "fecha": "2026-11-17 10:00:00", "orden": "mover", "operaciones": []}
    )
    ruta.write_text(f"{{esto no es json}}\n{valido}\n", encoding="utf-8")

    lotes = historial.leer()
    assert len(lotes) == 1
    assert lotes[0]["orden"] == "mover"


def test_deshacer_devuelve_un_movimiento(tmp_path):
    """Deshacer mover devuelve el fichero a su carpeta original."""
    origen = tmp_path / "a.txt"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "docs" / "a.txt"
    destino.parent.mkdir()
    origen.rename(destino)
    historial.registrar("mover", [Resultado(origen, destino, "movido")], "mover")

    informe = historial.deshacer()

    assert informe.deshechas == 1
    assert origen.is_file()
    assert not destino.exists()
    assert historial.leer() == []


def test_deshacer_devuelve_un_renombrado(tmp_path):
    """Deshacer renombrar recupera el nombre anterior."""
    original = tmp_path / "viejo.txt"
    original.write_text("x", encoding="utf-8")
    nuevo = tmp_path / "nuevo.txt"
    original.rename(nuevo)
    historial.registrar(
        "ejecutar renombrar", [Resultado(original, nuevo, "hecho")], "renombrar"
    )

    informe = historial.deshacer()

    assert informe.deshechas == 1
    assert original.is_file()
    assert not nuevo.exists()


def test_deshacer_copiar_manda_la_copia_a_la_papelera(tmp_path, monkeypatch):
    """Deshacer copiar retira solo la copia, sin tocar el original."""
    enviados: list[Path] = []
    monkeypatch.setattr(
        historial, "send2trash", lambda ruta: enviados.append(Path(ruta))
    )
    original = tmp_path / "a.txt"
    original.write_text("x", encoding="utf-8")
    copia = tmp_path / "copia.txt"
    copia.write_text("x", encoding="utf-8")
    historial.registrar("mover", [Resultado(original, copia, "copiado")], "copiar")

    informe = historial.deshacer()

    assert informe.deshechas == 1
    assert enviados == [copia]
    assert original.is_file()


def test_deshacer_salta_lotes_irreversibles(tmp_path):
    """Un lote reciente e irreversible no bloquea deshacer uno anterior."""
    origen = tmp_path / "a.txt"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "docs" / "a.txt"
    destino.parent.mkdir()
    origen.rename(destino)
    historial.registrar("mover", [Resultado(origen, destino, "movido")], "mover")
    historial.registrar(
        "ejecutar borrar", [Resultado(tmp_path / "x.txt", None, "hecho")], "borrar"
    )

    informe = historial.deshacer()

    assert informe.deshechas == 1
    assert informe.omitidos == 1
    assert "mover" == informe.orden
    assert origen.is_file()
    restantes = historial.leer()
    assert len(restantes) == 1
    assert restantes[0]["orden"] == "ejecutar borrar"


def test_deshacer_simular_no_toca_nada(tmp_path):
    """Con --simular se informa, pero el fichero y el historial se quedan."""
    origen = tmp_path / "a.txt"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "docs" / "a.txt"
    destino.parent.mkdir()
    origen.rename(destino)
    historial.registrar("mover", [Resultado(origen, destino, "movido")], "mover")

    informe = historial.deshacer(simular=True)

    assert informe.deshechas == 0
    assert informe.simuladas == 1
    assert destino.is_file()
    assert not origen.exists()
    assert len(historial.leer()) == 1


def test_deshacer_borrar_avisa_y_conserva_el_lote(tmp_path):
    """Lo que no se puede revertir se avisa y no se pierde del historial."""
    borrado = tmp_path / "x.txt"
    historial.registrar(
        "ejecutar borrar", [Resultado(borrado, None, "hecho")], "borrar"
    )

    informe = historial.deshacer()

    assert informe.deshechas == 0
    assert informe.operaciones[0].estado == "saltado"
    assert "no se puede deshacer" in informe.operaciones[0].detalle
    assert len(historial.leer()) == 1


def test_deshacer_sin_historial_falla():
    """Sin nada apuntado, el error es humano y no un traceback."""
    with pytest.raises(TareasError) as error:
        historial.deshacer()
    assert "historial está vacío" in str(error.value)


def test_cli_mover_se_apunta_y_se_deshace(tmp_path):
    """La orden mover se ve en historial y deshacer la revierte."""
    origen = tmp_path / "a.txt"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "docs"

    assert runner.invoke(app, ["mover", str(origen), str(destino)]).exit_code == 0

    listado = runner.invoke(app, ["historial"])
    assert listado.exit_code == 0
    assert "mover" in salida(listado)

    deshecho = runner.invoke(app, ["deshacer"])
    assert deshecho.exit_code == 0
    assert origen.is_file()
    assert not (destino / "a.txt").exists()


def test_cli_mover_con_rutas_relativas_y_deshacer(tmp_path):
    """Lo apuntado es absoluto, así que deshacer vale aunque cambie la carpeta."""
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    assert runner.invoke(app, ["mover", "a.txt", "docs"]).exit_code == 0

    deshecho = runner.invoke(app, ["deshacer"])

    assert deshecho.exit_code == 0
    assert (tmp_path / "a.txt").is_file()
    assert not (tmp_path / "docs" / "a.txt").exists()


def test_cli_mover_simulado_no_apunta_nada(tmp_path):
    """Una simulación no debe aparecer en el historial."""
    origen = tmp_path / "a.txt"
    origen.write_text("x", encoding="utf-8")

    runner.invoke(app, ["mover", str(origen), str(tmp_path / "docs"), "--simular"])

    listado = runner.invoke(app, ["historial"])
    assert "vacío" in salida(listado)


def test_cli_deshacer_simular_conserva_el_lote(tmp_path):
    """La simulación de deshacer deja el fichero y el historial como estaban."""
    origen = tmp_path / "a.txt"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "docs"
    runner.invoke(app, ["mover", str(origen), str(destino)])

    simulado = runner.invoke(app, ["deshacer", "--simular"])
    assert simulado.exit_code == 0
    assert (destino / "a.txt").is_file()
    assert not origen.exists()

    listado = runner.invoke(app, ["historial"])
    assert "mover" in salida(listado)


def test_cli_organizar_y_deshacer(tmp_path):
    """Organizar apunta un lote con varias operaciones y se puede revertir."""
    (tmp_path / "apunte.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "foto.png").write_text("x", encoding="utf-8")

    assert runner.invoke(app, ["organizar", str(tmp_path)]).exit_code == 0
    assert (tmp_path / "Documentos" / "apunte.pdf").is_file()

    deshecho = runner.invoke(app, ["deshacer"])
    assert deshecho.exit_code == 0
    assert (tmp_path / "apunte.pdf").is_file()
    assert (tmp_path / "foto.png").is_file()


def test_cli_deshacer_sin_historial(tmp_path):
    """Sin historial, deshacer sale con código 1 y un mensaje claro."""
    resultado = runner.invoke(app, ["deshacer"])
    assert resultado.exit_code == 1
    assert "historial está vacío" in salida(resultado)
