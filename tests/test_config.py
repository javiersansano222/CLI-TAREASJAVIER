"""Tests for config.py - validación de acciones.json."""

from pathlib import Path

import pytest

from tareas.config import cargar, resolver_ruta, ConfigError, AccionNoValida

RAIZ = Path(__file__).resolve().parents[1]


def test_cargar_acciones_validas():
    """El acciones.json del repo (solo lectura) se carga y valida."""
    acciones = cargar(RAIZ / "acciones.json")
    assert len(acciones) >= 5  # crece con cada acción nueva del proyecto


def test_cargar_acciones_sin_fichero(tmp_path: Path):
    """Test que falla si no encuentra el fichero."""
    ruta_inexistente = tmp_path / "nonexistent.json"
    with pytest.raises(ConfigError):
        cargar(ruta_inexistente)


def test_resolver_ruta_respeta_la_indicada(tmp_path: Path):
    """Con --config, la ruta se usa tal cual aunque no exista."""
    ruta = tmp_path / "otra.json"
    assert resolver_ruta(ruta) == ruta


def test_resolver_ruta_prefiere_la_carpeta_actual(tmp_path: Path, monkeypatch):
    """Si hay acciones.json donde lanzas la orden, se usa ese."""
    actual = tmp_path / "actual"
    casa = tmp_path / "casa"
    actual.mkdir()
    casa.mkdir()
    (actual / "acciones.json").write_text("{}", encoding="utf-8")
    (casa / "acciones.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(actual)
    monkeypatch.setenv("HOME", str(casa))
    monkeypatch.setenv("USERPROFILE", str(casa))
    assert resolver_ruta() == actual / "acciones.json"


def test_resolver_ruta_encuentra_la_carpeta_personal(tmp_path: Path, monkeypatch):
    """Fuera del repo, usa el acciones.json que deja el instalador en ~."""
    actual = tmp_path / "actual"
    casa = tmp_path / "casa"
    actual.mkdir()
    casa.mkdir()
    (casa / "acciones.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(actual)
    monkeypatch.setenv("HOME", str(casa))
    monkeypatch.setenv("USERPROFILE", str(casa))
    assert resolver_ruta() == casa / "acciones.json"


def test_resolver_ruta_sin_fichero_devuelve_la_actual(tmp_path: Path, monkeypatch):
    """Sin fichero, el error debe señalar la carpeta actual."""
    actual = tmp_path / "actual"
    casa = tmp_path / "casa"
    actual.mkdir()
    casa.mkdir()
    monkeypatch.chdir(actual)
    monkeypatch.setenv("HOME", str(casa))
    monkeypatch.setenv("USERPROFILE", str(casa))
    assert resolver_ruta() == actual / "acciones.json"


def test_version_invalida(tmp_path: Path):
    """Test que falla si la versión no es 1."""
    import json

    datos = {"version": 2, "acciones": []}
    ruta = tmp_path / "test_acciones.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(ConfigError) as exc:
        cargar(ruta)
    assert "no es compatible" in str(exc.value)


def test_accion_sin_nombre(tmp_path: Path):
    """Test que falla si una acción no tiene nombre."""
    import json

    datos = {"version": 1, "acciones": [{"descripcion": "sin nombre"}]}
    ruta = tmp_path / "test_acciones.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(AccionNoValida):
        cargar(ruta)


def test_accion_repetida_nombre(tmp_path: Path):
    """Test que falla si dos acciones tienen el mismo nombre."""
    import json

    datos = {"version": 1, "acciones": [
        {"nombre": "misma", "descripcion": "una", "tipo": "mover", "destino": "/tmp"},
        {"nombre": "misma", "descripcion": "otra", "tipo": "mover", "destino": "/tmp"},
    ]}
    ruta = tmp_path / "test_acciones.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(AccionNoValida) as exc:
        cargar(ruta)
    assert "repetido" in str(exc.value).lower()


BUENA = {
    "nombre": "ordenar",
    "descripcion": "Mueve los PDF",
    "tipo": "mover",
    "destino": "~/PDF",
}


def test_una_config_buena_se_carga(escribir_config):
    """Camino feliz: una acción bien escrita se valida y se devuelve tal cual."""
    acciones = cargar(escribir_config([BUENA]))
    assert [accion["nombre"] for accion in acciones] == ["ordenar"]


@pytest.mark.parametrize(
    "cambio, campo",
    [
        ({"tipo": "mober"}, "tipo"),
        ({"destino": ""}, "destino"),
        ({"descripcion": None}, "descripcion"),
        ({"filtro": {"patron": "*.tmp"}}, "filtro.patron"),
    ],
    ids=["tipo-inexistente", "destino-vacio", "sin-descripcion", "regex-rota"],
)
def test_el_error_dice_que_campo_falla(escribir_config, cambio, campo):
    """Cuatro casos feos: el mensaje siempre señala el campo que está mal."""
    with pytest.raises(AccionNoValida) as error:
        cargar(escribir_config([BUENA | cambio]))
    assert error.value.campo == campo


def test_nombre_repetido(escribir_config):
    """Dos acciones con el mismo nombre: error claro antes de tocar el disco."""
    with pytest.raises(AccionNoValida, match="está repetido"):
        cargar(escribir_config([BUENA, BUENA]))


def test_json_roto_dice_la_linea(escribir_config):
    """Un JSON roto dice la línea y no enseña un traceback."""
    with pytest.raises(ConfigError, match="línea 1"):
        cargar(escribir_config('{"version": 1, "acciones": [ } ]'))