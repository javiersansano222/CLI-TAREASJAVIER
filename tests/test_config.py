"""Tests for config.py - validación de acciones.json."""

from pathlib import Path

import pytest

from tareas.config import cargar, ConfigError, AccionNoValida


def test_cargar_acciones_validas():
    """Test que carga y valida acciones.json correcto."""
    ruta = Path("acciones.json")
    acciones = cargar(ruta)
    assert len(acciones) >= 5  # crece con cada acción nueva del proyecto


def test_cargar_acciones_sin_fichero(tmp_path: Path):
    """Test que falla si no encuentra el fichero."""
    ruta_inexistente = tmp_path / "nonexistent.json"
    with pytest.raises(ConfigError):
        cargar(ruta_inexistente)


def test_version_invalida(tmp_path: Path):
    """Test que falla si la versión no es 1."""
    import json

    datos = {"version": 2, "acciones": []}
    ruta = tmp_path / "test_acciones.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(ConfigError) as exc:
        cargar(ruta)
    assert "no es compatible" in str(exc.value)


def test_accion_sin_nombre(tmp_path: Path):
    """Test que falla si una acción no tiene nombre."""
    import json

    datos = {"version": 1, "acciones": [{"descripcion": "sin nombre"}]}
    ruta = tmp_path / "test_acciones.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(AccionNoValida):
        cargar(ruta)


def test_accion_repetida_nombre(tmp_path: Path):
    """Test que falla si dos acciones tienen el mismo nombre."""
    import json

    datos = {"version": 1, "acciones": [
        {"nombre": "misma", "descripcion": "una", "tipo": "mover", "destino": "/tmp"},
        {"nombre": "misma", "descripcion": "otra", "tipo": "mover", "destino": "/tmp"},
    ]}
    ruta = tmp_path / "test_acciones.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(AccionNoValida) as exc:
        cargar(ruta)
    assert "repetido" in str(exc.value).lower()