"""Pruebas de terminal.py: paletas, secuencias OSC y detección del terminal."""

from __future__ import annotations

import os

import pytest

from tareas.errores import TareasError
from tareas.terminal import (
    FIN,
    PALETAS,
    a_rgb,
    a_x11,
    aplicar,
    buscar,
    detectar,
    normalizar_hex,
    restablecer,
    secuencia_cursor,
    secuencia_fondo,
    secuencia_texto,
    secuencias_paleta,
)


@pytest.mark.parametrize("nombre", sorted(PALETAS))
def test_cada_paleta_tiene_los_16_colores(nombre):
    """Una paleta completa: fondo, texto, cursor y 16 colores ANSI válidos."""
    paleta = PALETAS[nombre]
    assert len(paleta.ansi) == 16
    for color in paleta.todo():
        assert normalizar_hex(color) == color
    assert paleta.nombre == nombre
    assert paleta.descripcion


def test_los_nombres_no_se_repiten():
    """Cada paleta se guarda con su propio nombre, sin duplicados."""
    assert len({paleta.nombre for paleta in PALETAS.values()}) == len(PALETAS)


def test_hay_seis_temas():
    """La tabla de temas no se queda corta: al menos seis para elegir."""
    assert len(PALETAS) >= 6


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("#0B1020", "#0b1020"),
        ("0b1020", "#0b1020"),
        ("  #7aa2f7  ", "#7aa2f7"),
        ("FFFFFF", "#ffffff"),
    ],
)
def test_hex_valido_se_normaliza(entrada, esperado):
    """Mayúsculas, sin almohadilla y con espacios: todo acaba en «#rrggbb»."""
    assert normalizar_hex(entrada) == esperado


@pytest.mark.parametrize(
    "malo",
    ["#12", "rojo", "#GGGGGG", "", "#1234567", "#12 34 56"],
)
def test_hex_invalido_da_error_humano(malo):
    """Un color mal escrito explica cómo se escribe, sin traceback."""
    with pytest.raises(TareasError) as error:
        normalizar_hex(malo)
    assert "#0b1020" in str(error.value)


def test_rgb_y_x11():
    """El color se traduce a números y al formato rgb:rr/gg/bb de las OSC."""
    assert a_rgb("#0b1020") == (11, 16, 32)
    assert a_x11("#0b1020") == "rgb:0b/10/20"


def test_secuencias_de_color():
    """Cada color de la sesión usa su código OSC y termina en ST."""
    assert secuencia_fondo("#0b1020") == f"\x1b]11;rgb:0b/10/20{FIN}"
    assert secuencia_texto("#ffffff") == f"\x1b]10;rgb:ff/ff/ff{FIN}"
    assert secuencia_cursor("#ffb000") == f"\x1b]12;rgb:ff/b0/00{FIN}"


def test_secuencias_de_la_paleta():
    """OSC 4 cambia los 16 colores ANSI, cada uno con su índice."""
    paleta = PALETAS["medianoche"]
    secuencias = secuencias_paleta(paleta)
    assert len(secuencias) == 16
    for indice, secuencia in enumerate(secuencias):
        assert secuencia.startswith(f"\x1b]4;{indice};rgb:")
        assert secuencia.endswith(FIN)


def test_aplicar_incluye_fondo_texto_cursor_y_paleta():
    """Aplicar un tema manda fondo, texto, cursor y los 16 colores."""
    texto = aplicar(PALETAS["matrix"])
    assert "\x1b]11;" in texto
    assert "\x1b]10;" in texto
    assert "\x1b]12;" in texto
    assert "\x1b]4;15;" in texto


def test_aplicar_sin_paleta_solo_toca_tres_colores():
    """Con con_paleta=False no se manda OSC 4: menos ruido en terminales lentos."""
    texto = aplicar(PALETAS["papel"], con_paleta=False)
    assert "\x1b]4;" not in texto
    assert texto.count(FIN) == 3


def test_restablecer_devuelve_todo():
    """Restablecer limpia paleta, texto, fondo y cursor."""
    texto = restablecer()
    for codigo in ("104", "110", "111", "112"):
        assert f"\x1b]{codigo};" in texto


def test_buscar_no_distingue_mayusculas():
    """«tareas tema MATRIX» funciona igual que en minúsculas."""
    assert buscar("  MATRIX ").nombre == "matrix"


def test_buscar_desconocido_lista_los_que_hay():
    """Si el tema no existe, el error dice cuáles hay."""
    with pytest.raises(TareasError) as error:
        buscar("neon")
    mensaje = str(error.value)
    for nombre in PALETAS:
        assert nombre in mensaje


@pytest.mark.parametrize(
    ("entorno", "soportado", "terminal"),
    [
        ({"WT_SESSION": "abc"}, True, "Windows Terminal"),
        ({"TERM_PROGRAM": "iTerm.app"}, True, "iTerm2"),
        ({"TERM_PROGRAM": "WezTerm"}, True, "WezTerm"),
        ({"TERM_PROGRAM": "vscode"}, True, "VS Code"),
        ({"KITTY_WINDOW_ID": "1"}, True, "kitty"),
        ({"VTE_VERSION": "7000"}, True, "GNOME Terminal / Tilix"),
        ({"TERM": "xterm-256color"}, True, "xterm"),
        ({"TERM": "dumb"}, False, "terminal sin color"),
        ({"TMUX": "/tmp/tmux", "TERM": "screen-256color"}, False, "tmux/screen"),
    ],
)
def test_detectar_el_terminal(entorno, soportado, terminal):
    """La detección no depende del equipo donde se ejecuten las pruebas."""
    soporte = detectar(entorno)
    assert soporte.soportado is soportado
    assert soporte.terminal == terminal


def test_un_terminal_desconocido_no_promete_nada():
    """Si no se reconoce el terminal, no se dice que sí a la ligera."""
    assert detectar({"TERM": "algo-raro"}).soportado is False


@pytest.mark.skipif(os.name != "nt", reason="la consola clásica solo existe en Windows")
def test_la_consola_clasica_de_windows_avisa():
    """En conhost no se puede, y el aviso manda a Windows Terminal o a exportar."""
    soporte = detectar({})
    assert not soporte.soportado
    assert soporte.terminal == "consola clásica de Windows"
    assert "Windows Terminal" in soporte.nota


def test_tmux_explica_el_motivo():
    """Cuando no se puede, el aviso dice qué hacer, no solo que falla."""
    soporte = detectar({"TMUX": "/tmp/tmux"})
    assert not soporte.soportado
    assert "tmux" in soporte.nota
