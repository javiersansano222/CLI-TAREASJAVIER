"""Tests for acciones.py - clases de acción."""

from pathlib import Path
import tempfile

import pytest

from tareas.acciones import Accion, MirarEspacio, Resultado, Mover, Copiar, Renombrar, Borrar


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