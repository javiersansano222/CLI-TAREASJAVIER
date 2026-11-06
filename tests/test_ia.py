"""Tests de ia.py sin tocar la red: la clave se pone a mano y urlopen se parchea."""

from __future__ import annotations

import io
import json
import urllib.request
from pathlib import Path

import pytest

from tareas.ia import (
    ErrorIA,
    ErrorRedIA,
    FaltaClaveIA,
    hablar,
    explicar_simulacion,
    sugerir_accion,
    _extraer_json,
)
from tareas.acciones import Resultado


@pytest.fixture
def con_clave(monkeypatch):
    """Pone las variables de entorno de prueba sin depender del sistema."""
    monkeypatch.setenv("CENTRO_IA_KEY", "sk-prueba-falsa")
    monkeypatch.setenv("CENTRO_IA_URL", "https://centro.example/v1")


def _respuesta(cuerpo: dict):
    """Fabrica un contexto de urlopen que devuelve el JSON indicado."""

    class Fake:
        def read(self) -> bytes:
            return json.dumps(cuerpo).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return Fake()


def test_falta_clave_sin_red(monkeypatch):
    """Sin CENTRO_IA_KEY debe avisar con FaltaClaveIA y no tocar la red."""
    monkeypatch.delenv("CENTRO_IA_KEY", raising=False)
    monkeypatch.setenv("CENTRO_IA_URL", "https://centro.example/v1")
    with pytest.raises(FaltaClaveIA) as exc:
        hablar("hola")
    assert "CENTRO_IA_KEY" in str(exc.value)
    assert "sk" not in str(exc.value)


def test_sin_url_igualmente(monkeypatch):
    """Si falta CENTRO_IA_URL también avisa."""
    monkeypatch.setenv("CENTRO_IA_KEY", "sk-prueba-falsa")
    monkeypatch.delenv("CENTRO_IA_URL", raising=False)
    with pytest.raises(FaltaClaveIA):
        hablar("hola")


def test_hablo_devuelve_texto(con_clave, monkeypatch):
    """hablar parsea choices[0].message.content."""
    cuerpo = {"choices": [{"message": {"content": "  todo bien  "}}]}
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, **kw: _respuesta(cuerpo))
    respuesta = hablar("prueba")
    assert respuesta.texto == "todo bien"
    assert respuesta.modelo


def test_error_red(con_clave, monkeypatch):
    """Un URLError se convierte en ErrorRedIA con mensaje humano."""

    def falla(*args, **kwargs):
        raise urllib.error.URLError("sin ruta")

    monkeypatch.setattr(urllib.request, "urlopen", falla)
    with pytest.raises(ErrorRedIA) as exc:
        hablar("hola")
    assert "sin IA" in str(exc.value)


def test_respuesta_rota(con_clave, monkeypatch):
    """Si el centro no manda el campo esperado, ErrorRedIA sin traceback."""
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda req, **kw: _respuesta({"nada": 1})
    )
    with pytest.raises(ErrorRedIA):
        hablar("hola")


def test_extraer_json_bloque():
    """Extrae el JSON de un bloque ```json ... ```."""
    texto = 'mira:\n```json\n{"a": 1}\n```\nfin'
    assert json.loads(_extraer_json(texto)) == {"a": 1}


def test_extraer_json_sin_bloque():
    """Sin bloque, coge el primer { y el último }."""
    texto = 'te propongo {"a": 1} ¿vale?'
    assert json.loads(_extraer_json(texto)) == {"a": 1}


def test_extraer_json_roto():
    """Sin JSON en el texto, ErrorIA con mensaje claro."""
    with pytest.raises(ErrorIA):
        _extraer_json("no hay nada aquí")


def test_sugerir_accion_valida(con_clave, monkeypatch):
    """Una propuesta válida pasa la validación real y la devuelve como dict."""
    accion = {
        "nombre": "mover-pdfs",
        "descripcion": "Mueve los PDF de Descargas a Documentos.",
        "tipo": "mover",
        "origen": "~/Descargas",
        "destino": "~/Documentos",
        "filtro": {"extensiones": [".pdf"]},
    }
    cuerpo = {"choices": [{"message": {"content": json.dumps(accion, ensure_ascii=False)}}]}
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, **kw: _respuesta(cuerpo))
    resultado = sugerir_accion("mover los pdf de descargas a documentos")
    assert resultado["nombre"] == "mover-pdfs"


def test_sugerir_propuesta_invalida(con_clave, monkeypatch):
    """Una propuesta que rompe el esquema da ErrorIA con el motivo."""
    cuerpo = {"choices": [{"message": {"content": '{"nombre": "MAL NOMBRE"}'}}]}
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, **kw: _respuesta(cuerpo))
    with pytest.raises(ErrorIA) as exc:
        sugerir_accion("prueba")
    assert "validación" in str(exc.value)


def test_explicar_simulacion_recorta(con_clave, monkeypatch):
    """explicar_simulacion envía la muestra y devuelve el texto del modelo."""
    capturado = {}

    def fake(req, **kwargs):
        capturado["payload"] = json.loads(req.data.decode("utf-8"))
        return _respuesta({"choices": [{"message": {"content": "explicación"}}]})

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    resultados = [
        Resultado(Path(f"/x/captura_{i}.png"), Path(f"/x/2026-11-05_{i:03}.png"), "simulado")
        for i in range(40)
    ]
    texto = explicar_simulacion("renombrar-capturas", resultados)
    assert texto == "explicación"
    assert "captura_0.png" in capturado["payload"]["messages"][-1]["content"]
    assert "15 ficheros más" in capturado["payload"]["messages"][-1]["content"]
