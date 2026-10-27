"""Comprime imágenes en una carpeta sin modificar los originales."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .errores import TareasError

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}
FORMATOS_EXTENSION = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}
NOMBRE_DESTINO = "comprimidas"
CALIDAD_MIN = 1
CALIDAD_MAX = 95


@dataclass(frozen=True)
class Imagen:
    """Datos mínimos de una imagen para listarla o comprimirla."""

    ruta: Path
    tamano: int


@dataclass(frozen=True)
class Resultado:
    """Resultado de comprimir una imagen."""

    origen: Path
    destino: Path | None
    tamano_original: int
    tamano_final: int
    estado: str
    detalle: str = ""


def seleccionar(carpeta: Path) -> list[Imagen]:
    """Devuelve las imágenes compatibles del primer nivel de la carpeta."""
    if not carpeta.is_dir():
        raise TareasError(f"La carpeta «{carpeta}» no existe o no es una carpeta.")

    try:
        entradas = sorted(
            carpeta.iterdir(),
            key=lambda ruta: (ruta.name.lower(), ruta.name),
        )
    except OSError as exc:
        raise TareasError(f"No se puede leer la carpeta «{carpeta}»: {exc}") from None

    imagenes: list[Imagen] = []
    for ruta in entradas:
        try:
            if ruta.is_symlink() or not ruta.is_file():
                continue
            if ruta.suffix.lower() not in EXTENSIONES:
                continue
            datos = ruta.stat()
        except OSError:
            continue
        imagenes.append(Imagen(ruta, datos.st_size))
    return imagenes


def _ocupado(ruta: Path) -> bool:
    return ruta.exists() or ruta.is_symlink()


def _destino_unico(destino: Path) -> Path:
    if not _ocupado(destino):
        return destino
    for numero in range(1, 1000):
        candidato = destino.with_name(
            f"{destino.stem} ({numero}){destino.suffix}"
        )
        if not _ocupado(candidato):
            return candidato
    raise TareasError(f"No hay un nombre libre para «{destino.name}».")


def _a_rgb(imagen: Image.Image) -> Image.Image:
    """Convierte a RGB, poniendo fondo blanco si hay transparencia."""
    if imagen.mode in {"RGBA", "LA"} or (
        imagen.mode == "P" and "transparency" in imagen.info
    ):
        rgba = imagen.convert("RGBA")
        fondo = Image.new("RGB", rgba.size, (255, 255, 255))
        fondo.paste(rgba, mask=rgba.getchannel("A"))
        return fondo
    return imagen.convert("RGB") if imagen.mode != "RGB" else imagen


def _preparar_salida(imagen: Image.Image, formato: str) -> Image.Image:
    if formato == "JPEG":
        return _a_rgb(imagen)
    if formato == "WEBP":
        tiene_alfa = imagen.mode in {"RGBA", "LA"} or (
            imagen.mode == "P" and "transparency" in imagen.info
        )
        return imagen.convert("RGBA" if tiene_alfa else "RGB")
    return imagen


def _opciones_guardado(
    imagen: Image.Image,
    formato: str,
    calidad: int,
) -> dict[str, object]:
    opciones: dict[str, object] = {}
    if formato == "JPEG":
        opciones.update(quality=calidad, optimize=True, progressive=True)
    elif formato == "PNG":
        opciones.update(optimize=True, compress_level=9)
    elif formato == "WEBP":
        opciones.update(quality=calidad, method=6)

    exif = imagen.info.get("exif")
    if exif and formato in {"JPEG", "WEBP"}:
        opciones["exif"] = exif
    icc = imagen.info.get("icc_profile")
    if icc:
        opciones["icc_profile"] = icc
    return opciones


def _comprimir_una(origen: Path, destino: Path, calidad: int) -> int:
    try:
        with Image.open(origen) as original:
            if getattr(original, "is_animated", False):
                raise TareasError(f"«{origen.name}» es animada; se omite.")

            formato = (original.format or "").upper()
            if formato not in {"JPEG", "PNG", "WEBP"}:
                raise TareasError(
                    f"«{origen.name}» no tiene un formato compatible."
                )
            esperado = FORMATOS_EXTENSION.get(origen.suffix.lower())
            if formato != esperado:
                raise TareasError(
                    f"«{origen.name}» no coincide con su extensión "
                    f"(contiene {formato})."
                )

            salida = _preparar_salida(original, formato)
            opciones = _opciones_guardado(original, formato, calidad)
            destino.parent.mkdir(parents=True, exist_ok=True)
            salida.save(destino, format=formato, **opciones)
            if salida is not original:
                salida.close()
        return destino.stat().st_size
    except (
        Image.DecompressionBombError,
        OSError,
        OverflowError,
        UnidentifiedImageError,
        ValueError,
    ) as exc:
        try:
            destino.unlink(missing_ok=True)
        except OSError:
            pass
        raise TareasError(f"No se puede comprimir «{origen.name}»: {exc}") from None


def comprimir(
    imagenes: list[Imagen],
    carpeta_destino: Path,
    calidad: int,
    simular: bool,
) -> list[Resultado]:
    """Comprime las imágenes indicadas y devuelve un resultado por cada una."""
    resultados: list[Resultado] = []
    for imagen in imagenes:
        destino: Path | None = None
        try:
            destino = _destino_unico(carpeta_destino / imagen.ruta.name)
            if simular:
                resultados.append(
                    Resultado(
                        imagen.ruta,
                        destino,
                        imagen.tamano,
                        0,
                        "simulado",
                        f"calidad {calidad}",
                    )
                )
                continue

            final = _comprimir_una(imagen.ruta, destino, calidad)
            if final >= imagen.tamano:
                try:
                    destino.unlink(missing_ok=True)
                except OSError:
                    pass
                resultados.append(
                    Resultado(
                        imagen.ruta,
                        destino,
                        imagen.tamano,
                        final,
                        "saltado",
                        "no reduce el tamaño",
                    )
                )
            else:
                resultados.append(
                    Resultado(
                        imagen.ruta,
                        destino,
                        imagen.tamano,
                        final,
                        "hecho",
                    )
                )
        except TareasError as error:
            resultados.append(
                Resultado(
                    imagen.ruta,
                    destino,
                    imagen.tamano,
                    0,
                    "error",
                    str(error),
                )
            )
    return resultados
