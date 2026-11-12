"""Clases que saben aplicar una acción a una lista de ficheros."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .errores import IANoDisponible

if TYPE_CHECKING:  # .ia importa a este módulo: aquí solo para anotar tipos
    from .ia import ProveedorIA, RespuestaIA

SISTEMA_RESUMIR = (
    "Eres un estudiante de 1º DAM que resume apuntes para repasar. "
    "Respondes SOLO en español y en markdown: un título de una línea y "
    "viñetas cortas. Sin preámbulos ni despedidas y sin inventar nada que "
    "no esté en el documento."
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
        if self.proveedor is None:
            raise IANoDisponible(
                "Esta acción necesita IA y no hay proveedor configurado. "
                "Mira el estado con «tareas comprobar-ia»."
            )
        usuario = (
            f"{self.instrucciones}\n\n"
            f"<documento nombre=\"{fichero.name}\">\n{texto}\n</documento>"
        )
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
