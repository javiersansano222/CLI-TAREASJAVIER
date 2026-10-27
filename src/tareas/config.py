"""Carga y valida acciones.json antes de que el motor toque ningún fichero."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from string import Formatter
from typing import Any

from .errores import AccionNoValida, ConfigError

TIPOS = {"mover", "copiar", "renombrar", "borrar"}
CAMPOS_RAIZ = {"version", "acciones"}
CAMPOS_ACCION = {
    "nombre",
    "descripcion",
    "tipo",
    "origen",
    "filtro",
    "destino",
    "plantilla",
    "confirmar",
}
CAMPOS_OBLIGATORIOS = ("nombre", "descripcion", "tipo")
CAMPOS_POR_TIPO = {
    "mover": ("destino",),
    "copiar": ("destino",),
    "renombrar": ("plantilla",),
}
CAMPOS_FILTRO = {
    "extensiones",
    "patron",
    "mas_antiguo_que_dias",
    "mayor_que_mb",
}
CAMPOS_PLANTILLA = {"fecha", "n", "ext", "nombre"}
CARACTERES_PROHIBIDOS = set('/\\<>:"|?*')
NOMBRES_RESERVADOS = {"CON", "PRN", "AUX", "NUL"}


def cargar(ruta: Path) -> list[dict[str, Any]]:
    """Lee y valida el fichero de acciones; devuelve la lista lista para usar."""
    ruta = ruta.expanduser()
    if not ruta.is_file():
        raise ConfigError(
            f"No encuentro «{ruta}». Crea acciones.json o usa --config RUTA."
        )

    try:
        texto = ruta.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConfigError(
            f"«{ruta.name}» no está guardado en UTF-8: {exc.reason}."
        ) from None
    except OSError as exc:
        raise ConfigError(f"No se puede leer «{ruta}»: {exc}") from None

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"«{ruta.name}» no es JSON válido: línea {exc.lineno}, "
            f"columna {exc.colno} ({exc.msg})."
        ) from None

    if not isinstance(datos, dict):
        raise ConfigError("La raíz de acciones.json debe ser un objeto JSON.")

    desconocidos = set(datos) - CAMPOS_RAIZ
    if desconocidos:
        raise ConfigError(
            "Campos desconocidos en la raíz de acciones.json: "
            f"{', '.join(sorted(desconocidos))}."
        )

    version = datos.get("version")
    if version is None:
        raise ConfigError("Falta el campo «version» en la raíz de acciones.json.")
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise ConfigError(
            f"La versión «{version}» del esquema no es compatible; se esperaba 1."
        )

    acciones = datos.get("acciones")
    if not isinstance(acciones, list) or not acciones:
        raise ConfigError("Falta la lista «acciones» o está vacía.")

    nombres: set[str] = set()
    for numero, accion in enumerate(acciones, start=1):
        if not isinstance(accion, dict):
            raise AccionNoValida(
                f"nº {numero}", "acción", "debe ser un objeto JSON con sus campos"
            )
        nombre = _nombre(accion, numero)
        _validar_campos(accion, nombre)
        if nombre in nombres:
            raise AccionNoValida(nombre, "nombre", "está repetido")
        nombres.add(nombre)
        _validar_filtro(accion, nombre)
        _validar_tipo(accion, nombre)

    return acciones


def _nombre(accion: dict[str, Any], numero: int) -> str:
    valor = accion.get("nombre")
    if not isinstance(valor, str) or not valor.strip():
        return f"nº {numero}"
    return valor


def _validar_campos(accion: dict[str, Any], nombre: str) -> None:
    desconocidos = set(accion) - CAMPOS_ACCION
    if desconocidos:
        raise AccionNoValida(
            nombre,
            "acción",
            f"campo desconocido: {', '.join(sorted(desconocidos))}",
        )

    for campo in CAMPOS_OBLIGATORIOS:
        valor = accion.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise AccionNoValida(nombre, campo, "es obligatorio y debe ser texto")

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", nombre):
        raise AccionNoValida(
            nombre,
            "nombre",
            "solo admite minúsculas, números y guiones (sin espacios)",
        )

    for campo in ("origen", "destino"):
        if campo in accion:
            valor = accion[campo]
            if not isinstance(valor, str) or not valor.strip():
                raise AccionNoValida(
                    nombre, campo, "debe ser una ruta de texto no vacía"
                )

    if "confirmar" in accion and not isinstance(accion["confirmar"], bool):
        raise AccionNoValida(nombre, "confirmar", "debe ser true o false")


def _validar_filtro(accion: dict[str, Any], nombre: str) -> None:
    filtro = accion.get("filtro", {})
    if not isinstance(filtro, dict):
        raise AccionNoValida(nombre, "filtro", "debe ser un objeto JSON")

    desconocidos = set(filtro) - CAMPOS_FILTRO
    if desconocidos:
        raise AccionNoValida(
            nombre,
            "filtro",
            f"campo desconocido: {', '.join(sorted(desconocidos))}",
        )

    if "extensiones" in filtro:
        extensiones = filtro["extensiones"]
        if not isinstance(extensiones, list) or not extensiones:
            raise AccionNoValida(
                nombre,
                "filtro.extensiones",
                "debe ser una lista no vacía, por ejemplo [\".pdf\"]",
            )
        for extension in extensiones:
            if (
                not isinstance(extension, str)
                or not extension.startswith(".")
                or len(extension) < 2
                or "/" in extension
                or "\\" in extension
            ):
                raise AccionNoValida(
                    nombre,
                    "filtro.extensiones",
                    f"«{extension}» no es una extensión válida (empieza por punto)",
                )

    if "patron" in filtro:
        patron = filtro["patron"]
        if not isinstance(patron, str) or not patron:
            raise AccionNoValida(
                nombre, "filtro.patron", "debe ser una expresión regular de texto"
            )
        try:
            re.compile(patron)
        except (re.error, OverflowError, RecursionError) as exc:
            raise AccionNoValida(
                nombre, "filtro.patron", f"expresión regular rota: {exc}"
            ) from None

    if "mas_antiguo_que_dias" in filtro:
        dias = filtro["mas_antiguo_que_dias"]
        if isinstance(dias, bool) or not isinstance(dias, int) or dias <= 0:
            raise AccionNoValida(
                nombre,
                "filtro.mas_antiguo_que_dias",
                "debe ser un número entero mayor que 0",
            )

    if "mayor_que_mb" in filtro:
        megas = filtro["mayor_que_mb"]
        if (
            isinstance(megas, bool)
            or not isinstance(megas, (int, float))
            or megas <= 0
            or not math.isfinite(float(megas))
        ):
            raise AccionNoValida(
                nombre,
                "filtro.mayor_que_mb",
                "debe ser un número mayor que 0",
            )


def _validar_tipo(accion: dict[str, Any], nombre: str) -> None:
    tipo = accion["tipo"]
    if tipo not in TIPOS:
        raise AccionNoValida(
            nombre,
            "tipo",
            f"«{tipo}» no existe; usa uno de: {', '.join(sorted(TIPOS))}",
        )

    for campo in CAMPOS_POR_TIPO.get(tipo, ()):
        valor = accion.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise AccionNoValida(
                nombre, campo, f"es obligatorio en acciones de tipo {tipo}"
            )

    if tipo == "renombrar":
        _validar_plantilla(accion["plantilla"], nombre)


def _validar_plantilla(plantilla: str, nombre: str) -> None:
    if "/" in plantilla or "\\" in plantilla:
        raise AccionNoValida(
            nombre,
            "plantilla",
            "no puede contener barras: el fichero se renombra en su misma carpeta",
        )

    try:
        for _, campo, _, _ in Formatter().parse(plantilla):
            if campo is not None and campo not in CAMPOS_PLANTILLA:
                raise AccionNoValida(
                    nombre,
                    "plantilla",
                    f"«{campo}» no es un hueco válido; usa "
                    "{fecha}, {n}, {ext} o {nombre}",
                )

        muestra = plantilla.format(
            fecha=datetime(2026, 10, 27, 12, 34, 56),
            n=1,
            ext=".jpg",
            nombre="IMG_2041",
        )
    except (ValueError, KeyError, IndexError, AttributeError) as exc:
        raise AccionNoValida(
            nombre, "plantilla", f"no se puede aplicar: {exc}"
        ) from None

    _validar_nombre_generado(muestra, nombre)


def _validar_nombre_generado(muestra: str, nombre: str) -> None:
    if not muestra or muestra in {".", ".."}:
        raise AccionNoValida(
            nombre, "plantilla", "genera un nombre de fichero vacío o inválido"
        )
    if any(caracter in CARACTERES_PROHIBIDOS for caracter in muestra):
        raise AccionNoValida(
            nombre,
            "plantilla",
            "genera un nombre con caracteres no válidos en Windows "
            '(/ \\ < > : " | ? *)',
        )
    if any(ord(caracter) < 32 for caracter in muestra):
        raise AccionNoValida(
            nombre, "plantilla", "genera un nombre con caracteres de control"
        )
    if muestra != muestra.rstrip(" ."):
        raise AccionNoValida(
            nombre, "plantilla", "genera un nombre que acaba en espacio o punto"
        )

    base = muestra.split(".", maxsplit=1)[0].upper()
    if base in NOMBRES_RESERVADOS or re.fullmatch(r"(?:COM|LPT)[1-9]", base):
        raise AccionNoValida(
            nombre, "plantilla", f"genera el nombre reservado «{base}» en Windows"
        )
