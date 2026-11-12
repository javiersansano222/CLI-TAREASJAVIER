"""Configuración común de pytest: las pruebas nunca dependen de la red ni de claves."""

import pytest


@pytest.fixture(autouse=True)
def _sin_clave_centro(monkeypatch):
    """Quita CENTRO_IA_KEY de todas las pruebas salvo que las pongan a mano."""
    monkeypatch.delenv("CENTRO_IA_KEY", raising=False)
