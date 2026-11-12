"""Tests for motor.py - selección y ejecución de acciones."""

from pathlib import Path

import pytest

from tareas.motor import Motor
from tareas.errores import TareasError


def test_motor_inicializacion():
    """Test que el motor se inicializa con acciones válidas."""
    from tareas.config import cargar
    acciones = cargar(Path("acciones.json"))
    motor = Motor(acciones)
    assert len(motor.acciones) >= 5  # crece con cada acción nueva del proyecto


def test_motor_obtener_accion():
    """Test que obtener una acción por nombre funciona."""
    from tareas.config import cargar
    motor = Motor(cargar(Path("acciones.json")))
    accion = motor.obtener("mirar-espacio")
    assert accion is not None
    assert accion.tipo == "mirar_espacio"


def test_motor_obtener_accion_inexistente():
    """Test que obtener acción inexistente falla."""
    from tareas.config import cargar
    motor = Motor(cargar(Path("acciones.json")))
    with pytest.raises(TareasError) as exc:
        motor.obtener("accion_inexistente")
    assert str(exc.value).lower().__contains__("no hay ninguna acción")


def test_motor_seleccionar_sin_filtro():
    """Test que seleccionar ficheros sin filtro retorna todos."""
    from pathlib import Path
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        # Crear algunos ficheros de prueba
        (carpeta / "fichero1.txt").write_text("hola")
        (carpeta / "fichero2.txt").write_text("mundo")
        (carpeta / "fichero3.png").write_text("imagen")

        from tareas.config import cargar
        motor = Motor(cargar(Path("acciones.json")))
        seleccionados = motor.seleccionar(carpeta, {})
        assert len(seleccionados) == 3


def test_motor_seleccionar_con_extensiones():
    """Test que seleccionar con filtro de extensiones funciona."""
    from pathlib import Path
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        (carpeta / "fichero1.txt").write_text("hola")
        (carpeta / "fichero2.py").write_text("mundo")
        (carpeta / "fichero3.txt").write_text("otro")

        from tareas.config import cargar
        motor = Motor(cargar(Path("acciones.json")))
        seleccionados = motor.seleccionar(carpeta, {"extensiones": [".txt"]})
        assert len(seleccionados) == 2
        assert all(ruta.suffix == ".txt" for ruta in seleccionados)