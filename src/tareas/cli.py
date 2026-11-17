"""Interfaz de línea de órdenes: aquí solo hay órdenes, opciones y salida."""

from datetime import datetime
from pathlib import Path
import re
import sys
from typing import Annotated, Any, NoReturn

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from tareas import __version__
from tareas import ajustes as modulo_ajustes
from tareas import capturas as modulo_capturas
from tareas import config as configuracion
from tareas import doctor as modulo_doctor
from tareas import exportar_tema as modulo_exportar
from tareas import historial as modulo_historial
from tareas import ia as modulo_ia
from tareas import imagenes as modulo_imagenes
from tareas import informe as modulo_informe
from tareas import mover as modulo_mover
from tareas import organizar as modulo_organizar
from tareas import temporales as modulo_temporales
from tareas import terminal as modulo_terminal
from tareas.acciones import Resultado
from tareas.bienvenida import mostrar_bienvenida
from tareas.chuleta import mostrar_chuleta
from tareas.errores import TareasError
from tareas.sistema import mostrar_sistema
from tareas.menu import cambiar_color, color_actual, menu_activo, menu_interactivo, _mostrar_cita_motivacional
from tareas.motor import Motor
from tareas.terminal import PALETAS, Paleta

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

    hechos = sum(
        resultado.estado in ("hecho", "movido", "copiado")
        for resultado in resultados
    )
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
        _aplicar_tema_guardado()
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


def _escribir_secuencias(texto: str) -> None:
    """Manda las secuencias tal cual: Rich las partiría al envolver renglones."""
    sys.stdout.write(texto)
    sys.stdout.flush()


def _aplicar_tema_guardado() -> None:
    """Al abrir el menú, recupera el tema elegido si el terminal lo admite."""
    nombre = modulo_ajustes.tema_elegido()
    if not nombre or not modulo_terminal.detectar().soportado:
        return
    try:
        paleta = modulo_ajustes.buscar_tema(nombre)
    except TareasError:
        return
    _escribir_secuencias(modulo_terminal.aplicar(paleta))


def _muestra(paleta: Paleta) -> str:
    """Muestra de la paleta: una ficha y los 16 colores en bloques."""
    bloques = "".join(f"[{color}]█[/]" for color in paleta.ansi)
    return f"[on {paleta.fondo}][{paleta.texto}] tareas [/][/] {bloques}"


def _tabla_temas() -> None:
    """Los temas disponibles, con el elegido marcado."""
    actual = modulo_ajustes.tema_elegido()
    todos = {**PALETAS, **modulo_ajustes.temas_propios()}

    tabla = Table(title="Temas de terminal", header_style="bold")
    tabla.add_column("Tema")
    tabla.add_column("Descripción")
    tabla.add_column("Muestra")
    for clave in sorted(todos):
        marca = "✔" if clave == actual else " "
        tabla.add_row(f"{marca} {clave}", todos[clave].descripcion, _muestra(todos[clave]))
    consola.print(tabla)
    consola.print(
        "[dim]Aplícalo con «tareas tema matrix»; vista previa sin tocar nada, "
        "«tareas tema --ver matrix»; para otro terminal, "
        "«tareas tema --exportar matrix».[/dim]"
    )


def _vista_previa(paleta: Paleta) -> None:
    """Enseña cómo queda el tema sin aplicarlo ni guardarlo."""
    consola.print(
        Panel.fit(
            f"[{paleta.texto}]Así se verán los mensajes sobre el fondo "
            f"«{paleta.nombre}».[/]\n\n"
            f"[{paleta.texto}]✔ hecho   ✘ error   ⚠ aviso   "
            f"tareas version[/]\n\n"
            f"{_muestra(paleta)}",
            title=f"tareas tema {paleta.nombre}",
            subtitle=paleta.descripcion,
            style=f"on {paleta.fondo}",
            border_style=paleta.cursor,
        )
    )
    consola.print(
        "[dim]Nada aplicado todavía: quita «--ver» para cambiar los colores "
        "de esta sesión.[/dim]"
    )


