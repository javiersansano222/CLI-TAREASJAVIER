"""Clases que saben aplicar una acción a una lista de ficheros."""

from __future__ import annotations

import re
import shutil
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .config import CARACTERES_PROHIBIDOS, NOMBRES_RESERVADOS
from .errores import IANoDisponible

if TYPE_CHECKING:  # .ia importa a este módulo: aquí solo para anotar tipos
    from .ia import ProveedorIA, RespuestaIA

SISTEMA_RESUMIR = (
    "Eres un estudiante de 1º DAM que resume apuntes para repasar. "
    "Respondes SOLO en español y en markdown: un título de una línea y "
    "viñetas cortas. Sin preámbulos ni despedidas y sin inventar nada que "
    "no esté en el documento."
)

SISTEMA_RENOMBRAR = (
    "Eres un estudiante de 1º DAM que ordena sus apuntes. Respondes SOLO "
    "con el nombre nuevo del fichero, en minúsculas y con guiones, sin "
    "extensión, sin comillas y sin ningún texto alrededor. Máximo 60 "
    "caracteres. Si el nombre ya es bueno, repítelo tal cual."
)

SISTEMA_CLASIFICAR = (
    "Eres un estudiante de 1º DAM que clasifica sus apuntes por asignatura. "
    "Respondes SOLO con una de las categorías que te indiquen, escrita "
    "exactamente igual, sin comillas y sin ningún texto alrededor."
)


@dataclass(frozen=True)
class Resultado:
    """Informe de lo que ha pasado con un fichero."""

    origen: Path
    destino: Path | None
    estado: str
    detalle: str | None = None


def destino_libre(
    destino: Path,
    reservados: set[Path] | None = None,
    desaparecidos: set[Path] | None = None,
) -> Path:
    """Devuelve una ruta libre frente al disco y a los destinos ya calculados."""
    ocupados = reservados if reservados is not None else set()
    vaciados = desaparecidos if desaparecidos is not None else set()
    libre = destino
    numero = 1
    while (
        ((libre.exists() or libre.is_symlink()) and libre not in vaciados)
        or libre in ocupados
    ):
        libre = destino.with_name(f"{destino.stem} ({numero}){destino.suffix}")
        numero += 1
    return libre


def leer_texto(fichero: Path, tope: int) -> str:
    """Devuelve el texto de un .pdf, .txt o .md cortado a «tope» caracteres.

    Los PDF se leen con pypdf (dependencia que se importa aquí dentro, para
    que la CLI arranque aunque no esté). Si el PDF no tiene texto extraíble o
    el formato no es de texto, lanza ValueError: la acción lo convierte en
    «saltado» y sigue con el siguiente fichero.
    """
    extension = fichero.suffix.lower()
    if extension == ".pdf":
        texto = _texto_pdf(fichero)
    elif extension in {".txt", ".md"}:
        try:
            texto = fichero.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ValueError(f"no se puede leer: {exc}") from None
    else:
        raise ValueError(
            f"«{extension or 'sin extensión'}» no es un formato de texto legible"
        )
    return texto[:tope]


