"""Pruebas de doctor.py: orígenes traducidos y la IA sin configurar."""

from __future__ import annotations

from tareas import doctor


def test_origen_en_otro_idioma_cuenta_como_ok(tmp_path):
    """Un origen «~/Descargas» vale si existe ~/Downloads."""
    (tmp_path / "Downloads").mkdir()
    comprobaciones = doctor.comprobar_origenes(
        [{"nombre": "limpiar", "origen": "~/Descargas"}]
    )
    assert comprobaciones[0].estado == "ok"
    assert "Downloads" in comprobaciones[0].detalle


def test_origen_que_no_existe_sigue_siendo_aviso(tmp_path):
    """Sin equivalente, el aviso se mantiene: no se esconde el problema."""
    comprobaciones = doctor.comprobar_origenes(
        [{"nombre": "x", "origen": "~/NoExisteNada"}]
    )
    assert comprobaciones[0].estado == "aviso"
    assert "no existe" in comprobaciones[0].detalle


def test_ia_sin_clave_es_info_no_aviso(monkeypatch):
    """Fuera del centro no hay clave: se informa, pero no es un aviso."""
    monkeypatch.delenv("CENTRO_IA_KEY", raising=False)
    monkeypatch.delenv("CENTRO_IA_URL", raising=False)
    comprobacion = doctor.comprobar_ia()
    assert comprobacion.estado == "info"
    assert "sin configurar" in comprobacion.detalle
    assert "fuera del centro" in comprobacion.detalle


def test_ia_configurada_es_ok(monkeypatch):
    """Con las variables puestas, la comprobación es verde."""
    monkeypatch.setenv("CENTRO_IA_KEY", "clave")
    monkeypatch.setenv("CENTRO_IA_URL", "https://ejemplo.invalid")
    assert doctor.comprobar_ia().estado == "ok"


def test_cada_estado_tiene_simbolo_y_color():
    """La tabla de doctor no se rompe si aparece un estado nuevo."""
    for estado in doctor.ESTADOS:
        assert estado in doctor.SIMBOLO
        assert estado in doctor.COLOR
