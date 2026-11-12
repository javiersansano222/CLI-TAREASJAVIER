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
from tareas import doctor as modulo_doctor
from tareas import ia as modulo_ia
from tareas import imagenes as modulo_imagenes
from tareas import informe as modulo_informe
from tareas import temporales as modulo_temporales
from tareas.acciones import Resultado
from tareas.bienvenida import mostrar_bienvenida
from tareas.chuleta import mostrar_chuleta
from tareas.errores import TareasError
from tareas.sistema import mostrar_sistema
from tareas.menu import cambiar_color, color_actual, menu_activo, menu_interactivo, _mostrar_cita_motivacional
from tareas.motor import Motor

app = typer.Typer(
    help="tareas: automatiza tareas repetitivas con tus ficheros.",
    no_args_is_help=False,
    add_completion=False,
)
ia_app = typer.Typer(
    help="Órdenes que usan la IA del centro (necesitan CENTRO_IA_KEY).",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(ia_app, name="ia")
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


def fecha_legible(marca: float) -> str:
    """Formatea una fecha de modificación sin romper con valores extremos."""
    try:
        return datetime.fromtimestamp(marca).strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError, ValueError):
        return "—"


def _mostrar_error(error: TareasError) -> NoReturn:
    consola_err.print(f"[red]✘ {escape(str(error))}[/red]")
    if isinstance(error, modulo_ia.IANoDisponible):
        consola_err.print(
            "[dim]Las acciones sin IA siguen funcionando: "
            "mira cuáles con «tareas acciones».[/dim]"
        )
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
    # La columna Detalle solo aparece si hay algo que contar (presupuesto de
    # la simulación con IA, coste real, motivo de un «saltado», tamaño…).
    con_detalle = any(resultado.detalle for resultado in resultados)
    if con_detalle:
        tabla.add_column("Detalle")

    for resultado in resultados:
        destino = str(resultado.destino) if resultado.destino is not None else "—"
        origen = (
            str(resultado.origen) if ruta_completa else resultado.origen.name
        )
        fila = [escape(origen), escape(destino), resultado.estado]
        if con_detalle:
            fila.append(escape(resultado.detalle or ""))
        tabla.add_row(*fila)

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


def _pintar_imagenes(
    resultados: list[modulo_imagenes.Resultado],
    simular: bool,
    webp: bool = False,
) -> bool:
    if simular:
        titulo = (
            "imágenes a WebP (SIMULACIÓN: no se ha creado nada)"
            if webp
            else "imágenes (SIMULACIÓN: no se ha creado nada)"
        )
    else:
        titulo = "imágenes convertidas a WebP" if webp else "imágenes comprimidas"
    tabla = Table(title=titulo)
    tabla.add_column("Imagen")
    tabla.add_column("Destino")
    tabla.add_column("Original", justify="right")
    tabla.add_column("Final", justify="right")
    tabla.add_column("Ahorro", justify="right")
    tabla.add_column("Estado")

    for resultado in resultados:
        final_texto = (
            tamano_legible(resultado.tamano_final)
            if resultado.tamano_final
            else "—"
        )
        if (
            resultado.estado == "hecho"
            and resultado.tamano_final
            and resultado.tamano_original
        ):
            ahorro = (
                (resultado.tamano_original - resultado.tamano_final)
                / resultado.tamano_original
                * 100
            )
            ahorro_texto = f"{ahorro:.0f} %"
        else:
            ahorro_texto = "—"
        destino = (
            str(resultado.destino) if resultado.destino is not None else "—"
        )
        tabla.add_row(
            escape(resultado.origen.name),
            escape(destino),
            tamano_legible(resultado.tamano_original),
            final_texto,
            ahorro_texto,
            resultado.estado,
        )

    consola.print(tabla)

    for resultado in resultados:
        if resultado.estado == "error":
            consola_err.print(
                f"[red]✘ {escape(resultado.origen.name)}: "
                f"{escape(resultado.detalle)}[/red]"
            )

    hechos = sum(resultado.estado == "hecho" for resultado in resultados)
    simulados = sum(resultado.estado == "simulado" for resultado in resultados)
    saltados = sum(resultado.estado == "saltado" for resultado in resultados)
    errores = sum(resultado.estado == "error" for resultado in resultados)
    etiqueta = "convertidas" if webp else "comprimidas"
    consola.print(
        f"Imágenes: {len(resultados)} · {etiqueta}: {hechos} · "
        f"simuladas: {simulados} · saltadas: {saltados} · errores: {errores}"
    )
    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin --simular.")
    return errores == 0


