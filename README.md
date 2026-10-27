# tareas

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 27/10/2026)

1. **Problema:** cada semana pierdo tiempo ordenando Descargas y limpiando temporales antiguos a mano.
2. **Para quién:** para mí y para mis compañeros de clase.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes previstas:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** borrar temporales de más de 30 días, mover imágenes a `fotos/` y renombrar capturas por fecha.
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).

## Puesta en marcha

```bash
uv python install 3.12
uv sync
uv run tareas --help
uv tool install --editable .
```

## Estructura

```
cli-tareas/
├── pyproject.toml
├── uv.lock              (lo genera uv sync)
├── .python-version
├── .gitignore
├── .gitattributes
├── opencode.json        Permisos del agente
├── AGENTS.md            Normas del proyecto para el agente
├── README.md
├── docs/
│   └── prompts.md       Cuaderno de prompts
└── src/
    └── tareas/
        ├── __init__.py  Versión del paquete
        ├── __main__.py  python -m tareas
        └── cli.py       Órdenes version y listar
```
