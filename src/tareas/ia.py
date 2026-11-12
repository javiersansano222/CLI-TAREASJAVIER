"""Capa IA de «tareas» contra el servidor OpenAI-compatible del centro.

Todo pasa por la interfaz ProveedorIA: le das texto y te devuelve texto.
ProveedorCentro habla con httpx usando CENTRO_IA_URL y CENTRO_IA_KEY, que
lee del entorno (cargando antes el .env de la carpeta si existe); la clave
nunca se imprime ni se escribe en ningún fichero. Sin clave o sin red lanza
IANoDisponible (salida 4): ninguna otra orden depende de este módulo.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import find_dotenv, load_dotenv

from .acciones import Resultado
from .config import cargar as cargar_config
from .errores import IANoDisponible, TareasError

MODELO = "Qwen38-DualSpark-low"
TIMEOUT_S = 45
MAX_FICHEROS = 25
MAX_CHARS = 4000
CANDIDATOS_CA = (
    Path.home() / ".config" / "opencode" / "ca-simarro.crt",
    Path.home() / ".certs" / "ca-simarro.crt",
)

SISTEMA_GENERICO = (
    "Eres el asistente de una CLI escolar de tareas con ficheros. "
    "Respondes en español claro y breve."
)

MENSAJE_CONEXION = (
    "No hay conexión con el servidor del centro. "
    "Las órdenes sin IA siguen funcionando igual."
)
MENSAJE_CERTIFICADO = (
    "El servidor del centro usa un certificado auto-firmado. Añade su CA "
    "a tu almacén de sistemas, guarda ca-simarro.crt en "
    f"{CANDIDATOS_CA[0]} o usa IA_TLS_VERIFICAR=0 (solo en la red del "
    "instituto, nunca fuera)."
)


class IANoDisponible(TareasError):
    """Sin clave, sin red o el servidor de IA no responde: las órdenes sin IA siguen."""

    codigo_salida = 4


class FaltaClaveIA(IANoDisponible):
    """Falta CENTRO_IA_KEY o CENTRO_IA_URL en el entorno."""


class ErrorRedIA(IANoDisponible):
    """El servidor del centro no responde o ha devuelto algo no válido."""


class ErrorIA(TareasError):
    """La IA respondió, pero su respuesta no sirve: mensaje humano, sin traceback."""

    codigo_salida = 1


@dataclass(frozen=True)
class RespuestaIA:
    """Texto limpio que devuelve el modelo, con su coste."""

    texto: str
    modelo: str
    tokens_entrada: int = 0
    tokens_salida: int = 0
    segundos: float = 0.0

    def resumen(self) -> str:
        """Lo que gastó esta llamada, para la columna Detalle de las tablas."""
        return f"{self.tokens_entrada}+{self.tokens_salida} tokens · {self.segundos:.1f} s"


class ProveedorIA(ABC):
    """Lo único que el resto del programa sabe de la IA: le das texto y te devuelve texto."""

    @abstractmethod
    def completar(
        self, sistema: str, usuario: str, max_tokens: int = 600
    ) -> RespuestaIA:
        ...


class ProveedorCentro(ProveedorIA):
    """Un servidor compatible con la API de OpenAI: el del centro (o cualquier otro)."""

    def __init__(
        self,
        url: str,
        clave: str,
        modelo: str = MODELO,
        verificar: bool = True,
    ) -> None:
        url = url.rstrip("/")
        if url.endswith("/chat/completions"):
            url = url[: -len("/chat/completions")]
        self.url = url.rstrip("/")
        self.modelo = modelo
        self._clave = clave  # «_»: privada; nunca se imprime ni se muestra
        self._verificar = verificar

    @staticmethod
    def desde_entorno() -> ProveedorCentro:
        """Fábrica: carga el .env si lo hay y arma el proveedor con lo que encuentre."""
        cargar_dotenv()
        url = os.environ.get("CENTRO_IA_URL", "").strip()
        clave = os.environ.get("CENTRO_IA_KEY", "").strip()
        faltan = [
            nombre
            for nombre, valor in (
                ("CENTRO_IA_URL", url),
                ("CENTRO_IA_KEY", clave),
            )
            if not valor
        ]
        if faltan:
            raise FaltaClaveIA(
                f"Falta {', '.join(faltan)}: añádela a tu sesión o al .env "
                "(mira .env.example). Sin ellas las órdenes con IA no "
                "funcionan; el resto de tareas sigue igual."
            )
        return ProveedorCentro(url, clave, MODELO, _verificacion_activa())

    def completar(
        self, sistema: str, usuario: str, max_tokens: int = 600
    ) -> RespuestaIA:
        """Pide al modelo una completación y devuelve su texto ya limpio."""
        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        inicio = time.perf_counter()
        cuerpo = self._post_chat(payload)
        try:
            mensaje = cuerpo["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ErrorRedIA(
                "El centro ha contestado sin el campo esperado; "
                "inténtalo otra vez en unos minutos."
            ) from None
        texto = (mensaje or "").strip()
        if not texto:
            raise ErrorRedIA("El centro ha contestado vacío; inténtalo otra vez.")
        uso = cuerpo.get("usage") or {}
        return RespuestaIA(
            texto=texto,
            modelo=self.modelo,
            tokens_entrada=int(uso.get("prompt_tokens", 0) or 0),
            tokens_salida=int(uso.get("completion_tokens", 0) or 0),
            segundos=time.perf_counter() - inicio,
        )

    def _post_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Envía la petición al centro y devuelve el JSON ya parseado.

        Si el equipo tiene certificado auto-firmado se reintenta una vez sin
        verificar, solo cuando el fallo pinta a certificado. Cada fallo se
        convierte en un mensaje humano: nunca hay traceback ni clave a la vista.
        """

        def enviar(verificar: bool) -> httpx.Response:
            return httpx.post(
                f"{self.url}/chat/completions",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._clave}",
                },
                timeout=httpx.Timeout(TIMEOUT_S, connect=10),
                verify=_contexto_ssl(verificar),
            )

        intentos = (True, False) if self._verificar else (False,)
        for posicion, verificar in enumerate(intentos):
            try:
                respuesta = enviar(verificar)
                respuesta.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise _error_http(exc) from None
            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                ssl.SSLCertVerificationError,
            ) as exc:
                if verificar and posicion == 0:
                    continue  # se reintenta una vez sin verificar
                if _es_certificado(exc):
                    raise ErrorRedIA(MENSAJE_CERTIFICADO) from None
                raise ErrorRedIA(MENSAJE_CONEXION) from None
            except httpx.TimeoutException:
                raise ErrorRedIA(
                    f"El servidor de IA no ha respondido a tiempo ({TIMEOUT_S} s)."
                ) from None
            try:
                return respuesta.json()
            except json.JSONDecodeError as exc:
                raise ErrorRedIA(
                    f"El centro ha devuelto algo que no es JSON: {exc.msg}."
                ) from None
        raise ErrorRedIA(MENSAJE_CONEXION) from None


