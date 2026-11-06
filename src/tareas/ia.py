"""Capa IA de «tareas» contra el servidor OpenAI-compatible del centro.

Lee CENTRO_IA_URL y CENTRO_IA_KEY del entorno en el momento de la llamada,
nunca de ficheros. Sin red o sin clave, lanza excepciones propias con
mensajes humanos: ninguna otra orden depende de este módulo.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .acciones import Resultado
from .config import cargar as cargar_config
from .errores import TareasError

MODELO = "Qwen38-DualSpark-low"
TIMEOUT_S = 45
MAX_FICHEROS = 25
MAX_CHARS = 4000
CANDIDATOS_CA = (
    Path.home() / ".config" / "opencode" / "ca-simarro.crt",
    Path.home() / ".certs" / "ca-simarro.crt",
)


class ErrorIA(TareasError):
    """La IA del centro no ha podido responder: mensaje humano, sin traceback."""

    codigo_salida = 1


class FaltaClaveIA(ErrorIA):
    """Falta CENTRO_IA_KEY o CENTRO_IA_URL en el entorno."""


class ErrorRedIA(ErrorIA):
    """El servidor del centro no responde o ha devuelto algo no válido."""


@dataclass(frozen=True)
class RespuestaIA:
    """Texto limpio que devuelve el modelo, más el modelo usado."""

    texto: str
    modelo: str


def _leer_env(clave: str) -> str:
    """Devuelve la variable de entorno o lanza FaltaClaveIA con mensaje claro."""
    valor = os.environ.get(clave, "").strip()
    if not valor:
        raise FaltaClaveIA(
            f"Falta la variable de entorno {clave}. Añádela a tu sesión "
            "(mira .env.example). Sin ella las órdenes con IA no funcionan; "
            "el resto de tareas sigue igual."
        )
    return valor


def _url_base() -> str:
    """Quita la parte /chat/completions si el alumno la puso en CENTRO_IA_URL."""
    base = _leer_env("CENTRO_IA_URL").rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    return base.rstrip("/")


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

    Usar CAISPACE=0 es solo para redes escolares con certificado auto-firmado:
    evita el error CERTIFICATE_VERIFY_FAILED sin bajar la verificación en
    cualquier otro sitio.
    """
    if not verificar:
        contexto = ssl._create_unverified_context()
        return contexto
    contexto = ssl.create_default_context()
    ca = _buscar_ca()
    if ca is not None:
        try:
            contexto.load_verify_locations(cafile=str(ca))
        except (OSError, ssl.SSLError):
            pass
    return contexto


def _post_chat(payload: dict[str, Any]) -> dict[str, Any]:
    """Envía la petición al centro y devuelve el JSON ya parseado.

    Si el equipo tiene certificado auto-firmado (CAISPACE=0) se reintentará
    sin verificación, pero solo con ese flag explícito.
    """
    url = _url_base() + "/chat/completions"
    datos = json.dumps(payload).encode("utf-8")
    peticion = urllib.request.Request(
        url,
        data=datos,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {_leer_env('CENTRO_IA_KEY')}",
        },
    )
    verificar = os.environ.get("IA_TLS_VERIFICAR", "").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    intentos = (True, False) if verificar else (False,)
    ultimo_error: Exception | None = None
    for verificar_en_intento in intentos:
        contexto = _contexto_ssl(verificar_en_intento)
        try:
            with urllib.request.urlopen(
                peticion, timeout=TIMEOUT_S, context=contexto
            ) as respuesta:
                cuerpo = respuesta.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise ErrorRedIA(
                f"El servidor del centro ha respondido {exc.code} {exc.reason}. "
                "Revisa CENTRO_IA_URL, CENTRO_IA_KEY o inténtalo más tarde."
            ) from None
        except ssl.SSLCertVerificationError as exc:
            ultimo_error = exc
            continue
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            ultimo_error = exc
            continue
        try:
            return json.loads(cuerpo)
        except json.JSONDecodeError as exc:
            raise ErrorRedIA(
                f"El centro ha devuelto algo que no es JSON: {exc.msg}."
            ) from None

    if isinstance(ultimo_error, ssl.SSLCertVerificationError):
        raise ErrorRedIA(
            "El servidor del centro usa un certificado auto-firmado. Añade su CA "
            "a tu almacén de sistemas, guarda ca-simarro.crt en "
            f"{CANDIDATOS_CA[0]} o usa IA_TLS_VERIFICAR=0 (solo en la red del "
            "instituto, nunca fuera)."
        ) from None
    raise ErrorRedIA(
        "No hay conexión con el servidor del centro. "
        "Las órdenes sin IA siguen funcionando igual."
    ) from None


def hablar(prompt: str, max_tokens: int = 600) -> RespuestaIA:
    """Pregunta al modelo del centro y devuelve su texto limpio."""
    cuerpo = _post_chat(
        {
            "model": MODELO,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres el asistente de una CLI escolar de tareas con "
                        "ficheros. Respondes en español claro y breve."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
    )
    try:
        mensaje = cuerpo["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ErrorRedIA(
            "El centro ha contestado sin el campo esperado; "
            "inténtalo otra vez en unos minutos."
        ) from None
    texto = (mensaje or "").strip()
    if not texto:
        raise ErrorRedIA("El centro ha contestado vacío; inténtalo otra vez.")
    return RespuestaIA(texto=texto, modelo=MODELO)


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
