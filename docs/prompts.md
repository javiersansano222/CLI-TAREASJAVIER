# Prompts clave del proyecto

## 2026-10-27 · Primera orden: listar

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.
La conexión con el servidor del centro funciona con la clave configurada en `CENTRO_IA_KEY` (fuera del repo).

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

## 2026-10-27 · Semana 2: acciones.json, validación y motor

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.

**Punto de partida:** el repo tenía la semana 1 cerrada y el borrador de las 3
acciones en el README. El prompt de trabajo fue:

> Continúa con la semana 2 del proyecto CLI tareas siguiendo la rúbrica.
> Lee el README, la sesión 2 y el estado actual del repo. Añade `acciones.json`
> con mis 3 acciones del borrador, `errores.py`, `config.py`, `acciones.py`,
> `motor.py` y las órdenes `validar`, `acciones` y `ejecutar` con `--simular`,
> `--si` y `--config`. Crea también la skill `acciones-json`, el comando
> `/nueva-accion`, el subagente `revisor` y el ADR-0001.
>
> Criterio de aceptación:
> - Validar TODO el JSON antes de tocar el disco, con mensajes que digan acción y campo.
> - Códigos 0/1/3 y ningún traceback ante errores previsibles.
> - Simulación sin `mkdir`, `move`, `rename` ni `unlink`.
> - Nunca sobrescribir: sufijo ` (1)`.
> - Probar solo en `~/pruebas-tareas`, primero con `--simular`.
> - No hacer commits ni push; los hago yo.

**Qué corregí del primer planteamiento:**

- El agente propuso validar solo los campos obligatorios; añadí validación de `version`, nombres únicos, formato del nombre, tipos de filtro, números finitos, `confirmar` booleano y huecos de plantilla.
- Rechacé que una acción pudiera renombrar con barras en la plantilla: podría salirse de la carpeta.
- Rechacé tratar `False` como entero en `version` o en los filtros numéricos.
- Añadí comprobación de que `extensiones` empiece por punto y de que no haya filtros desconocidos.
- Una revisión posterior detectó que un typo como `"filtros"` se ignoraba y podía hacer que un borrado viera todos los ficheros. Ahora se rechazan campos desconocidos en la raíz y en cada acción.
- La plantilla se prueba con un nombre de muestra: se rechazan formatos inválidos, fechas con `/` o `:`, nombres reservados de Windows y finales en punto o espacio.
- El JSON se lee con `utf-8-sig`; un fichero en Latin-1 da `ConfigError`, no un traceback.
- La regex y las fechas extremas capturan también `OverflowError`, `RecursionError`, `ValueError` y `OSError`.
- La confirmación de borrado solo aparece si la acción es destructiva, no se simula, no se pasa `--si` y `confirmar` no es `false`.
- Los errores se capturan por fichero: si uno falla, los demás terminan, se muestra su detalle y la orden sale con código 1.

**Pruebas manuales (en `~/pruebas-tareas/semana2`):**

- Simulación de las 3 acciones sin cambios en disco.
- Ejecución real de mover, renombrar y borrar sobre copias de prueba.
- Colisión de destino: `FOTO1 (1).JPG`.
- Nombres con tildes, eñes, espacios y extensión en mayúsculas.
- Repetición de mover y renombrar: no duplica ni renombra dos veces.
- Dos capturas con la misma fecha y una plantilla sin `{n}`: la simulación reserva `(1)` y coincide con la ejecución real.
- Un fichero que ocupa el destino de otro pero se renombra antes en el mismo lote: simulación y ejecución real coinciden.
- Un symlink roto en el destino no se sustituye; se usa ` (1)`.
- Borrar sin `--si` y responder que no: no borra y sale con código 1.
- Copiar un fichero sin permiso de lectura: el otro se copia, se muestra el error concreto y sale con código 1.
- JSON roto, tipo inexistente, nombre repetido, campo desconocido, regex inválida, regex desbordada, plantilla inválida, `destino` ausente, `NaN` y fichero inexistente: código 3 sin traceback.
- JSON Latin-1: código 3 con mensaje de encoding; JSON UTF-8 con BOM: se acepta.
- Acción o carpeta inexistente: código 1 sin traceback.

**Revisión antes de cerrar:** pedí una revisión independiente de solo lectura
con este criterio: buscar errores reales, casos feos, problemas multiplataforma
y comprobar que simulación y ejecución coinciden. La revisión encontró el typo
de `filtros`, plantillas con formatos no validados, el JSON no UTF-8, symlinks
rotos, los `NaN` y que un fallo a mitad de lote ocultaba lo ya hecho. Corregí
esos puntos y añadí pruebas específicas para cada uno.

**Qué aprendí:** validar todo antes de ejecutar evita errores a mitad de una
acción; rechazar campos desconocidos es una medida de seguridad, no un detalle
de estilo; `__init_subclass__` permite registrar cada tipo de acción sin cadenas
de `if/elif`; y `--simular` tiene que comprobar el disco para calcular destinos,
pero sin ejecutar ninguna escritura. También aprendí que un fallo por fichero no
debe ocultar lo que ya se ha hecho en los demás.

## 2026-10-27 · Orden capturas: papelera a las 5 horas

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.

**Prompt de referencia:**

> Añade una orden `capturas` que detecte las capturas de pantalla de la carpeta
> de descargas y envíe a la papelera las que tengan 5 horas o más. Debe
> funcionar en Linux, Windows y macOS, aceptar `--simular`, `--si`, `--horas` y
> `--carpeta`, y no tocar nunca carpetas reales durante las pruebas. Al terminar,
> añade los ficheros, haz commit y push.
>
> Criterio de aceptación:
> - Detecta `Screenshot`, `Screen Shot`, `Captura de pantalla` y `Capture d'écran`.
> - Solo imágenes y nunca enlaces simbólicos ni subcarpetas.
> - `--simular` no envía nada a la papelera.
> - La papelera es la del sistema, no un borrado definitivo.
> - La salida indica qué ficheros se han enviado y cuáles han fallado.

**Qué implementé:**

- `src/tareas/capturas.py` con detección de la carpeta de descargas vía XDG y
  nombres habituales del sistema.
- `send2trash` como dependencia para usar la papelera real de Linux, Windows y
  macOS.
- La orden `tareas capturas` con `--horas` (5 por defecto), `--simular`, `--si`
  y `--carpeta`.
- Confirmación antes de enviar capturas y salida con tabla y código 1 si algún
  fichero falla.
- Documentación en el README y actualización de `AGENTS.md`.

**Pruebas manuales (en `~/pruebas-tareas/semana3/capturas`):**

- Capturas con nombres de GNOME, macOS, Windows y español.
- Ficheros antiguos y recientes: solo se eligen los de 5 horas o más.
- Ficheros que no son capturas y enlaces simbólicos: se ignoran.
- `--simular`: no cambia nada.
- `--si`: envía una captura de prueba a la papelera.
- `--horas 1` y `--carpeta`: selección correcta.
- Carpeta inexistente y `--horas 0`: error sin traceback.

**Qué aprendí:** la carpeta de descargas no siempre se llama `Descargas`;
conviene leer XDG en Linux y tener alternativas para Windows/macOS. Enviar a la
papelera no es lo mismo que `unlink`, y `send2trash` permite hacerlo sin
depender de un comando del sistema. También aprendí a separar la simulación de
la ejecución real para poder probar sin riesgo.
