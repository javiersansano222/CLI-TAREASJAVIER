"""Interfaz de línea de órdenes: aquí solo hay órdenes, opciones y salida."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__
from tareas import capturas as modulo_capturas
from tareas import config as configuracion
from tareas.acciones import Resultado
from tareas.errores import TareasError
from tareas.motor import Motor

app = typer.Typer(
    help="tareas: automatiza tareas repetitivas con tus ficheros.",
    no_args_is_help=True,
    add_completion=False,
)
consola = Console()
consola_err = Console(stderr=True)


def tamano_legible(n: int) -> str:
    """Convierte bytes en texto: 532 B, 1.2 KB, 3.4 MB..."""
    if n < 1024:
        return f"{n} B"
    tamano = float(n)
    unidad = "B"
    for unidad in ("KB", "MB", "GB", "TB"):
        tamano /= 1024
        if tamano < 1024:
            break
    return f"{tamano:.1f} {unidad}"


def _mostrar_error(error: TareasError) -> NoReturn:
    consola_err.print(f"[red]✘ {escape(str(error))}[/red]")
    raise typer.Exit(code=error.codigo_salida)


def _cargar_acciones(ctx: typer.Context) -> list[dict[str, Any]]:
    return configuracion.cargar(ctx.obj)


def _pintar_resultados(
    resultados: list[Resultado],
    nombre: str,
    simular: bool,
    ruta_completa: bool = True,
) -> bool:
    if not resultados:
        consola.print("Ningún fichero cumple el filtro de esta acción.")
        return True

    titulo = (
        f"{nombre} (SIMULACIÓN: no se ha tocado nada)"
        if simular
        else f"{nombre} (resultado)"
    )
    tabla = Table(title=escape(titulo))
    tabla.add_column("Fichero")
    tabla.add_column("Destino")
    tabla.add_column("Estado")

    for resultado in resultados:
        destino = str(resultado.destino) if resultado.destino is not None else "—"
        origen = (
            str(resultado.origen) if ruta_completa else resultado.origen.name
        )
        tabla.add_row(
            escape(origen),
            escape(destino),
            resultado.estado,
        )

    consola.print(tabla)

    for resultado in resultados:
        if resultado.estado == "error":
            detalle = resultado.detalle or "error desconocido"
            consola_err.print(
                f"[red]✘ {escape(str(resultado.origen))}: {escape(detalle)}[/red]"
            )

    hechos = sum(resultado.estado == "hecho" for resultado in resultados)
    simulados = sum(resultado.estado == "simulado" for resultado in resultados)
    saltados = sum(resultado.estado == "saltado" for resultado in resultados)
    errores = sum(resultado.estado == "error" for resultado in resultados)
    consola.print(
        f"Ficheros: {len(resultados)} · hechos: {hechos} · "
        f"simulados: {simulados} · saltados: {saltados} · errores: {errores}"
    )
    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin --simular.")
    return errores == 0


@app.callback()
def principal(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            help="Ruta del fichero de acciones (por defecto, ./acciones.json).",
        ),
    ] = Path("acciones.json"),
) -> None:
    """Configura la ruta de acciones.json para todas las órdenes."""
    ctx.obj = config


@app.command()
def version() -> None:
    """Muestra la versión instalada."""
    consola.print(f"tareas {__version__}")


@app.command()
def listar(
    carpeta: Annotated[
        Path, typer.Argument(help="Carpeta que quieres ver (por defecto, la actual).")
    ] = Path("."),
) -> None:
    """Lista los ficheros de una carpeta en una tabla."""
    carpeta = carpeta.expanduser()
    if not carpeta.is_dir():
        consola_err.print(
            f"[red]Error:[/red] «{escape(str(carpeta))}» no existe o no es una carpeta."
        )
        raise typer.Exit(code=1)

    try:
        elementos = sorted(
            carpeta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        )
    except OSError as exc:
        consola_err.print(
            f"[red]Error:[/red] no se puede leer «{escape(str(carpeta))}»: "
            f"{escape(str(exc))}"
        )
        raise typer.Exit(code=1) from None

    if not elementos:
        consola.print(f"La carpeta «{escape(str(carpeta))}» está vacía.")
        return

    tabla = Table(title=f"Contenido de {escape(str(carpeta.resolve()))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")

    for ruta in elementos:
        try:
            datos = ruta.stat()
            fecha = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        except (OSError, OverflowError, ValueError):
            continue
        es_carpeta = ruta.is_dir()
        tipo = "carpeta" if es_carpeta else (ruta.suffix.lower() or "(sin extensión)")
        tamano = "—" if es_carpeta else tamano_legible(datos.st_size)
        tabla.add_row(escape(ruta.name), tipo, tamano, fecha)

    consola.print(tabla)


@app.command()
def capturas(
    carpeta: Annotated[
        Path | None,
        typer.Option("--carpeta", help="Carpeta de capturas (por defecto, la de descargas)."),
    ] = None,
    horas: Annotated[
        int,
        typer.Option("--horas", help="Antigüedad mínima de las capturas, en horas."),
    ] = 5,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué capturas se moverían sin tocar nada."),
    ] = False,
    si: Annotated[
        bool,
        typer.Option("--si", help="No pedir confirmación."),
    ] = False,
) -> None:
    """Envía a la papelera las capturas de descargas con 5 horas o más."""
    if horas < 1:
        raise typer.BadParameter("debe ser 1 o más", param_hint="--horas")

    ruta = (carpeta or modulo_capturas.carpeta_descargas()).expanduser()
    if not ruta.is_dir():
        consola_err.print(
            f"[red]Error:[/red] «{escape(str(ruta))}» no existe o no es una carpeta."
        )
        raise typer.Exit(code=1)

    try:
        ficheros = modulo_capturas.seleccionar(ruta, horas)
    except TareasError as error:
        _mostrar_error(error)

    if not ficheros:
        consola.print(
            f"No hay capturas con al menos {horas} horas en «{escape(str(ruta))}»."
        )
        return

    if not simular and not si:
        texto = "captura" if len(ficheros) == 1 else "capturas"
        typer.confirm(f"¿Enviar {len(ficheros)} {texto} a la papelera?", abort=True)

    resultados = modulo_capturas.enviar_a_papelera(ficheros, simular)
    if not _pintar_resultados(resultados, "capturas", simular, ruta_completa=False):
        raise typer.Exit(code=1)


@app.command()
def validar(ctx: typer.Context) -> None:
    """Comprueba que acciones.json existe y cumple el esquema."""
    try:
        acciones = _cargar_acciones(ctx)
    except TareasError as error:
        _mostrar_error(error)

    texto = "acción válida" if len(acciones) == 1 else "acciones válidas"
    consola.print(f"[green]✔ {len(acciones)} {texto}[/green]")


@app.command()
def acciones(ctx: typer.Context) -> None:
    """Lista las acciones definidas en acciones.json."""
    try:
        lista = _cargar_acciones(ctx)
    except TareasError as error:
        _mostrar_error(error)

    tabla = Table(title="Acciones disponibles")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")

    for accion in lista:
        tabla.add_row(
            escape(accion["nombre"]),
            escape(accion["tipo"]),
            escape(accion["descripcion"]),
        )

    consola.print(tabla)


@app.command()
def ejecutar(
    ctx: typer.Context,
    nombre: Annotated[
        str, typer.Argument(help="Nombre de la acción (ver: tareas acciones).")
    ],
    carpeta: Annotated[
        Path | None,
        typer.Argument(help="Carpeta sobre la que actuar (por defecto, el origen)."),
    ] = None,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué haría sin tocar nada."),
    ] = False,
    si: Annotated[
        bool,
        typer.Option("--si", help="No pedir confirmación."),
    ] = False,
) -> None:
    """Ejecuta una acción sobre una carpeta."""
    try:
        motor = Motor(_cargar_acciones(ctx))
        accion = motor.obtener(nombre)
        if accion.destructiva and accion.confirmar and not simular and not si:
            typer.confirm(
                f"«{nombre}» borra ficheros. ¿Seguro?",
                abort=True,
            )
        resultados = motor.ejecutar(nombre, carpeta, simular)
    except TareasError as error:
        _mostrar_error(error)

    if not _pintar_resultados(resultados, nombre, simular):
        raise typer.Exit(code=1)
