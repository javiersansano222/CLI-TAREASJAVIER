"""tareas: automatiza tareas repetitivas con ficheros desde la terminal."""

import sys

__version__ = "0.1.0"


def _asegurar_codificacion() -> None:
    """Pone stdout y stderr en UTF-8 para que la CLI no se rompa en Windows.

    En Windows la salida sale en cp1252 y caracteres como «✔» o «█» lanzan
    UnicodeEncodeError, sobre todo con la salida redirigida a un fichero o a
    un tubo (que es como trabajan los tests). Con UTF-8 todo escribe igual en
    Linux, Windows y macOS; y si algún carácter no se pudiera escribir, se
    pone en su lugar un «?» en vez de romper el programa.
    """
    for flujo in (sys.stdout, sys.stderr):
        if flujo is None:
            continue
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is None:
            continue
        try:
            reconfigurar(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Si el flujo no admite cambios (por ejemplo, la captura de
            # pytest), seguimos con la codificación que traiga.
            pass


_asegurar_codificacion()