def _texto_pdf(fichero: Path) -> str:
    """Extrae el texto de todas las páginas de un PDF."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ValueError(
            "para leer PDF hace falta pypdf: instálalo con «uv add pypdf»"
        ) from None
    try:
        lector = PdfReader(str(fichero))
        partes = [pagina.extract_text() or "" for pagina in lector.pages]
    except Exception as exc:  # pypdf lanza tipos variados con PDFs rotos
        raise ValueError(
            f"el PDF no se puede leer ({exc.__class__.__name__})"
        ) from None
    return "\n".join(partes)


def a_nombre_seguro(texto: str, tope: int = 60) -> str:
    """Convierte lo que diga la IA en un nombre apto para cualquier sistema.

    Quita comillas, caracteres prohibidos en Windows (/ \\ < > : " | ? *),
    puntos finales, espacios repetidos y nombres reservados; recorta a «tope»
    y devuelve vacío si no queda nada utilizable (la acción lo saltará).
    """
    nombre = texto.strip().strip("\"'«»").replace("\n", " ")
    nombre = "".join(
        " " if caracter in CARACTERES_PROHIBIDOS else caracter
        for caracter in nombre
    )
    nombre = " ".join(nombre.split())[:tope].strip(" .")
    if not nombre or nombre in {".", ".."}:
        return ""
    base = nombre.split(".", maxsplit=1)[0].upper()
    if base in NOMBRES_RESERVADOS or re.fullmatch(r"(?:COM|LPT)[1-9]", base):
        return f"n-{nombre}"
    return nombre


class Accion(ABC):
    """Base de todas las acciones; cada subclase se registra sola por su tipo."""

    tipo = ""
    destructiva = False
    necesita_ia = False
    _registro: dict[str, type[Accion]] = {}

    def __init__(self, config: dict[str, Any]) -> None:
        self.nombre: str = config["nombre"]
        self.descripcion: str = config["descripcion"]
        self.config = config
        self._reservados: set[Path] = set()
        self._desaparecidos: set[Path] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.tipo:
            Accion._registro[cls.tipo] = cls

    @property
    def confirmar(self) -> bool:
        """Indica si hay que pedir confirmación antes de ejecutar de verdad."""
        return bool(self.config.get("confirmar", True))

    @staticmethod
    def desde_config(config: dict[str, Any]) -> Accion:
        """Fábrica: convierte un diccionario del JSON en la clase que toca."""
        clase = Accion._registro.get(config["tipo"])
        if clase is None:
            raise ValueError(f"No hay ninguna clase registrada para «{config['tipo']}»")
        return clase(config)

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        """Aplica la acción a cada fichero y devuelve un resultado por fichero."""
        self._reservados = set()
        self._desaparecidos = set()
        resultados: list[Resultado] = []
        for numero, fichero in enumerate(ficheros, start=1):
            try:
                resultado = self.aplicar(fichero, numero, simular)
            except (
                OSError,
                ValueError,
                OverflowError,
                KeyError,
                IndexError,
                AttributeError,
                shutil.Error,
            ) as exc:
                detalle = str(exc) or exc.__class__.__name__
                resultado = Resultado(fichero, None, "error", detalle)
            resultados.append(resultado)
        return resultados

    def _destino_libre(self, destino: Path) -> Path:
        libre = destino_libre(destino, self._reservados, self._desaparecidos)
        self._reservados.add(libre)
        return libre

    @abstractmethod
    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        """Aplica la acción a un único fichero."""


class Mover(Accion):
    tipo = "mover"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta = Path(self.config["destino"]).expanduser()
        destino = self._destino_libre(carpeta / fichero.name)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.move(fichero, destino)
        self._desaparecidos.add(fichero)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Copiar(Accion):
    tipo = "copiar"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        carpeta = Path(self.config["destino"]).expanduser()
        destino = self._destino_libre(carpeta / fichero.name)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fichero, destino)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Renombrar(Accion):
    tipo = "renombrar"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        fecha = datetime.fromtimestamp(fichero.stat().st_mtime)
        nuevo_nombre = self.config["plantilla"].format(
            fecha=fecha,
            n=n,
            ext=fichero.suffix.lower(),
            nombre=fichero.stem,
        )
        if nuevo_nombre == fichero.name:
            return Resultado(fichero, None, "saltado")

        destino = self._destino_libre(fichero.with_name(nuevo_nombre))
        if not simular:
            fichero.rename(destino)
        self._desaparecidos.add(fichero)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Borrar(Accion):
    tipo = "borrar"
    destructiva = True

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        if not simular:
            fichero.unlink()
        self._desaparecidos.add(fichero)
        return Resultado(fichero, None, "simulado" if simular else "hecho")


class MirarEspacio(Accion):
    tipo = "mirar_espacio"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        try:
            total = sum(f.stat().st_size for f in fichero.parent.iterdir() if f.is_file())
            return Resultado(fichero, None, "hecho", f"Total: {total / 1024 / 1024:.2f} MB ({len(list(fichero.parent.iterdir()))} ficheros)")
        except OSError as exc:
            return Resultado(fichero, None, "error", str(exc))


class AccionIA(Accion):
    """Base de las acciones que mandan texto al modelo y guardan su respuesta.

    El proveedor lo inyecta el motor antes de ejecutar: sin él (o en
    simulación) nunca se gasta un solo token.
    """

    tipo = ""
    necesita_ia = True
    max_tokens = 1200

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.proveedor: ProveedorIA | None = None

    @property
    def max_caracteres(self) -> int:
        """Tope de texto que se envía al modelo para no pasarnos de contexto."""
        return int(self.config.get("max_caracteres", 12_000))

    @property
    def instrucciones(self) -> str:
        """Lo que el usuario pide que se haga con el documento."""
        return str(self.config.get("instrucciones", "")).strip()

    def presupuesto(self, caracteres: int) -> str:
        """Lo que costaría procesar este fichero; es lo único que enseña --simular."""
        return (
            f"enviaría {caracteres} caracteres "
            f"(~{max(1, caracteres // 4)} tokens, sin gastar)"
        )

    def preguntar(self, sistema: str, fichero: Path, texto: str) -> RespuestaIA:
        """Pide al modelo que trabaje sobre el texto de un fichero ya leído."""
        usuario = f"<documento nombre=\"{fichero.name}\">\n{texto}\n</documento>"
        return self.preguntar_texto(sistema, usuario)

    def preguntar_texto(self, sistema: str, usuario: str) -> RespuestaIA:
        """Última llamada al modelo: aquí se comprueba que haya proveedor."""
        if self.proveedor is None:
            raise IANoDisponible(
                "Esta acción necesita IA y no hay proveedor configurado. "
                "Mira el estado con «tareas comprobar-ia»."
            )
        if self.instrucciones:
            usuario = f"{self.instrucciones}\n\n{usuario}"
        return self.proveedor.completar(sistema, usuario, max_tokens=self.max_tokens)


class Resumir(AccionIA):
    """Escribe un .resumen.md junto a cada apunte (o en «destino»)."""

    tipo = "resumir"

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        try:
            texto = leer_texto(fichero, self.max_caracteres)
        except ValueError as exc:
            return Resultado(fichero, None, "saltado", str(exc))
        if not texto.strip():
            return Resultado(fichero, None, "saltado", "no contiene texto extraíble")

        if simular:
            return Resultado(fichero, None, "simulado", self.presupuesto(len(texto)))

        respuesta = self.preguntar(SISTEMA_RESUMIR, fichero, texto)
        carpeta = (
            Path(self.config["destino"]).expanduser()
            if "destino" in self.config
            else fichero.parent
        )
        destino = self._destino_libre(carpeta / f"{fichero.stem}.resumen.md")
        carpeta.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            f"# Resumen de {fichero.name}\n\n{respuesta.texto}\n",
            encoding="utf-8",
        )
        return Resultado(fichero, destino, "hecho", respuesta.resumen())


class RenombrarIA(AccionIA):
    """Pide a la IA un nombre mejor y renombra el fichero en su misma carpeta.

    La extensión original nunca se toca: solo cambia la base del nombre, y
    lo que devuelva el modelo pasa siempre por a_nombre_seguro().
    """

    tipo = "renombrar_ia"
    max_tokens = 60

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        try:
            texto = leer_texto(fichero, self.max_caracteres)
        except ValueError:
            texto = ""  # imagen u otro formato: solo se manda el nombre actual

        if simular:
            return Resultado(
                fichero,
                None,
                "simulado",
                self.presupuesto(len(texto) + len(fichero.name)),
            )

        extracto = texto.strip() or "(sin texto legible: usa solo el nombre)"
        usuario = f"Nombre actual: {fichero.name}\n\n{extracto}"
        respuesta = self.preguntar_texto(SISTEMA_RENOMBRAR, usuario)
        base = a_nombre_seguro(respuesta.texto)
        if not base:
            return Resultado(
                fichero, None, "saltado", "la IA no ha propuesto un nombre válido"
            )

        nuevo = f"{base}{fichero.suffix}"
        if nuevo == fichero.name:
            return Resultado(fichero, None, "saltado", "el nombre ya es bueno")

        destino = self._destino_libre(fichero.with_name(nuevo))
        if not simular:
            fichero.rename(destino)
        self._desaparecidos.add(fichero)
        return Resultado(fichero, destino, "hecho", respuesta.resumen())


class Classificar(AccionIA):
    """Reparte los apuntes en subcarpetas de «destino» según la categoría que
    elija la IA entre las declaradas en «categorias»."""

    tipo = "clasificar"

    @property
    def categorias(self) -> list[str]:
        return [str(c) for c in self.config.get("categorias", [])]

    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado:
        try:
            texto = leer_texto(fichero, self.max_caracteres)
        except ValueError as exc:
            return Resultado(fichero, None, "saltado", str(exc))
        if not texto.strip():
            return Resultado(fichero, None, "saltado", "no contiene texto extraíble")

        if simular:
            return Resultado(fichero, None, "simulado", self.presupuesto(len(texto)))

        usuario = (
            f"Categorías posibles: {', '.join(self.categorias)}\n\n"
            f"<documento nombre=\"{fichero.name}\">\n{texto}\n</documento>"
        )
        respuesta = self.preguntar_texto(SISTEMA_CLASIFICAR, usuario)
        categoria = _categoria_mas_cercana(respuesta.texto, self.categorias)
        if categoria is None:
            return Resultado(
                fichero,
                None,
                "saltado",
                f"«{respuesta.texto.strip()[:40]}» no es una categoría conocida",
            )

        carpeta = Path(self.config["destino"]).expanduser() / categoria
        destino = self._destino_libre(carpeta / fichero.name)
        carpeta.mkdir(parents=True, exist_ok=True)
        shutil.move(str(fichero), str(destino))
        self._desaparecidos.add(fichero)
        return Resultado(
            fichero, destino, "hecho", f"categoría «{categoria}» · {respuesta.resumen()}"
        )


def _categoria_mas_cercana(texto: str, categorias: list[str]) -> str | None:
    """Casa la respuesta con una categoría ignorando mayúsculas y tildes.

    Si el modelo devuelve algo que no está en la lista, no se inventa una
    carpeta: se salta el fichero y se avisa en la columna Detalle.
    """
    limpia = _sin_tildes(texto).strip().lower()
    for categoria in categorias:
        if _sin_tildes(categoria).strip().lower() == limpia:
            return categoria
    return None


def _sin_tildes(texto: str) -> str:
    """Quita las tildes: «Programación» y «programacion» son la misma cosa."""
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
