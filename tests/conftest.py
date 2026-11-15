"""Configuración común de pytest: la caja de arena de todas las pruebas.

Ninguna prueba toca tus carpetas de verdad ni llama al servidor de IA: cada
una se ejecuta en su propia carpeta temporal, con HOME apuntando ahí y sin
las variables del centro. Además hay un «modelo falso» para probar las
acciones con IA sin red, sin clave y sin gastar un solo token.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from tareas import ia as modulo_ia
from tareas.ia import ProveedorIA, RespuestaIA


@pytest.fixture(autouse=True)
def aislado(tmp_path, monkeypatch):
    """Cada prueba, en su carpeta temporal y sin el servidor de IA de verdad."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))  # ~ apunta aquí (Linux, macOS)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # y aquí en Windows
    for variable in ("CENTRO_IA_URL", "CENTRO_IA_KEY", "CENTRO_IA_CA"):
        monkeypatch.delenv(variable, raising=False)
    # Ni un .env despistado por la carpeta del repo puede colar una clave.
    monkeypatch.setattr(modulo_ia, "cargar_dotenv", lambda: None)


@pytest.fixture
def descargas(tmp_path) -> Path:
    """Una carpeta con ficheros feos: tildes, espacios, mayúsculas y uno viejo."""
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()
    for nombre in (
        "factura.pdf",
        "apuntes de redes.docx",
        "FOTO1.JPG",
        "cumpleaños 2.png",
        "viejo.tmp",
    ):
        (carpeta / nombre).write_text("contenido de prueba", encoding="utf-8")
    hace_40_dias = time.time() - 40 * 86400
    os.utime(carpeta / "viejo.tmp", (hace_40_dias, hace_40_dias))
    return carpeta


@pytest.fixture
def escribir_config(tmp_path):
    """Escribe un acciones.json (lista de acciones o texto tal cual) y da su ruta."""

    def escribir(acciones) -> Path:
        ruta = tmp_path / "acciones.json"
        texto = (
            acciones
            if isinstance(acciones, str)
            else json.dumps({"version": 1, "acciones": acciones})
        )
        ruta.write_text(texto, encoding="utf-8")
        return ruta

    return escribir


class ProveedorFalso(ProveedorIA):
    """Un «modelo» que contesta siempre lo mismo y apunta lo que le preguntan."""

    def __init__(self, respuesta: str) -> None:
        self.respuesta = respuesta
        self.preguntas: list[str] = []

    def completar(
        self, sistema: str, usuario: str, max_tokens: int = 600
    ) -> RespuestaIA:
        self.preguntas.append(usuario)
        return RespuestaIA(
            texto=self.respuesta,
            modelo="falso",
            tokens_entrada=10,
            tokens_salida=5,
            segundos=0.0,
        )


@pytest.fixture
def modelo_falso():
    """La clase: cada prueba crea su falso con la respuesta que quiera."""
    return ProveedorFalso
