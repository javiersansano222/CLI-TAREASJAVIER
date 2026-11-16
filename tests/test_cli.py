"""La CLI desde fuera: CliRunner ejecuta las órdenes como si las tecleara alguien.

Una prueba por código de salida (0, 1, 2, 3 y 4). Nada de subprocess ni de
`uv run` anidado: más rápido y funciona igual en Linux, Windows y macOS.
"""

from __future__ import annotations

import re

import pytest
from typer.testing import CliRunner

from tareas import ajustes
from tareas.cli import app

runner = CliRunner()

ACCION_BORRAR = {"nombre": "a", "descripcion": "x", "tipo": "borrar"}
ACCION_RESUMIR = {
    "nombre": "res",
    "descripcion": "x",
    "tipo": "resumir",
    "instrucciones": "resume el apunte en cinco viñetas",
}


# Click colorea las opciones cuando la terminal lo admite y en GitHub Actions
# lo hace: "--inventada" llega partido por los códigos de color. Se quitan antes
# de mirar el texto para que la prueba no dependa del entorno.
COLORES = re.compile(r"\x1b\[[0-9;]*m")


def salida(resultado) -> str:
    """stdout + stderr, sin colores: Rich manda los errores por la salida de error."""
    texto = (resultado.output or "") + (getattr(resultado, "stderr", "") or "")
    return COLORES.sub("", texto)


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
    # Con FORCE_COLOR se pinta igual que en GitHub Actions; salida() quita los
    # colores antes de comparar, así la prueba vale en cualquier terminal.
    resultado = runner.invoke(
        app, ["listar", "--inventada"], env={"FORCE_COLOR": "1"}
    )
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


def test_doctor_avisa_de_ia_sin_configurar_sin_contarlo_como_aviso(
    escribir_config, tmp_path
):
    """La IA sin clave se muestra como «sin configurar», no como aviso."""
    (tmp_path / "Downloads").mkdir()
    ruta = escribir_config([ACCION_RESUMIR])
    resultado = runner.invoke(app, ["--config", str(ruta), "doctor"])
    assert resultado.exit_code == 0
    assert "Sin configurar" in salida(resultado)
    assert "0 avisos" not in salida(resultado)


def test_tema_sin_argumentos_lista_los_disponibles():
    """`tareas tema` no cambia nada: enseña los temas que hay."""
    resultado = runner.invoke(app, ["tema"])
    assert resultado.exit_code == 0
    texto = salida(resultado)
    for nombre in ("medianoche", "matrix", "papel", "ambar", "oceano", "contraste"):
        assert nombre in texto


def test_tema_vista_previa_no_guarda_nada():
    """`--ver` enseña el tema y no deja rastro en los ajustes."""
    resultado = runner.invoke(app, ["tema", "--ver", "matrix"])
    assert resultado.exit_code == 0
    assert "matrix" in salida(resultado)
    assert not ajustes.ruta().exists()


def test_tema_aplica_y_lo_recuerda():
    """Aplicar manda las secuencias OSC y guarda el tema para el menú."""
    resultado = runner.invoke(app, ["tema", "matrix"], env={"WT_SESSION": "1"})
    assert resultado.exit_code == 0
    texto = salida(resultado)
    assert "\x1b]11;rgb:05/08/05" in texto  # fondo de matrix
    assert "aplicado" in texto
    assert ajustes.tema_elegido() == "matrix"


def test_tema_avisa_si_el_terminal_no_admite_colores():
    """En un terminal sin OSC no se miente: se avisa y no se guarda nada."""
    resultado = runner.invoke(
        app, ["tema", "matrix"], env={"TERM": "dumb", "WT_SESSION": ""}
    )
    assert resultado.exit_code == 0
    assert "no admite" in salida(resultado)
    assert ajustes.tema_elegido() is None


def test_tema_crear_guarda_el_tema_propio():
    """Un tema propio se crea con tres colores y se puede volver a usar."""
    resultado = runner.invoke(
        app,
        [
            "tema",
            "--crear",
            "mi-tema",
            "--desde",
            "oceano",
            "--fondo",
            "#001018",
            "--texto",
            "#c8f0ff",
            "--cursor",
            "#22d3ee",
        ],
    )
    assert resultado.exit_code == 0
    assert "guardado" in salida(resultado)
    propio = ajustes.buscar_tema("mi-tema")
    assert propio.fondo == "#001018"
    assert len(propio.ansi) == 16


@pytest.mark.parametrize(
    "argumentos",
    [
        ["--crear", "con espacios", "--fondo", "#000000", "--texto", "#ffffff", "--cursor", "#ffff00"],
        ["--crear", "otro", "--fondo", "rojo", "--texto", "#ffffff", "--cursor", "#ffff00"],
        ["--crear", "tercero"],
    ],
)
def test_tema_crear_con_datos_malos_sale_con_2(argumentos):
    """Un error de uso (nombre, color o falta de colores) es código 2."""
    resultado = runner.invoke(app, ["tema", *argumentos])
    assert resultado.exit_code == 2
    assert "Traceback" not in salida(resultado)