def cargar_dotenv() -> None:
    """Carga el .env de la carpeta desde la que se lanza la orden, si existe.

    Busca hacia arriba desde la carpeta actual; lo que ya esté exportado en la
    terminal manda, el fichero no lo pisa. Sin .env no pasa nada: se siguen
    leyendo las variables de entorno de siempre.
    """
    ruta = find_dotenv(usecwd=True)
    if ruta:
        load_dotenv(ruta)


def _verificacion_activa() -> bool:
    """IA_TLS_VERIFICAR=0 es solo para redes escolares con CA propia."""
    return os.environ.get("IA_TLS_VERIFICAR", "").strip().lower() not in {
        "0",
        "false",
        "no",
    }


def _buscar_ca() -> Path | None:
    """Devuelve la CA del centro si existe en alguna ruta habitual del equipo."""
    for ruta in CANDIDATOS_CA:
        try:
            if ruta.is_file():
                return ruta
        except OSError:
            continue
    return None


def _contexto_ssl(verificar: bool) -> ssl.SSLContext:
    """Contexto TLS normal, con la CA del centro si la pilla, o sin verificación.

    Usar IA_TLS_VERIFICAR=0 es solo para redes escolares con certificado
    auto-firmado: evita CERTIFICATE_VERIFY_FAILED sin bajar la verificación
    en cualquier otro sitio.
    """
    if not verificar:
        return ssl._create_unverified_context()
    contexto = ssl.create_default_context()
    ca = _buscar_ca()
    if ca is not None:
        try:
            contexto.load_verify_locations(cafile=str(ca))
        except (OSError, ssl.SSLError):
            pass
    return contexto


def _es_certificado(exc: BaseException) -> bool:
    """¿Este fallo de red huele a certificado? Mira la cadena de causas."""
    actual: BaseException | None = exc
    while actual is not None:
        if isinstance(actual, ssl.SSLCertVerificationError):
            return True
        if "CERTIFICATE" in str(actual).upper():
            return True
        actual = actual.__cause__ or actual.__context__
    return False