@app.callback(invoke_without_command=True)
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
    if ctx.invoked_subcommand is None:
        menu_interactivo(app)


@app.command()
def version() -> None:
    """Muestra la versión instalada."""
    consola.print(f"tareas {__version__}")


@app.command()
def hola() -> None:
    """Muestra la bienvenida personalizada de la terminal."""
    mostrar_bienvenida()


@app.command()
def chuleta() -> None:
    """Muestra una chuleta rápida de Git y comandos de Linux."""
    mostrar_chuleta(consola)


@app.command()
def sistema() -> None:
    """Muestra el tamaño del disco y la memoria en uso."""
    mostrar_sistema(consola)


@app.command()
def cita() -> None:
    """Muestra una cita motivacional aleatoria."""
    _mostrar_cita_motivacional()


@app.command()
def cambio(
    color: Annotated[
        str,
        typer.Argument(help="Color del menú: rojo, normal, azul, verde o amarillo."),
    ] = "rojo",
) -> None:
    """Cambia el color del menú interactivo."""
    try:
        elegido = cambiar_color(color)
    except ValueError as error:
        raise typer.BadParameter(str(error), param_hint="color") from None
    actual = color_actual()
    consola.print(f"[{actual}]✔ Color del menú cambiado a {elegido}.[/{actual}]")
    if not menu_activo():
        menu_interactivo(app)


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
            f"[red]✘ «{escape(str(carpeta))}» no existe o no es una carpeta."
        )
        raise typer.Exit(code=1)

    try:
        elementos = sorted(
            carpeta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        )
    except OSError as exc:
        consola_err.print(
            f"[red]✘ no se puede leer «{escape(str(carpeta))}»: "
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
            f"[red]✘ «{escape(str(ruta))}» no existe o no es una carpeta."
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
def temporales(
    carpeta: Annotated[
        Path | None,
        typer.Option("--carpeta", help="Carpeta de temporales (por defecto, descargas)."),
    ] = None,
    dias: Annotated[
        int,
        typer.Option("--dias", help="Antigüedad mínima, en días."),
    ] = 30,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué ficheros se moverían sin tocar nada."),
    ] = False,
    si: Annotated[
        bool,
        typer.Option("--si", help="No pedir confirmación."),
    ] = False,
) -> None:
    """Envía a la papelera los ficheros temporales antiguos."""
    if dias < 1:
        raise typer.BadParameter("debe ser 1 o más", param_hint="--dias")

    ruta = (carpeta or modulo_capturas.carpeta_descargas()).expanduser()
    try:
        ficheros = modulo_temporales.seleccionar(ruta, dias)
    except TareasError as error:
        _mostrar_error(error)

    if not ficheros:
        consola.print(
            f"No hay ficheros temporales con al menos {dias} días en "
            f"«{escape(str(ruta))}»."
        )
        return

    if not simular and not si:
        texto = "fichero temporal" if len(ficheros) == 1 else "ficheros temporales"
        typer.confirm(
            f"¿Enviar {len(ficheros)} {texto} a la papelera?",
            abort=True,
        )

    resultados = modulo_temporales.enviar_a_papelera(ficheros, simular)
    if not _pintar_resultados(
        resultados,
        "temporales",
        simular,
        ruta_completa=False,
    ):
        raise typer.Exit(code=1)