def test_tema_restablecer_olvida_el_tema():
    """Restablecer devuelve los colores y no vuelve a aplicarse solo."""
    ajustes.guardar_tema("matrix")
    resultado = runner.invoke(app, ["tema", "--restablecer"])
    assert resultado.exit_code == 0
    assert "\x1b]110;" in salida(resultado)
    assert ajustes.tema_elegido() is None


def test_tema_exportar_escribe_los_tres_ficheros(tmp_path):
    """Exportar deja los ficheros de los tres terminales en el destino."""
    destino = tmp_path / "salida"
    resultado = runner.invoke(
        app, ["tema", "--exportar", "papel", "--destino", str(destino)]
    )
    assert resultado.exit_code == 0
    assert len(list(destino.iterdir())) == 3


def test_tema_desconocido_sale_con_1():
    """Código 1: el tema pedido no existe y el mensaje dice cuáles hay."""
    resultado = runner.invoke(app, ["tema", "neon"])
    assert resultado.exit_code == 1
    assert "No hay ningún tema" in salida(resultado)


def test_organizar_simular_no_mueve_nada(tmp_path):
    """`organizar --simular` enseña el plan y deja los ficheros donde están."""
    (tmp_path / "nota.pdf").write_text("x", encoding="utf-8")
    resultado = runner.invoke(app, ["organizar", str(tmp_path), "--simular"])
    assert resultado.exit_code == 0
    assert "simulado" in salida(resultado)
    assert "SIMULACIÓN" in salida(resultado)
    assert (tmp_path / "nota.pdf").is_file()
    assert not (tmp_path / "Documentos").exists()


def test_organizar_mueve_los_ficheros(tmp_path):
    """Sin --simular, el fichero acaba en la carpeta de su tipo."""
    (tmp_path / "foto.JPG").write_text("x", encoding="utf-8")
    resultado = runner.invoke(app, ["organizar", str(tmp_path)])
    assert resultado.exit_code == 0
    assert "movido" in salida(resultado)
    assert (tmp_path / "Imagenes" / "foto.JPG").is_file()
    assert not (tmp_path / "foto.JPG").exists()


def test_organizar_carpeta_inexistente_sale_con_1(tmp_path):
    """Código 1: la carpeta no existe y se explica sin traceback."""
    resultado = runner.invoke(app, ["organizar", str(tmp_path / "no-existe")])
    assert resultado.exit_code == 1
    assert "no existe" in salida(resultado)
    assert "Traceback" not in salida(resultado)


def test_organizar_aparece_en_la_ayuda():
    """La orden nueva se lista en `tareas --help`."""
    resultado = runner.invoke(app, ["--help"])
    assert resultado.exit_code == 0
    assert "organizar" in salida(resultado)


def test_mover_simular_no_mueve_nada(tmp_path):
    """`mover --simular` enseña el destino y deja el fichero donde está."""
    (tmp_path / "apuntes.pdf").write_text("x", encoding="utf-8")
    destino = tmp_path / "Documentos"

    resultado = runner.invoke(
        app, ["mover", "apuntes.pdf", str(destino), "--simular"]
    )

    assert resultado.exit_code == 0
    assert "simulado" in salida(resultado)
    assert "SIMULACIÓN" in salida(resultado)
    assert (tmp_path / "apuntes.pdf").is_file()
    assert not destino.exists()


def test_mover_lleva_el_fichero_a_destino(tmp_path):
    """Sin --simular, el fichero acaba en la carpeta indicada."""
    (tmp_path / "apuntes.pdf").write_text("x", encoding="utf-8")
    destino = tmp_path / "Documentos"

    resultado = runner.invoke(app, ["mover", "apuntes.pdf", str(destino)])

    assert resultado.exit_code == 0
    assert "movido" in salida(resultado)
    assert (destino / "apuntes.pdf").is_file()
    assert not (tmp_path / "apuntes.pdf").exists()


def test_mover_copiar_deja_el_original(tmp_path):
    """Con --copiar el fichero sigue en su sitio y aparece la copia."""
    (tmp_path / "apuntes.pdf").write_text("x", encoding="utf-8")
    destino = tmp_path / "Documentos"

    resultado = runner.invoke(
        app, ["mover", "apuntes.pdf", str(destino), "--copiar"]
    )

    assert resultado.exit_code == 0
    assert "copiado" in salida(resultado)
    assert (destino / "apuntes.pdf").is_file()
    assert (tmp_path / "apuntes.pdf").is_file()


def test_mover_fichero_inexistente_sale_con_1(tmp_path):
    """Código 1: no se encuentra el fichero y se explica sin traceback."""
    resultado = runner.invoke(
        app, ["mover", "fantasma.pdf", str(tmp_path / "Documentos")]
    )
    assert resultado.exit_code == 1
    assert "No encuentro" in salida(resultado)
    assert "Traceback" not in salida(resultado)


def test_mover_aparece_en_la_ayuda():
    """La orden nueva se lista en `tareas --help`."""
    resultado = runner.invoke(app, ["--help"])
    assert resultado.exit_code == 0
    assert "mover" in salida(resultado)