def _error_http(exc: httpx.HTTPStatusError) -> ErrorRedIA:
    """Un error HTTP con su motivo en español; la clave jamás aparece."""
    codigo = exc.response.status_code
    motivos = {
        401: "la clave no es válida (revisa CENTRO_IA_KEY)",
        429: "demasiadas peticiones, espera un minuto",
    }
    motivo = motivos.get(codigo)
    if motivo:
        return ErrorRedIA(f"El servidor de IA responde {codigo}: {motivo}.")
    return ErrorRedIA(
        f"El servidor del centro ha respondido {codigo}. "
        "Revisa CENTRO_IA_URL, CENTRO_IA_KEY o inténtalo más tarde."
    )


def hablar(prompt: str, max_tokens: int = 600) -> RespuestaIA:
    """Pregunta al modelo del centro y devuelve su respuesta ya limpia."""
    proveedor = ProveedorCentro.desde_entorno()
    return proveedor.completar(SISTEMA_GENERICO, prompt, max_tokens)


def _extraer_json(texto: str) -> str:
    """Devuelve el primer objeto JSON del texto, con o sin bloque ```json."""
    bloque = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if bloque:
        return bloque.group(1)
    principio, final = texto.find("{"), texto.rfind("}")
    if 0 <= principio < final:
        return texto[principio : final + 1]
    raise ErrorIA(
        "La IA no ha devuelto un JSON de acción; inténtalo con una "
        "descripción más concreta."
    )


def _validar_propuesta(accion: dict[str, Any]) -> None:
    """Valida la acción propuesta con el validador real, sin escribir en disco."""
    prueba = {"version": 1, "acciones": [accion]}
    with tempfile.TemporaryDirectory(prefix="tareas-ia-") as tmp:
        ruta = Path(tmp) / "prueba.json"
        ruta.write_text(
            json.dumps(prueba, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        try:
            cargar_config(ruta)
        except TareasError as exc:
            raise ErrorIA(
                f"La propuesta de la IA no supera la validación de tareas: {exc}"
            ) from None


def sugerir_accion(descripcion: str) -> dict[str, Any]:
    """Convierte una descripción en una acción válida para acciones.json."""
    prompt = f"""Genera UNA acción para la CLI «tareas» (escolar, 1º DAM).

Descripción del usuario: {descripcion}

Esquema estricto (sin campos extra, sin inventar):
{{
  "nombre": "solo-minúsculas-números-y-guiones",
  "descripcion": "frase corta en español",
  "tipo": "mover" | "copiar" | "renombrar" | "borrar" | "mirar_espacio",
  "origen": "~/Carpeta (opcional)",
  "filtro": {{"extensiones": [".jpg"], "patron": "regex", "mas_antiguo_que_dias": 30, "mayor_que_mb": 100}},
  "destino": "~/Carpeta (obligatoria en mover y copiar)",
  "plantilla": "obligatoria en renombrar, huecos {{fecha:%Y-%m-%d}} {{n:03}} {{ext}} {{nombre}}",
  "confirmar": true o false (opcional)
}}
Un tipo renombrar necesita "plantilla" sin barras. Un tipo borrar usa
"confirmar": true. "origen" y "destino" empiezan por ~/, nunca rutas concretas.

Responde SOLO con el objeto JSON, sin texto alrededor.
"""
    respuesta = hablar(prompt, max_tokens=500)
    accion = json.loads(_extraer_json(respuesta.texto))
    if not isinstance(accion, dict):
        raise ErrorIA("La IA ha devuelto algo que no es una acción de objeto JSON.")
    _validar_propuesta(accion)
    return accion


def explicar_simulacion(nombre: str, resultados: list[Resultado]) -> str:
    """Pide a la IA que explique en cristiano el resultado de una simulación."""
    lineas = []
    for resultado in resultados[:MAX_FICHEROS]:
        destino = f" → {resultado.destino}" if resultado.destino else ""
        origen = f"{resultado.origen}" + (
            "" if resultado.origen.suffix else "(sin extensión)"
        )
        lineas.append(f"{resultado.estado}: {origen}{destino}")
    if len(resultados) > MAX_FICHEROS:
        lineas.append(f"… y {len(resultados) - MAX_FICHEROS} ficheros más.")
    detalle = "\n".join(lineas)[:MAX_CHARS]
    prompt = f"""La acción «{nombre}» se ha SIMULADO (no se ha tocado nada) y ha
dado estos resultados:

{detalle}

Explícalo en 2-4 frases para alguien de 1º de DAM: qué pasaría si se ejecutara
de verdad y algo a lo que prestar atención. Nada de generalidades. Los nombres
terminados en .png u otra extensión SÍ conservan su tipo; no inventes problemas
que no se ven en la lista.
"""
    return hablar(prompt).texto