@app.command()
def informe(
    carpeta: Annotated[
        Path | None,
        typer.Option("--carpeta", help="Carpeta a analizar (por defecto, descargas)."),
    ] = None,
    top: Annotated[
        int,
        typer.Option("--top", help="Número de filas en cada tabla."),
    ] = 5,
    horas: Annotated[
        int,
        typer.Option("--horas", help="Antigüedad para contar capturas pendientes."),
    ] = 5,
) -> None:
    """Muestra un resumen de solo lectura de la carpeta de descargas."""
    if top < 1:
        raise typer.BadParameter("debe ser 1 o más", param_hint="--top")
    if horas < 1:
        raise typer.BadParameter("debe ser 1 o más", param_hint="--horas")

    ruta = (carpeta or modulo_capturas.carpeta_descargas()).expanduser()
    try:
        resumen = modulo_informe.analizar(ruta, top, horas)
    except TareasError as error:
        _mostrar_error(error)

    consola.print(f"[bold]Informe de {escape(str(ruta))}[/bold]")
    consola.print(
        f"Ficheros: {resumen.ficheros} · Carpetas: {resumen.carpetas} · "
        f"Tamaño: {tamano_legible(resumen.tamano)}"
    )
    consola.print(
        f"Capturas: {resumen.capturas} · Pendientes de papelera "
        f"(con {horas} h o más): {resumen.capturas_pendientes}"
    )

    if resumen.ficheros == 0:
        consola.print("No hay ficheros que analizar.")
        return

    tabla_tipos = Table(title=f"Tipos (top {top})")
    tabla_tipos.add_column("Extensión")
    tabla_tipos.add_column("Ficheros", justify="right")
    tabla_tipos.add_column("Tamaño", justify="right")
    for tipo in resumen.tipos:
        tabla_tipos.add_row(
            escape(tipo.extension),
            str(tipo.ficheros),
            tamano_legible(tipo.tamano),
        )
    consola.print(tabla_tipos)

    tabla_antiguos = Table(title=f"Más antiguos (top {top})")
    tabla_antiguos.add_column("Fichero")
    tabla_antiguos.add_column("Modificado")
    tabla_antiguos.add_column("Tamaño", justify="right")
    for fichero in resumen.mas_antiguos:
        tabla_antiguos.add_row(
            escape(fichero.ruta.name),
            fecha_legible(fichero.modificado),
            tamano_legible(fichero.tamano),
        )
    consola.print(tabla_antiguos)

    tabla_grandes = Table(title=f"Más grandes (top {top})")
    tabla_grandes.add_column("Fichero")
    tabla_grandes.add_column("Tamaño", justify="right")
    tabla_grandes.add_column("Modificado")
    for fichero in resumen.mas_grandes:
        tabla_grandes.add_row(
            escape(fichero.ruta.name),
            tamano_legible(fichero.tamano),
            fecha_legible(fichero.modificado),
        )
    consola.print(tabla_grandes)


