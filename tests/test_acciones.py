"""Tests for acciones.py - clases de acción."""

from pathlib import Path
import tempfile

import pytest

from tareas.acciones import (
    Accion,
    AccionIA,
    MirarEspacio,
    Resultado,
    Mover,
    Copiar,
    Renombrar,
    Borrar,
    Resumir,
    leer_texto,
)


def test_mirar_espacio_tipo():
    """Test que MirarEspacio tiene tipo correcto."""
    assert MirarEspacio.tipo == "mirar_espacio"


def test_mirar_espacio_registro():
    """Test que MirarEspacio está registrado en Accion._registro."""
    assert "mirar_espacio" in Accion._registro


def test_accion_subclases_registradas():
    """Test que todas las subclases se registran."""
    assert Accion._registro["mover"] == Mover
    assert Accion._registro["copiar"] == Copiar
    assert Accion._registro["renombrar"] == Renombrar
    assert Accion._registro["borrar"] == Borrar
    assert Accion._registro["mirar_espacio"] == MirarEspacio


def test_resultado_dataclass():
    """Test que Resultado tiene los campos esperados."""
    resultado = Resultado(Path("/origen"), Path("/destino"), "hecho", "detalle")
    assert resultado.origen == Path("/origen")
    assert resultado.destino == Path("/destino")
    assert resultado.estado == "hecho"
    assert resultado.detalle == "detalle"


def test_mover_tipo():
    """Test tipo Mover."""
    assert Mover.tipo == "mover"


def test_copiar_tipo():
    """Test tipo Copiar."""
    assert Copiar.tipo == "copiar"


def test_renombrar_tipo():
    """Test tipo Renombrar."""
    assert Renombrar.tipo == "renombrar"


def test_borrar_tipo():
    """Test tipo Borrar."""
    assert Borrar.tipo == "borrar"


def test_resumir_registro_y_necesita_ia():
    """Resumir se registra por su tipo y solo él pide proveedor IA."""
    assert Accion._registro["resumir"] == Resumir
    assert Resumir.necesita_ia is True
    assert Mover.necesita_ia is False
    assert isinstance(Resumir({"nombre": "x", "descripcion": "y", "tipo": "resumir"}), AccionIA)


def test_leer_texto_txt_y_tope(tmp_path):
    """Lee un .txt y lo corta al tope indicado."""
    fichero = tmp_path / "notas.txt"
    fichero.write_text("a" * 500, encoding="utf-8")
    assert leer_texto(fichero, 100) == "a" * 100


def test_leer_texto_md(tmp_path):
    """Lee un .md conservando el formato."""
    fichero = tmp_path / "tema.md"
    fichero.write_text("# Título\n\nviñeta", encoding="utf-8")
    assert leer_texto(fichero, 1000).startswith("# Título")


def test_leer_texto_formato_no_valido(tmp_path):
    """Un formato que no es texto da ValueError (la acción lo salta)."""
    fichero = tmp_path / "foto.png"
    fichero.write_bytes(b"PNG")
    with pytest.raises(ValueError):
        leer_texto(fichero, 100)


def test_presupuesto_sin_gastar():
    """En simulación solo se cuenta: caracteres y tokens estimados."""
    resumir = Resumir(
        {
            "nombre": "resumir-apuntes",
            "descripcion": "resumen",
            "tipo": "resumir",
            "instrucciones": "resume",
        }
    )
    detalle = resumir.presupuesto(1200)
    assert "1200 caracteres" in detalle
    assert "300 tokens" in detalle
    assert "sin gastar" in detalle


def test_resumir_sin_proveedor_no_gasta():
    """Sin proveedor inyectado, preguntar avisa en vez de intentar la red."""
    from tareas.errores import IANoDisponible

    resumir = Resumir(
        {
            "nombre": "resumir-apuntes",
            "descripcion": "resumen",
            "tipo": "resumir",
            "instrucciones": "resume",
        }
    )
    with pytest.raises(IANoDisponible):
        resumir.preguntar("sistema", Path("apunte.md"), "texto")