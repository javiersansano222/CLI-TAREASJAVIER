"""Mueve (o copia) un fichero concreto a la carpeta que indique el usuario.

No clasifica nada: el usuario dice qué fichero quiere y dónde lo quiere. Si
solo escribe el nombre, se busca en la carpeta actual y, si no está, en la de
descargas. Nunca sobrescribe: añade « (1)», « (2)»… al nombre.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .acciones import Resultado, destino_libre
from .errores import TareasError
from .rutas import carpeta_descargas, resolver_carpeta


def localizar(archivo: str | Path) -> Path:
    """Devuelve la ruta del fichero pedido, buscándolo si solo dan el nombre."""
    pedido = Path(archivo).expanduser()
    if pedido.exists():
        return pedido

    # Sin ninguna carpeta en la ruta: se prueba en la carpeta actual y en la
    # de descargas, que es donde suele quedarse lo que se baja de internet.
    if pedido.parent == Path("."):
        candidatas = [
            Path.cwd() / pedido.name,
            carpeta_descargas() / pedido.name,
        ]
        for candidata in candidatas:
            if candidata.is_file():
                return candidata
        probadas = " y ".join(f"«{ruta}»" for ruta in candidatas)
        raise TareasError(f"No encuentro «{pedido.name}». Lo he buscado en {probadas}.")

    raise TareasError(f"«{pedido}» no existe.")


def ejecutar(
    archivo: str | Path,
    destino: str | Path,
    simular: bool = False,
    copiar: bool = False,
) -> Resultado:
    """Mueve (o copia) «archivo» dentro de la carpeta «destino»."""
    origen = localizar(archivo)
    if origen.is_dir():
        raise TareasError(
            f"«{origen}» es una carpeta, no un fichero. "
            "Para ordenar carpetas usa «tareas organizar»."
        )

    carpeta = resolver_carpeta(destino)
    if carpeta.exists() and not carpeta.is_dir():
        raise TareasError(f"«{carpeta}» existe, pero no es una carpeta.")

    # Mover a la carpeta donde ya está no es un error del programa, pero sí
    # algo que el usuario debe saber: se avisa y no se toca nada.
    if carpeta.resolve() == origen.parent.resolve():
        raise TareasError(f"«{origen.name}» ya está en «{carpeta}».")

    final = destino_libre(carpeta / origen.name)

    if simular:
        return Resultado(origen, final, "simulado")

    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        if copiar:
            shutil.copy2(origen, final)
            estado = "copiado"
        else:
            shutil.move(str(origen), str(final))
            estado = "movido"
    except OSError as error:
        return Resultado(origen, final, "error", detalle=f"{error}")

    return Resultado(origen, final, estado)
