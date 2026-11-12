"""Tests for acciones.py - clases de acción."""

from pathlib import Path
import tempfile

import pytest

from tareas.acciones import (
    Accion,
    AccionIA,
    Classificar,
    MirarEspacio,
    Resultado,
    Mover,
    Copiar,
    Renombrar,
    Borrar,
    Resumir,
    leer_texto,
)


def test_mirar_espacio_tipo():
    """Test que MirarEspacio tiene tipo correcto."""
    assert MirarEspacio.tipo == "mirar_espacio"


def test_mirar_espacio_registro():
    """Test que MirarEspacio está registrado en Accion._registro."""
    assert "mirar_espacio" in Accion._registro


def test_accion_subclases_registradas():
    """Test que todas las subclases se registran."""
    assert Accion._registro["mover"] == Mover
    assert Accion._registro["copiar"] == Copiar
    assert Accion._registro["renombrar"] == Renombrar
    assert Accion._registro["borrar"] == Borrar
    assert Accion._registro["mirar_espacio"] == MirarEspacio


def test_resultado_dataclass():
    """Test que Resultado tiene los campos esperados."""
    resultado = Resultado(Path("/origen"), Path("/destino"), "hecho", "detalle")
    assert resultado.origen == Path("/origen")
    assert resultado.destino == Path("/destino")
    assert resultado.estado == "hecho"
    assert resultado.detalle == "detalle"


def test_mover_tipo():
    """Test tipo Mover."""
    assert Mover.tipo == "mover"


def test_copiar_tipo():
    """Test tipo Copiar."""
    assert Copiar.tipo == "copiar"


def test_renombrar_tipo():
    """Test tipo Renombrar."""
    assert Renombrar.tipo == "renombrar"


def test_borrar_tipo():
    """Test tipo Borrar."""
    assert Borrar.tipo == "borrar"


def test_resumir_registro_y_necesita_ia():
    """Resumir se registra por su tipo y solo él pide proveedor IA."""
    assert Accion._registro["resumir"] == Resumir
    assert Resumir.necesita_ia is True
    assert Mover.necesita_ia is False
    assert isinstance(Resumir({"nombre": "x", "descripcion": "y", "tipo": "resumir"}), AccionIA)


def test_leer_texto_txt_y_tope(tmp_path):
    """Lee un .txt y lo corta al tope indicado."""
    fichero = tmp_path / "notas.txt"
    fichero.write_text("a" * 500, encoding="utf-8")
    assert leer_texto(fichero, 100) == "a" * 100


def test_leer_texto_md(tmp_path):
    """Lee un .md conservando el formato."""
    fichero = tmp_path / "tema.md"
    fichero.write_text("# Título\n\nviñeta", encoding="utf-8")
    assert leer_texto(fichero, 1000).startswith("# Título")


def test_leer_texto_formato_no_valido(tmp_path):
    """Un formato que no es texto da ValueError (la acción lo salta)."""
    fichero = tmp_path / "foto.png"
    fichero.write_bytes(b"PNG")
    with pytest.raises(ValueError):
        leer_texto(fichero, 100)


def test_presupuesto_sin_gastar():
    """En simulación solo se cuenta: caracteres y tokens estimados."""
    resumir = Resumir(
        {
            "nombre": "resumir-apuntes",
            "descripcion": "resumen",
            "tipo": "resumir",
            "instrucciones": "resume",
        }
    )
    detalle = resumir.presupuesto(1200)
    assert "1200 caracteres" in detalle
    assert "300 tokens" in detalle
    assert "sin gastar" in detalle


def test_resumir_sin_proveedor_no_gasta():
    """Sin proveedor inyectado, preguntar avisa en vez de intentar la red."""
    from tareas.errores import IANoDisponible

    resumir = Resumir(
        {
            "nombre": "resumir-apuntes",
            "descripcion": "resumen",
            "tipo": "resumir",
            "instrucciones": "resume",
        }
    )
    with pytest.raises(IANoDisponible):
        resumir.preguntar("sistema", Path("apunte.md"), "texto")


def test_nombre_seguro_quita_lo_prohibido():
    """Lo que devuelva la IA se limpia para Windows/Linux/macOS."""
    from tareas.acciones import a_nombre_seguro

    assert a_nombre_seguro('"Tema 5: herencia / intro"') == "Tema 5 herencia intro"
    assert a_nombre_seguro("  espacios   dobles  ") == "espacios dobles"
    assert a_nombre_seguro("final.") == "final"
    assert a_nombre_seguro("") == ""
    assert a_nombre_seguro("CON") == "n-CON"  # nombre reservado de Windows
    assert len(a_nombre_seguro("x" * 300)) == 60  # tope


def test_categoria_con_tildes_y_mayusculas():
    """La respuesta de la IA casa con la categoría aunque cambien tildes."""
    from tareas.acciones import _categoria_mas_cercana

    categorias = ["programacion", "bases-de-datos", "otro"]
    assert _categoria_mas_cercana("Programación", categorias) == "programacion"
    assert _categoria_mas_cercana(" BASES-DE-DATOS ", categorias) == "bases-de-datos"
    assert _categoria_mas_cercana("inventada", categorias) is None


def test_clasificar_y_renombrar_necesitan_ia():
    """Los dos tipos nuevos están registrados y piden proveedor."""
    from tareas.acciones import Classificar, RenombrarIA

    assert Accion._registro["clasificar"] == Classificar
    assert Accion._registro["renombrar_ia"] == RenombrarIA
    assert Classificar.necesita_ia is True
    assert RenombrarIA.necesita_ia is True


def test_clasificar_simulacion_no_mueve(tmp_path):
    """La simulación cuenta tokens y no crea ni mueve nada."""
    origen = tmp_path / "origen"
    destino = tmp_path / "destino"
    origen.mkdir()
    (origen / "apunte.txt").write_text("contenido del apunte", encoding="utf-8")
    accion = Classificar(
        {
            "nombre": "clasificar-apuntes",
            "descripcion": "prueba",
            "tipo": "clasificar",
            "origen": str(origen),
            "destino": str(destino),
            "categorias": ["programacion"],
            "instrucciones": "elige",
            "max_caracteres": 8000,
        }
    )
    resultados = accion.ejecutar([origen / "apunte.txt"], simular=True)
    assert resultados[0].estado == "simulado"
    assert "sin gastar" in resultados[0].detalle
    assert not destino.exists()