@app.command()
def imagenes(
    carpeta: Annotated[
        Path | None,
        typer.Option("--carpeta", help="Carpeta de imágenes (por defecto, descargas)."),
    ] = None,
    comprimir: Annotated[
        bool,
        typer.Option("--comprimir", help="Crea copias comprimidas sin tocar los originales."),
    ] = False,
    webp: Annotated[
        bool,
        typer.Option("--webp", help="Convierte las copias a WebP (implica --comprimir)."),
    ] = False,
    destino: Annotated[
        Path | None,
        typer.Option("--destino", help="Carpeta de salida (por defecto, comprimidas)."),
    ] = None,
    calidad: Annotated[
        int,
        typer.Option("--calidad", help="Calidad JPEG/WebP (1-95)."),
    ] = 75,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué haría sin crear ficheros."),
    ] = False,
    si: Annotated[
        bool,
        typer.Option("--si", help="No pedir confirmación."),
    ] = False,
) -> None:
    """Lista o comprime imágenes de una carpeta."""
    if not modulo_imagenes.CALIDAD_MIN <= calidad <= modulo_imagenes.CALIDAD_MAX:
        raise typer.BadParameter("debe estar entre 1 y 95", param_hint="--calidad")
    if webp:
        comprimir = True

    ruta = (carpeta or modulo_capturas.carpeta_descargas()).expanduser()
    try:
        lista = modulo_imagenes.seleccionar(ruta)
    except TareasError as error:
        _mostrar_error(error)

    if not comprimir:
        if not lista:
            consola.print(f"No hay imágenes compatibles en «{escape(str(ruta))}».")
            return
        tabla = Table(title=f"Imágenes en {escape(str(ruta.resolve()))}")
        tabla.add_column("Imagen")
        tabla.add_column("Formato")
        tabla.add_column("Tamaño", justify="right")
        for imagen in lista:
            tabla.add_row(
                escape(imagen.ruta.name),
                imagen.ruta.suffix.lower().lstrip("."),
                tamano_legible(imagen.tamano),
            )
        consola.print(tabla)
        consola.print(
            f"Total: {len(lista)} imágenes · "
            f"{tamano_legible(sum(imagen.tamano for imagen in lista))}"
        )
        consola.print("Usa [bold]--comprimir[/bold] para crear copias comprimidas.")
        return

    carpeta_destino = (
        destino or ruta / modulo_imagenes.NOMBRE_DESTINO
    ).expanduser()
    if (
        carpeta_destino.exists() or carpeta_destino.is_symlink()
    ) and not carpeta_destino.is_dir():
        raise typer.BadParameter(
            "debe ser una carpeta",
            param_hint="--destino",
        )
    try:
        misma_carpeta = carpeta_destino.resolve() == ruta.resolve()
    except (OSError, RuntimeError):
        raise typer.BadParameter(
            "no se puede resolver la ruta de destino",
            param_hint="--destino",
        ) from None
    if misma_carpeta:
        raise typer.BadParameter(
            "no puede ser la misma carpeta que el origen",
            param_hint="--destino",
        )
    if not lista:
        consola.print(f"No hay imágenes compatibles en «{escape(str(ruta))}».")
        return

    if not simular and not si:
        texto = "imagen" if len(lista) == 1 else "imágenes"
        accion = "Convertir" if webp else "Comprimir"
        typer.confirm(
            f"¿{accion} {len(lista)} {texto} en «{carpeta_destino}»?",
            abort=True,
        )

    resultados = modulo_imagenes.comprimir(
        lista,
        carpeta_destino,
        calidad,
        simular,
        convertir_webp=webp,
    )
    if not _pintar_imagenes(resultados, simular, webp):
        raise typer.Exit(code=1)


@app.command("mirar-espacio")
def mirar_espacio(
    carpeta: Annotated[
        Path | None,
        typer.Argument(help="Carpeta a revisar (por defecto, el origen de la acción)."),
    ] = None,
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué ficheros ocuparían sin tocar nada."),
    ] = False,
    ctx: typer.Context = typer.Argument(),
) -> None:
    """Muestra el espacio total y número de ficheros de una carpeta."""
    try:
        motor = Motor(_cargar_acciones(ctx))
        ruta = motor.ruta_de("mirar-espacio", carpeta)
        resultados = motor.ejecutar("mirar-espacio", carpeta, simular)
    except TareasError as error:
        _mostrar_error(error)

    tabla = Table(title=f"Espacio en {escape(str(ruta))}")
    tabla.add_column("Fichero")
    tabla.add_column("Estado")
    tabla.add_column("Detalle")
    for resultado in resultados:
        detalle = resultado.detalle or "—"
        tabla.add_row(
            escape(resultado.origen.name),
            resultado.estado,
            detalle,
        )
    consola.print(tabla)
    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin --simular.")


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
    tabla.add_column("IA")
    tabla.add_column("Descripción")

    con_ia = 0
    for accion in lista:
        necesita = accion["tipo"] in configuracion.TIPOS_IA
        con_ia += necesita
        tabla.add_row(
            escape(accion["nombre"]),
            escape(accion["tipo"]),
            "[yellow]sí[/yellow]" if necesita else "—",
            escape(accion["descripcion"]),
        )

    consola.print(tabla)
    if con_ia:
        resto = len(lista) - con_ia
        palabra = "acción" if con_ia == 1 else "acciones"
        verbo = "necesita" if con_ia == 1 else "necesitan"
        consola.print(
            f"[yellow]{con_ia} {palabra} {verbo} IA[/yellow] "
            f"(las {resto} restantes funcionan sin red)."
        )
        consola.print(
            "[dim]Sin clave o sin red, las de IA salen con código 4 y no "
            "tocan nada: sigue usando las demás.[/dim]"
        )


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
        if accion.necesita_ia and not simular:
            # Sin clave o sin red, desde_entorno avisa y sale con código 4:
            # el resto de órdenes de la CLI no se entera.
            motor.proveedor = modulo_ia.ProveedorCentro.desde_entorno()
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


