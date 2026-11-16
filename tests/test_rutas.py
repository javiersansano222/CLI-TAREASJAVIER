"""Pruebas de rutas.py: carpetas personales escritas en otro idioma."""

from __future__ import annotations

from pathlib import Path

from tareas.rutas import resolver_carpeta


def test_si_la_carpeta_existe_no_se_cambia(tmp_path):
    """Con la ruta buena, el resolutor devuelve exactamente esa."""
    (tmp_path / "Descargas").mkdir()
    assert resolver_carpeta("~/Descargas") == tmp_path / "Descargas"


def test_descargas_se_traduce_a_downloads(tmp_path):
    """~/Descargas en un Windows en inglés acaba en ~/Downloads."""
    (tmp_path / "Downloads").mkdir()
    assert resolver_carpeta("~/Descargas") == tmp_path / "Downloads"


def test_imagenes_y_capturas_se_traducen(tmp_path):
    """La ruta anidada ~/Imágenes/Capturas también se resuelve."""
    destino = tmp_path / "Pictures" / "Screenshots"
    destino.mkdir(parents=True)
    assert resolver_carpeta("~/Imágenes/Capturas") == destino


def test_no_distingue_tildes_ni_mayusculas(tmp_path):
    """«DESCARGAS» sin tilde vale igual que «Descargas»."""
    (tmp_path / "Downloads").mkdir()
    assert resolver_carpeta("~/DESCARGAS") == tmp_path / "Downloads"


def test_en_valenciano_descargas_es_baixades(tmp_path):
    """En un Windows en valenciano, ~/Descargas acaba en ~/Baixades."""
    (tmp_path / "Baixades").mkdir()
    assert resolver_carpeta("~/Descargas") == tmp_path / "Baixades"


def test_en_valenciano_capturas_es_captures_de_pantalla(tmp_path):
    """~/Imágenes/Capturas se resuelve a ~/Imatges/Captures de pantalla."""
    destino = tmp_path / "Imatges" / "Captures de pantalla"
    destino.mkdir(parents=True)
    assert resolver_carpeta("~/Imágenes/Capturas") == destino


def test_desde_valenciano_tambien_se_llega_al_ingles(tmp_path):
    """Y al revés: ~/Baixades funciona en un sistema en inglés."""
    (tmp_path / "Downloads").mkdir()
    assert resolver_carpeta("~/Baixades") == tmp_path / "Downloads"


def test_sin_equivalente_devuelve_la_ruta_original(tmp_path):
    """Si no hay traducción, no se inventa nada: se devuelve lo pedido."""
    assert resolver_carpeta("~/NoExiste") == tmp_path / "NoExiste"


def test_fuera_de_la_carpeta_personal_no_se_traduce(tmp_path):
    """Una ruta absoluta ajena a ~ se deja tal cual."""
    ruta = Path(tmp_path.anchor) / "carpeta-que-no-existe-xyz"
    assert resolver_carpeta(ruta) == ruta