def _nombre_de_tema(valor: str) -> str:
    """Valida el nombre de un tema propio antes de guardarlo."""
    clave = valor.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,23}", clave):
        raise typer.BadParameter(
            "usa letras sin tilde, números, guion o guion bajo (máximo 24)",
            param_hint="--crear",
        )
    return clave


def _color_de_tema(valor: str, opcion: str) -> str:
    """Valida un color hex y lo devuelve normalizado."""
    try:
        return modulo_terminal.normalizar_hex(valor)
    except TareasError:
        raise typer.BadParameter(
            "escribe seis dígitos hex, por ejemplo #0b1020",
            param_hint=opcion,
        ) from None


@app.command()
def tema(
    nombre: Annotated[
        str | None,
        typer.Argument(
            help="Tema a aplicar: medianoche, matrix, papel, ambar, oceano, "
            "contraste o uno creado por ti.",
        ),
    ] = None,
    ver: Annotated[
        str | None,
        typer.Option("--ver", help="Vista previa de un tema, sin aplicarlo."),
    ] = None,
    restablecer: Annotated[
        bool,
        typer.Option("--restablecer", help="Devuelve los colores originales."),
    ] = False,
    exportar: Annotated[
        str | None,
        typer.Option(
            "--exportar",
            help="Genera los ficheros de Windows Terminal, iTerm2 y GNOME.",
        ),
    ] = None,
    destino: Annotated[
        Path | None,
        typer.Option(
            "--destino",
            help="Carpeta de los ficheros exportados (por defecto, la actual).",
        ),
    ] = None,
    crear: Annotated[
        str | None,
        typer.Option(
            "--crear",
            help="Guarda un tema propio con --fondo, --texto y --cursor.",
        ),
    ] = None,
    desde: Annotated[
        str,
        typer.Option("--desde", help="Tema del que copiar los 16 colores."),
    ] = "medianoche",
    fondo: Annotated[
        str | None,
        typer.Option("--fondo", help="Color de fondo al crear: #0b1020."),
    ] = None,
    texto: Annotated[
        str | None,
        typer.Option("--texto", help="Color del texto al crear: #d7dcf5."),
    ] = None,
    cursor: Annotated[
        str | None,
        typer.Option("--cursor", help="Color del cursor al crear: #7aa2f7."),
    ] = None,
    sin_paleta: Annotated[
        bool,
        typer.Option(
            "--sin-paleta",
            help="Cambia solo fondo, texto y cursor, sin tocar los 16 colores.",
        ),
    ] = False,
) -> None:
    """Cambia los colores de la terminal: seis temas o uno propio."""
    if restablecer:
        _escribir_secuencias(modulo_terminal.restablecer())
        modulo_ajustes.guardar_tema("")
        consola.print("✔ Colores del terminal restablecidos.")
        return

    if crear:
        clave = _nombre_de_tema(crear)
        if not (fondo and texto and cursor):
            raise typer.BadParameter(
                "al crear un tema hacen falta --fondo, --texto y --cursor",
                param_hint="--crear",
            )
        try:
            base = modulo_ajustes.buscar_tema(desde)
        except TareasError as error:
            _mostrar_error(error)
        propia = Paleta(
            nombre=clave,
            descripcion=f"tema propio sobre {base.nombre}",
            fondo=_color_de_tema(fondo, "--fondo"),
            texto=_color_de_tema(texto, "--texto"),
            cursor=_color_de_tema(cursor, "--cursor"),
            ansi=base.ansi,
        )
        ruta = modulo_ajustes.guardar_tema_propio(propia)
        consola.print(
            f"[{propia.cursor}]✔ Tema «{clave}» guardado en {ruta}.[/{propia.cursor}]"
        )
        consola.print(
            f"[dim]Pruébalo con «tareas tema --ver {clave}» y aplícalo con "
            f"«tareas tema {clave}».[/dim]"
        )
        return

    if exportar:
        try:
            paleta = modulo_ajustes.buscar_tema(exportar)
        except TareasError as error:
            _mostrar_error(error)
        carpeta = (destino or Path.cwd()).expanduser()
        ficheros = modulo_exportar.guardar(paleta, carpeta)
        tabla = Table(title=f"Tema «{paleta.nombre}» exportado", header_style="bold")
        tabla.add_column("Fichero")
        tabla.add_column("Tamaño", justify="right")
        for fichero in ficheros:
            tabla.add_row(str(fichero), tamano_legible(fichero.stat().st_size))
        consola.print(tabla)
        consola.print(
            "[dim]Windows Terminal: Configuración → Abrir JSON y pega el objeto "
            "en «schemes».\n"
            "iTerm2: Preferencias → Profiles → Colors → Color Presets → Import.\n"
            "GNOME Terminal o Tilix: ejecuta el script .sh una vez.[/dim]"
        )
        return

    if ver:
        try:
            paleta = modulo_ajustes.buscar_tema(ver)
        except TareasError as error:
            _mostrar_error(error)
        _vista_previa(paleta)
        return

    if nombre is None:
        _tabla_temas()
        return

    try:
        paleta = modulo_ajustes.buscar_tema(nombre)
    except TareasError as error:
        _mostrar_error(error)

    soporte = modulo_terminal.detectar()
    if not soporte.soportado:
        consola.print(
            f"[yellow]⚠ Este terminal ({soporte.terminal}) no admite cambiar "
            f"los colores de la sesión.[/yellow]"
        )
        if soporte.nota:
            consola.print(f"[dim]{escape(soporte.nota)}[/dim]")
        consola.print(
            f"[dim]Para dejarlo puesto de forma permanente: "
            f"«tareas tema --exportar {paleta.nombre}».[/dim]"
        )
        return

    _escribir_secuencias(modulo_terminal.aplicar(paleta, con_paleta=not sin_paleta))
    modulo_ajustes.guardar_tema(paleta.nombre)
    consola.print(f"✔ Tema «{paleta.nombre}» aplicado a esta sesión.")
    consola.print("[dim]Se recordará al abrir el menú de «tareas».[/dim]")


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
def organizar(
    carpeta: Annotated[
        Path,
        typer.Argument(help="Carpeta que quieres ordenar (por defecto, la actual)."),
    ] = Path("."),
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué haría sin mover ni copiar nada."),
    ] = False,
    copiar: Annotated[
        bool,
        typer.Option("--copiar", help="Copia los ficheros en vez de moverlos."),
    ] = False,
) -> None:
    """Ordena los ficheros de una carpeta en subcarpetas por tipo."""
    ruta = carpeta.expanduser()
    try:
        resultados = modulo_organizar.ejecutar(
            ruta, simular=simular, copiar=copiar
        )
    except TareasError as error:
        _mostrar_error(error)

    if not resultados:
        consola.print(
            f"No hay ficheros que ordenar en «{escape(str(ruta))}»."
        )
        return

    if not simular:
        modulo_historial.registrar(
            "organizar", resultados, "copiar" if copiar else "mover"
        )

    if not _pintar_resultados(
        resultados, "organizar", simular, ruta_completa=False
    ):
        raise typer.Exit(code=1)

    if not simular:
        carpetas = sorted(
            {resultado.destino.parent.name for resultado in resultados if resultado.destino}
        )
        consola.print(
            f"[dim]Carpetas: {escape(', '.join(carpetas))}.[/dim]"
        )