@app.command()
def doctor(ctx: typer.Context) -> None:
    """Diagnostica el entorno: configuración, dependencias y rutas. No toca nada."""
    try:
        comprobaciones = modulo_doctor.diagnosticar(ctx.obj)
    except TareasError as error:
        _mostrar_error(error)

    tabla = Table(title="tareas doctor")
    tabla.add_column("Comprobación")
    tabla.add_column("Estado")
    tabla.add_column("Detalle")

    for comprobacion in comprobaciones:
        simbolo = modulo_doctor.SIMBOLO[comprobacion.estado]
        color = modulo_doctor.COLOR[comprobacion.estado]
        tabla.add_row(
            escape(comprobacion.nombre),
            f"[{color}]{simbolo} {comprobacion.estado}[/]",
            escape(comprobacion.detalle),
        )

    consola.print(tabla)

    errores = [
        c for c in comprobaciones if c.estado == "error"
    ]
    avisos = [c for c in comprobaciones if c.estado == "aviso"]

    if errores:
        plural = "" if len(errores) == 1 else "s"
        consola_err.print(
            f"[red]✘ {len(errores)} comprobación{plural} bloqueante{plural}.[/red]"
        )
        raise typer.Exit(code=3)

    if avisos:
        plural = "" if len(avisos) == 1 else "s"
        consola.print(
            f"[yellow]⚠ {len(avisos)} aviso{plural}:"
            " la herramienta funciona, pero algo puede no estar listo.[/yellow]"
        )
        return

    consola.print("[green]✔ Todo listo.[/green]")


@app.command("comprobar-ia")
def comprobar_ia() -> None:
    """Comprueba la conexión con el servidor de IA (sin enseñar la clave)."""
    try:
        proveedor = modulo_ia.ProveedorCentro.desde_entorno()
        consola.print(
            f"Servidor: {escape(proveedor.url)}  ·  "
            f"modelo: {escape(proveedor.modelo)}  ·  clave: definida"
        )
        respuesta = proveedor.completar(
            "Responde solo con la palabra: ok", "¿Me oyes?", max_tokens=5
        )
    except TareasError as error:
        _mostrar_error(error)

    consola.print(
        f"[green]✔ El modelo responde «{escape(respuesta.texto)}» "
        f"en {respuesta.segundos:.1f} s[/green]"
    )


@ia_app.command()
def sugerir(
    descripcion: Annotated[
        str, typer.Argument(help="Qué quieres hacer, en lenguaje natural.")
    ],
) -> None:
    """Propone una acción para acciones.json a partir de una descripción."""
    try:
        accion = modulo_ia.sugerir_accion(descripcion)
    except TareasError as error:
        _mostrar_error(error)

    consola.print(
        "[green]✔ Acción propuesta y validada con el esquema de tareas:[/green]"
    )
    consola.print_json(data=accion)
    consola.print(
        "Si te vale, añádela a acciones.json (o usa /nueva-accion en OpenCode)"
        " y comprueba con [bold]tareas validar[/bold] y --simular."
    )


@ia_app.command()
def explicar(
    ctx: typer.Context,
    nombre: Annotated[
        str, typer.Argument(help="Nombre de la acción (ver: tareas acciones).")
    ],
    carpeta: Annotated[
        Path | None,
        typer.Argument(help="Carpeta sobre la que simular (por defecto, el origen)."),
    ] = None,
) -> None:
    """Simula una acción y explica en claro qué pasaría."""
    try:
        motor = Motor(_cargar_acciones(ctx))
        resultados = motor.ejecutar(nombre, carpeta, simular=True)
        explicacion = modulo_ia.explicar_simulacion(nombre, resultados)
    except TareasError as error:
        _mostrar_error(error)

    consola.print(explicacion)
    consola.print("[dim](Simulación: no se ha tocado ningún fichero.)[/dim]")
