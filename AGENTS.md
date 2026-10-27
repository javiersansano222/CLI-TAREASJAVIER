# tareas · CLI de tareas con ficheros (proyecto de 1º DAM)

## Stack y órdenes

- Python 3.12 + Typer + Rich, gestionado con uv (src layout, paquete src/tareas).
- Ejecutar: `tareas` (menú interactivo) · Ayuda: `tareas --help` · Bienvenida: `hola` o `uv run tareas hola` · Validar config: `uv run tareas validar` · Capturas: `uv run tareas capturas --simular` · Informe: `uv run tareas informe` · Pruebas (semana 4): `uv run pytest`.

## Normas

- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que funcionar en Linux, Windows y macOS.
- Nunca ejecutes acciones sobre carpetas reales: solo en ~/pruebas-tareas y con --simular. Sobre ~/Baixades usa siempre `tareas capturas --simular`.
- Todas las órdenes de `tareas` y el ejecutable `hola` funcionan desde cualquier carpeta.
- No toques .env ni escribas claves en ningún fichero. No hagas git push ni commits: los hace el alumno.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.