@app.command()
def mover(
    archivo: Annotated[
        Path,
        typer.Argument(
            help="Fichero que quieres mover (ruta completa o solo el nombre)."
        ),
    ],
    destino: Annotated[
        Path,
        typer.Argument(help="Carpeta donde quieres dejarlo."),
    ],
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué haría sin mover ni copiar nada."),
    ] = False,
    copiar: Annotated[
        bool,
        typer.Option("--copiar", help="Copia el fichero y deja el original."),
    ] = False,
) -> None:
    """Mueve un fichero concreto a la carpeta que le indiques."""
    try:
        resultado = modulo_mover.ejecutar(
            archivo, destino, simular=simular, copiar=copiar
        )
    except TareasError as error:
        _mostrar_error(error)

    if not simular:
        modulo_historial.registrar(
            "mover", [resultado], "copiar" if copiar else "mover"
        )

    if not _pintar_resultados([resultado], "mover", simular, ruta_completa=False):
        raise typer.Exit(code=1)


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
    if not simular:
        modulo_historial.registrar("capturas", resultados, "papelera")
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
    if not simular:
        modulo_historial.registrar("temporales", resultados, "papelera")
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
    if not simular:
        modulo_historial.registrar("imagenes", resultados, "crear")
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

    if not simular:
        tipo = {
            "mover": "mover",
            "copiar": "copiar",
            "renombrar": "renombrar",
            "renombrar_ia": "renombrar",
            "clasificar": "mover",
            "borrar": "borrar",
            "resumir": "crear",
        }.get(accion.tipo)
        if tipo:
            modulo_historial.registrar(f"ejecutar {nombre}", resultados, tipo)

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
    informes = [c for c in comprobaciones if c.estado == "info"]

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
    else:
        consola.print("[green]✔ Todo listo.[/green]")

    if informes:
        nombres = ", ".join(comprobacion.nombre for comprobacion in informes)
        consola.print(f"[dim]ℹ Sin configurar: {escape(nombres)}.[/dim]")


