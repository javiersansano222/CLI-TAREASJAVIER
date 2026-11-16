"""Pruebas de mover.py: localizar un fichero concreto y llevarlo a otra carpeta."""

from __future__ import annotations

from pathlib import Path

import pytest

from tareas import mover
from tareas.errores import TareasError


def test_localizar_ruta_completa(tmp_path):
    """Con una ruta normal, se devuelve tal cual."""
    fichero = tmp_path / "apuntes.pdf"
    fichero.write_text("x", encoding="utf-8")
    assert mover.localizar(fichero) == fichero


def test_localizar_solo_el_nombre_en_la_carpeta_actual(tmp_path):
    """Si el fichero está donde estás, no hace falta escribir la ruta."""
    (tmp_path / "apuntes.pdf").write_text("x", encoding="utf-8")
    assert mover.localizar("apuntes.pdf") == Path("apuntes.pdf")


def test_localizar_solo_el_nombre_en_descargas(tmp_path):
    """Si no está en la carpeta actual, se busca en Descargas."""
    descargas = tmp_path / "Descargas"
    descargas.mkdir()
    (descargas / "apuntes.pdf").write_text("x", encoding="utf-8")
    assert mover.localizar("apuntes.pdf") == descargas / "apuntes.pdf"


def test_localizar_no_encontrado_explica_donde_busco(tmp_path):
    """Si no aparece, el mensaje dice las rutas probadas."""
    with pytest.raises(TareasError) as error:
        mover.localizar("fantasma.pdf")
    mensaje = str(error.value)
    assert "No encuentro" in mensaje
    assert "fantasma.pdf" in mensaje
    assert "Lo he buscado en" in mensaje


def test_mover_de_verdad(tmp_path):
    """El fichero acaba en destino y desaparece del origen."""
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "Documentos"

    resultado = mover.ejecutar(origen, destino)

    assert resultado.estado == "movido"
    assert resultado.destino == destino / "apuntes.pdf"
    assert (destino / "apuntes.pdf").is_file()
    assert not origen.exists()


def test_copiar_deja_el_original(tmp_path):
    """Con --copiar hay dos copias."""
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "Documentos"

    resultado = mover.ejecutar(origen, destino, copiar=True)

    assert resultado.estado == "copiado"
    assert (destino / "apuntes.pdf").is_file()
    assert origen.is_file()


def test_simular_no_toca_nada(tmp_path):
    """En simulación se enseña el destino, pero el disco queda igual."""
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "Documentos"

    resultado = mover.ejecutar(origen, destino, simular=True)

    assert resultado.estado == "simulado"
    assert resultado.destino == destino / "apuntes.pdf"
    assert origen.is_file()
    assert not destino.exists()


def test_nunca_sobrescribe(tmp_path):
    """Si ya hay un fichero con ese nombre, se añade « (1)»."""
    destino = tmp_path / "Documentos"
    destino.mkdir()
    (destino / "apuntes.pdf").write_text("viejo", encoding="utf-8")
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("nuevo", encoding="utf-8")

    mover.ejecutar(origen, destino)

    assert (destino / "apuntes (1).pdf").read_text(encoding="utf-8") == "nuevo"
    assert (destino / "apuntes.pdf").read_text(encoding="utf-8") == "viejo"


def test_crea_la_carpeta_de_destino(tmp_path):
    """Si la carpeta no existe, se crea en vez de fallar."""
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("x", encoding="utf-8")
    destino = tmp_path / "Nueva" / "Subcarpeta"

    mover.ejecutar(origen, destino)

    assert (destino / "apuntes.pdf").is_file()


def test_una_carpeta_no_se_mueve(tmp_path):
    """El comando es para ficheros: una carpeta se rechaza con un consejo."""
    carpeta = tmp_path / "proyecto"
    carpeta.mkdir()
    with pytest.raises(TareasError) as error:
        mover.ejecutar(carpeta, tmp_path / "Documentos")
    assert "no un fichero" in str(error.value)
    assert "organizar" in str(error.value)


def test_mover_a_la_misma_carpeta_avisa(tmp_path):
    """Mover a donde ya está no hace nada y lo explica."""
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("x", encoding="utf-8")
    with pytest.raises(TareasError) as error:
        mover.ejecutar(origen, tmp_path)
    assert "ya está en" in str(error.value)


def test_destino_que_es_un_fichero(tmp_path):
    """Si el destino es un fichero, no se puede usar como carpeta."""
    origen = tmp_path / "apuntes.pdf"
    origen.write_text("x", encoding="utf-8")
    ocupado = tmp_path / "no-soy-carpeta.txt"
    ocupado.write_text("x", encoding="utf-8")

    with pytest.raises(TareasError) as error:
        mover.ejecutar(origen, ocupado)
    assert "no es una carpeta" in str(error.value)
