"""La CLI desde fuera: CliRunner ejecuta las órdenes como si las tecleara alguien.

Una prueba por código de salida (0, 1, 2, 3 y 4). Nada de subprocess ni de
`uv run` anidado: más rápido y funciona igual en Linux, Windows y macOS.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tareas.cli import app

runner = CliRunner()

ACCION_BORRAR = {"nombre": "a", "descripcion": "x", "tipo": "borrar"}
ACCION_RESUMIR = {
    "nombre": "res",
    "descripcion": "x",
    "tipo": "resumir",
    "instrucciones": "resume el apunte en cinco viñetas",
}


def salida(resultado) -> str:
    """stdout + stderr: Rich manda los errores por la salida de error."""
    return (resultado.output or "") + (getattr(resultado, "stderr", "") or "")


def test_la_ayuda_funciona():
    """tareas --help sale con 0 y enseña las órdenes."""
    resultado = runner.invoke(app, ["--help"])
    assert resultado.exit_code == 0
    assert "ejecutar" in salida(resultado)


def test_version_sale_con_0():
    """tareas version dice la versión y termina bien."""
    resultado = runner.invoke(app, ["version"])
    assert resultado.exit_code == 0
    assert "tareas " in salida(resultado)


def test_validar_una_config_buena_sale_con_0(escribir_config):
    """Camino feliz de la CLI: el JSON se valida y se cuenta."""
    ruta = escribir_config(
        [
            {
                "nombre": "ordenar",
                "descripcion": "Mueve los PDF",
                "tipo": "mover",
                "destino": "~/PDF",
            }
        ]
    )
    resultado = runner.invoke(app, ["--config", str(ruta), "validar"])
    assert resultado.exit_code == 0
    assert "1 acción válida" in salida(resultado)


def test_accion_que_no_existe_sale_con_1(escribir_config, descargas):
    """Código 1: la orden existe, pero la acción pedida no."""
    ruta = escribir_config([ACCION_BORRAR])
    resultado = runner.invoke(
        app, ["--config", str(ruta), "ejecutar", "inventada", str(descargas)]
    )
    assert resultado.exit_code == 1
    assert "No hay ninguna acción" in salida(resultado)


def test_opcion_que_no_existe_sale_con_2():
    """Código 2: error de uso, la opción no existe."""
    resultado = runner.invoke(app, ["listar", "--inventada"])
    assert resultado.exit_code == 2
    assert "--inventada" in salida(resultado)


def test_json_roto_sale_con_3_y_sin_traza(escribir_config):
    """Código 3: configuración inválida, con mensaje humano y sin traceback."""
    ruta = escribir_config('{"acciones": [ }')
    resultado = runner.invoke(app, ["--config", str(ruta), "validar"])
    assert resultado.exit_code == 3
    assert "no es JSON válido" in salida(resultado)
    assert "Traceback" not in salida(resultado)


def test_ia_sin_clave_sale_con_4(escribir_config, tmp_path):
    """Código 4: sin clave no hay IA, pero las acciones sin IA siguen."""
    ruta = escribir_config([ACCION_RESUMIR])
    resultado = runner.invoke(
        app, ["--config", str(ruta), "ejecutar", "res", str(tmp_path)]
    )
    assert resultado.exit_code == 4
    assert "siguen funcionando" in salida(resultado)
