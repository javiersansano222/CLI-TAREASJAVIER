# Prompts clave del proyecto

## 2026-10-27 · Primera orden: listar

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.
La conexión con el servidor del centro falló porque la clave actual no empieza por `sk-`; queda pendiente de corregir.

**Prompt de referencia (agente plan):**

> Lee @README.md y @pyproject.toml. Quiero `src/tareas/cli.py` (app de Typer llamada `app`) y `src/tareas/__main__.py` con dos órdenes: `version` y `listar [CARPETA]`.
> No escribas código todavía: dime qué ficheros crearías, qué funciones tendría cada uno y cómo tratarías la carpeta inexistente, la vacía, los nombres con corchetes y los ficheros que no se pueden leer.
>
> Criterio de aceptación:
> - `uv run tareas` sin argumentos muestra la ayuda, en español y sin autocompletado.
> - `version` imprime «tareas 0.1.0» leyendo `__version__` del paquete.
> - `listar` (por defecto la carpeta actual, acepta `~`) pinta una tabla Rich: Nombre, Tipo (extensión o «carpeta»), Tamaño legible, Modificado (AAAA-MM-DD HH:MM). Carpetas primero, luego alfabético sin distinguir mayúsculas.
> - Carpeta inexistente o que no es carpeta: mensaje en stderr, sin traza, código 1. Carpeta vacía: aviso en vez de tabla vacía.
> - `pathlib`, sin `os.system` ni `subprocess`, sin dependencias nuevas. `uv run python -m tareas` también funciona.

**Qué corregí del plan:**

- Escapé los nombres con `rich.markup.escape` para que `[borrador].pdf` salga entero.
- Salté los ficheros con enlace roto, sin permisos o con fecha no representable.
- Controlé también el error al iterar una carpeta sin permisos, devolviendo código 1 sin traza.
- No añadí dependencias nuevas: Typer ya trae Rich.

**Diffs que rechacé o deshice (/undo) y por qué:** ninguno; no se añadieron dependencias ni se tocaron ficheros fuera de `src/tareas/`.

**Funcionaba a la primera:** sí, tras `uv sync`. Probé ayuda, versión, carpeta actual, carpeta con espacios, carpeta vacía, ruta inexistente, fichero en vez de carpeta, corchetes y `python -m tareas`.

**Qué aprendí:** `typer.Exit(code=1)` termina con código 1 sin traza; `expanduser()` es necesario cuando la `~` llega entre comillas; y `escape()` evita que Rich interprete corchetes como marcado.
