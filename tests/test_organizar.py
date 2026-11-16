"""Pruebas de organizar.py: clasificar por extensión y mover sin pisar nada."""

from __future__ import annotations

from pathlib import Path

import pytest

from tareas import organizar
from tareas.errores import TareasError


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("nota.pdf", "Documentos"),
        ("foto.JPG", "Imagenes"),
        ("clip.mp4", "Videos"),
        ("cancion.mp3", "Audio"),
        ("paquete.zip", "Comprimidos"),
        ("setup.exe", "Instaladores"),
        ("raro.xyz", "Otros"),
        ("sin_extension", "Otros"),
    ],
)
def test_categoria_por_extension(nombre, esperado):
    """Cada extensión cae en su carpeta, sin importar mayúsculas."""
    assert organizar.categoria(Path(nombre)) == esperado


def test_seleccionar_solo_el_primer_nivel(tmp_path):
    """No entra en subcarpetas ni mueve ficheros ocultos."""
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.pdf").write_text("b", encoding="utf-8")
    (tmp_path / ".oculto").write_text("x", encoding="utf-8")
    (tmp_path / "subcarpeta").mkdir()
    (tmp_path / "subcarpeta" / "c.txt").write_text("c", encoding="utf-8")

    nombres = [ruta.name for ruta in organizar.seleccionar(tmp_path)]
    assert nombres == ["a.txt", "b.pdf"]


def test_carpeta_inexistente_da_error_humano(tmp_path):
    """La carpeta que no existe se explica, sin traceback."""
    with pytest.raises(TareasError) as error:
        organizar.seleccionar(tmp_path / "no-existe")
    assert "no existe" in str(error.value)


def test_carpeta_vacia_no_hace_nada(tmp_path):
    """Sin ficheros, no se crea ninguna carpeta de categoría."""
    assert organizar.ejecutar(tmp_path) == []
    assert list(tmp_path.iterdir()) == []


def test_simular_no_toca_nada(tmp_path):
    """En simulación se dice qué haría, pero el disco queda igual."""
    (tmp_path / "nota.pdf").write_text("x", encoding="utf-8")
    resultados = organizar.ejecutar(tmp_path, simular=True)
    assert resultados[0].estado == "simulado"
    assert (tmp_path / "nota.pdf").is_file()
    assert not (tmp_path / "Documentos").exists()


def test_mover_de_verdad(tmp_path):
    """Al mover, el fichero acaba en su carpeta y desaparece del origen."""
    (tmp_path / "nota.pdf").write_text("x", encoding="utf-8")
    resultados = organizar.ejecutar(tmp_path)
    assert resultados[0].estado == "movido"
    assert (tmp_path / "Documentos" / "nota.pdf").is_file()
    assert not (tmp_path / "nota.pdf").exists()


def test_copiar_deja_el_original(tmp_path):
    """Con --copiar hay dos copias: la de origen y la clasificada."""
    (tmp_path / "nota.pdf").write_text("x", encoding="utf-8")
    resultados = organizar.ejecutar(tmp_path, copiar=True)
    assert resultados[0].estado == "copiado"
    assert (tmp_path / "Documentos" / "nota.pdf").is_file()
    assert (tmp_path / "nota.pdf").is_file()


def test_nunca_sobrescribe(tmp_path):
    """Si ya hay un fichero con ese nombre, se añade « (1)»."""
    destino = tmp_path / "Documentos"
    destino.mkdir()
    (destino / "nota.pdf").write_text("viejo", encoding="utf-8")
    (tmp_path / "nota.pdf").write_text("nuevo", encoding="utf-8")

    organizar.ejecutar(tmp_path)

    assert (destino / "nota (1).pdf").read_text(encoding="utf-8") == "nuevo"
    assert (destino / "nota.pdf").read_text(encoding="utf-8") == "viejo"
