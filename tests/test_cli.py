"""Tests for cli.py - pruebas de la CLI de tareas."""

import subprocess

import pytest


def test_cli_validar():
    """Test que `tareas validar` retorna código 0."""
    result = subprocess.run(
        ["uv", "run", "tareas", "validar"],
        capture_output=True,
        text=True,
        cwd="/home/javsanmar6/Documents/cli-tareas",
    )
    assert result.returncode == 0
    assert "5 acciones válidas" in result.stdout


def test_cli_mirar_espacio_simular():
    """Test que `tareas mirar-espacio --simular` funciona."""
    result = subprocess.run(
        ["uv", "run", "tareas", "mirar-espacio", "--simular"],
        capture_output=True,
        text=True,
        cwd="/home/javsanmar6/Documents/cli-tareas",
    )
    assert result.returncode == 0
    assert "Espacio en" in result.stdout
    assert "Fichero" in result.stdout


def test_cli_acciones():
    """Test que `tareas acciones` muestra las 5 acciones."""
    result = subprocess.run(
        ["uv", "run", "tareas", "acciones"],
        capture_output=True,
        text=True,
        cwd="/home/javsanmar6/Documents/cli-tareas",
    )
    assert result.returncode == 0
    assert "mirar-espacio" in result.stdout
    assert "mirar_espacio" in result.stdout


def test_cli_ayuda_general():
    """Test que `tareas --help` funciona."""
    result = subprocess.run(
        ["uv", "run", "tareas", "--help"],
        capture_output=True,
        text=True,
        cwd="/home/javsanmar6/Documents/cli-tareas",
    )
    assert result.returncode == 0
    assert "mirar-espacio" in result.stdout


def test_cli_version():
    """Test que `tareas version` funciona."""
    result = subprocess.run(
        ["uv", "run", "tareas", "version"],
        capture_output=True,
        text=True,
        cwd="/home/javsanmar6/Documents/cli-tareas",
    )
    assert result.returncode == 0
    assert "tareas" in result.stdout.lower()