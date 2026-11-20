"""Los instaladores deben poder ejecutarse tal y como se documentan."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_instaladores_sin_bom():
    """Un BOM al principio rompe «irm ... | iex» en PowerShell."""
    for nombre in ("instalar.sh", "instalar.ps1"):
        datos = (RAIZ / nombre).read_bytes()
        assert not datos.startswith(b"\xef\xbb\xbf"), (
            f"{nombre} empieza con BOM; guárdalo en UTF-8 sin BOM"
        )


def test_instalar_ps1_solo_ascii():
    """PowerShell 5.1 lee sin BOM como ANSI; con ASCII puro no hay sorpresas."""
    (RAIZ / "instalar.ps1").read_text(encoding="ascii")