@app.command()
def historial(
    n: Annotated[
        int,
        typer.Option("--n", help="Cuántos lotes mostrar (por defecto, 10)."),
    ] = 10,
) -> None:
    """Muestra las últimas operaciones y si se pueden deshacer."""
    if n < 1:
        raise typer.BadParameter("debe ser 1 o más", param_hint="--n")

    lotes = modulo_historial.leer()
    if not lotes:
        consola.print(
            "El historial está vacío: todavía no se ha ejecutado ninguna "
            "operación que cambie ficheros."
        )
        return

    tabla = Table(title="Historial de operaciones")
    tabla.add_column("Fecha")
    tabla.add_column("Orden")
    tabla.add_column("Operaciones", justify="right")
    tabla.add_column("¿Deshacer?", justify="center")
    for lote in lotes[-n:]:
        operaciones = lote.get("operaciones", [])
        marca = (
            "[green]sí[/green]"
            if modulo_historial.reversible(lote)
            else "[yellow]no[/yellow]"
        )
        tabla.add_row(
            escape(str(lote.get("fecha", "—"))),
            escape(str(lote.get("orden", "—"))),
            str(len(operaciones)),
            marca,
        )
    consola.print(tabla)
    consola.print(
        f"[dim]{len(lotes)} lote(s) en {escape(str(modulo_historial.ruta()))}. "
        "Deshaz el último con «tareas deshacer».[/dim]"
    )


@app.command()
def deshacer(
    simular: Annotated[
        bool,
        typer.Option("--simular", help="Enseña qué revertiría sin tocar nada."),
    ] = False,
) -> None:
    """Revierte el lote reversible más reciente del historial."""
    try:
        informe = modulo_historial.deshacer(simular)
    except TareasError as error:
        _mostrar_error(error)

    titulo = (
        "deshacer (SIMULACIÓN: no se ha tocado nada)"
        if simular
        else "deshacer (resultado)"
    )
    tabla = Table(title=titulo)
    tabla.add_column("Tipo")
    tabla.add_column("Origen")
    tabla.add_column("Destino")
    tabla.add_column("Estado")
    tabla.add_column("Detalle")
    for operacion in informe.operaciones:
        tabla.add_row(
            escape(operacion.tipo),
            escape(str(operacion.origen)),
            escape(str(operacion.destino) if operacion.destino else "—"),
            operacion.estado,
            escape(operacion.detalle),
        )
    consola.print(tabla)
    consola.print(
        f"Lote «{escape(informe.orden)}» del {escape(informe.fecha)} · "
        f"deshechas: {informe.deshechas} · simuladas: {informe.simuladas}"
    )
    if informe.omitidos:
        consola.print(
            f"[dim]Se saltan {informe.omitidos} lote(s) más reciente(s) que no "
            "se pueden deshacer.[/dim]"
        )

    if simular:
        consola.print("Para deshacerlo de verdad, repite la orden sin --simular.")
        return
    if informe.deshechas:
        consola.print("Lote eliminado del historial.")
        return
    consola_err.print(
        "[yellow]⚠ No se ha podido deshacer nada de este lote; "
        "sigue en el historial.[/yellow]"
    )
    raise typer.Exit(code=1)


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
