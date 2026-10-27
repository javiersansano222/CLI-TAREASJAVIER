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

## 2026-10-27 · Orden informe: resumen de descargas

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.

**Prompt de referencia:**

> Añade una orden `informe` que muestre un resumen de solo lectura de la carpeta
> de descargas: número de ficheros y carpetas, tamaño total, tipos, capturas
> pendientes y los ficheros más antiguos y más grandes. Debe aceptar `--carpeta`,
> `--top` y `--horas`, funcionar en Linux, Windows y macOS y no modificar nada.
>
> Criterio de aceptación:
> - Usa la misma detección de capturas que `tareas capturas`.
> - Ignora enlaces simbólicos y no entra en subcarpetas.
> - Las tablas se limitan con `--top` y no fallan con una carpeta vacía.
> - Ruta inexistente: código 1 sin traceback.
> - `--top 0` o `--horas 0`: error de uso con código 2.

**Qué implementé:**

- `src/tareas/informe.py` con un resumen inmutable de ficheros, tipos y capturas.
- La orden `tareas informe` con `--carpeta`, `--top` y `--horas`.
- Reutilización de `es_captura()` de `capturas.py` para no duplicar patrones.
- Tablas Rich para tipos, ficheros más antiguos y ficheros más grandes.
- Documentación en el README y actualización de `AGENTS.md`.

**Pruebas manuales (en `~/pruebas-tareas/semana3/capturas`):**

- Recuento de ficheros, carpetas y tamaño total.
- Agrupación por extensión y capturas totales/pendientes.
- Ficheros más antiguos y más grandes con `--top`.
- Enlaces simbólicos y subcarpetas ignorados.
- Carpeta vacía, ruta inexistente y valores cero de `--top`/`--horas`.
- Comprobado que no se modifica ningún fichero.

**Qué aprendí:** un informe es más útil si separa datos globales de listas
cortas; conviene reutilizar la detección de capturas para que el informe y la
limpieza no discrepen. También aprendí que hasta una orden de solo lectura debe
controlar rutas inexistentes, enlaces y fechas raras para no romper la salida.

## 2026-10-27 · Bienvenida `hola` con banner ASCII

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.

**Prompt de referencia:**

> Añade una orden `hola` que muestre un banner ASCII generado por la propia
> terminal y el mensaje «Bienvenido a mi terminal personalizado», parecido al
> arranque de OpenCode. Quiero poder ejecutarlo como `tareas hola` y también
> como `hola` directamente.
>
> Criterio de aceptación:
> - Banner legible en una terminal normal.
> - Mensaje centrado y en español.
> - Sin dependencias nuevas.
> - Sin tocar `acciones.json` ni ningún fichero.

**Qué implementé:**

- `src/tareas/bienvenida.py` con el banner y un `main()` para el ejecutable.
- La orden `tareas hola`.
- El script `hola` en `pyproject.toml`, instalado con el resto de la herramienta.
- Documentación en el README y actualización de `AGENTS.md`.

**Pruebas manuales:**

- `uv run tareas hola`.
- `hola` tras reinstalar con `uv tool install --editable .`.
- `tareas --help` muestra la orden.
- Comprobado que no lee ni modifica `acciones.json`.

**Qué aprendí:** un entry point de `pyproject.toml` permite crear un comando
corto (`hola`) que reutiliza el mismo código que la CLI principal sin duplicar
la lógica.

## 2026-10-27 · Restringir `hola` e `informe` al proyecto

**Herramienta:** OpenCode 1.18.35 · modelo configurado: `simarro/Qwen38-DualSpark-medium`.

**Prompt de referencia:**

> Quiero que `hola` y la orden anterior, `informe`, solo se ejecuten dentro de
> la carpeta del proyecto `cli-tareas`, nunca desde fuera. Debe seguir
> funcionando desde cualquier subcarpeta del proyecto.
>
> Criterio de aceptación:
> - `hola` y `tareas hola` funcionan en la raíz y en `src/`.
> - Desde `/tmp` muestran un error claro y código 1.
> - `tareas informe` se comporta igual.
> - En una segunda petición se amplió la restricción a todo el CLI (ver el
>   apartado siguiente).

**Qué implementé:**

- `src/tareas/proyecto.py`, que busca hacia arriba un `pyproject.toml` con
  `name = "tareas"` y una carpeta `src/tareas`.
- La guarda en `hola`, en el ejecutable directo `hola` y en `informe`.
- Documentación en el README y una norma nueva en `AGENTS.md`.
- Después se movió la guarda al callback global para cubrir todo el CLI.

**Pruebas manuales:**

- `hola`, `tareas hola` e `informe` funcionan desde la raíz.
- `tareas hola` funciona desde `src/`.
- Desde `/tmp`, las tres variantes fallan con código 1.
- `tareas --help` sigue funcionando desde cualquier carpeta.

**Qué aprendí:** buscar un marcador del proyecto hacia arriba es más portable
que hardcodear `/home/.../cli-tareas`, y permite que la restricción funcione
también en subcarpetas.

## 2026-10-27 · Restringir todo el CLI al proyecto (retirado después)

> **Nota:** esta restricción se retiró en la petición siguiente; ver el último
> apartado.

**Prompt de referencia:**

> Perdona, quiero que todo eso, lo de `hola`, las descargas y lo del peso de las
> imágenes, funcione cuando entre dentro de `tareas`, y los próximos que haga
> también ahí dentro.

**Interpretación:** las funciones son `hola`, `capturas` (descargas) e `informe`
(tamaños y tipos de fichero). La restricción debía ampliarse de dos órdenes a
todo el CLI y a las órdenes futuras.

**Qué implementé:**

- Moví la comprobación al callback global `principal`: cualquier subcomando se
  valida antes de ejecutarse, sin repetir la guarda en cada orden.
- `tareas --help` y `tareas` sin argumentos siguen mostrando la ayuda desde
  cualquier carpeta.
- El ejecutable directo `hola` conserva su propia guarda.
- Las órdenes futuras heredan la restricción automáticamente.

**Pruebas manuales:**

- Dentro de la raíz y de `src/` funcionan `version`, `hola`, `capturas`,
  `informe`, `validar`, `acciones` y `ejecutar`.
- Desde `/tmp` todas esas órdenes fallan con código 1 y un mensaje claro.
- `hola` directo también falla desde `/tmp`.
- `tareas --help` y `tareas` sin argumentos siguen funcionando desde `/tmp`.

**Qué aprendí:** una guarda en el callback de Typer es más segura que repetirla
en cada comando, porque también protege las órdenes que se añadan más adelante.

## 2026-10-27 · Quitar la restricción y usar `tareas` desde cualquier carpeta

**Prompt de referencia:**

> Al ejecutar `tareas` desde mi home veo la ayuda, pero luego `hola` me dice que
> solo funciona dentro de la carpeta del proyecto. Creo que no funciona.

**Interpretación:** el usuario quiere las órdenes dentro de `tareas`, pero sin
tener que cambiar de carpeta. La restricción de directorio no era lo que
buscaba.

**Qué implementé:**

- Retiré la comprobación del callback global de Typer.
- Retiré la guarda del ejecutable directo `hola`.
- Mantuve `hola` y `tareas hola` como dos formas de ver la bienvenida.
- Dejé `capturas`, `informe` y el resto de órdenes disponibles desde cualquier
  carpeta.

**Pruebas manuales:**

- Desde `/tmp` funcionan `tareas hola`, `tareas capturas --simular`,
  `tareas informe`, `tareas version` y `tareas --help`.
- El ejecutable directo `hola` vuelve a funcionar desde cualquier carpeta.
- `tareas --help` sigue mostrando la ayuda.

**Qué aprendí:** para este proyecto es más cómodo que la restricción sea una
decisión de uso y no una comprobación de directorio; si más adelante se quiere
limitar, conviene hacerlo con un modo explícito y no con una guarda global.

## 2026-10-27 · Menú interactivo al ejecutar `tareas`

**Prompt de referencia:**

> Pero quiero que funcionen todos esos comandos cuando entre dentro de `tareas`,
> cuando ponga el comando `tareas` en la terminal.

**Interpretación:** al escribir `tareas` sin argumentos debe abrirse una
sesión interactiva con todas las órdenes, no mostrar solo la ayuda.

**Qué implementé:**

- `src/tareas/menu.py`, con un menú Rich que lista las órdenes registradas en
  Typer y lee una línea de la terminal.
- El callback principal abre el menú cuando no hay subcomando.
- El menú ejecuta la orden introducida reutilizando el propio `app` de Typer,
  así que acepta las mismas opciones que la terminal.
- `tareas --help` sigue mostrando la ayuda.
- Las órdenes nuevas aparecen en el menú automáticamente porque se leen de
  `app.registered_commands`.
- `salir`, `exit`, `quit` y `q` cierran el menú; `ayuda`, `help` y `?` muestran
  la ayuda; también se acepta el prefijo `tareas`.

**Pruebas manuales:**

- `printf 'version\nhola\nsalir\n' | tareas`: muestra versión y bienvenida.
- `capturas --simular` e `informe --top 1` funcionan dentro del menú.
- `tareas version` dentro del menú ejecuta `version`.
- Una orden inexistente muestra el error y el menú sigue abierto.
- Sin entrada (`</dev/null`) el menú termina sin quedarse colgado.
- `tareas --help` y `tareas hola` siguen funcionando fuera del menú.

**Qué aprendí:** reutilizar el `app` de Typer dentro del bucle evita duplicar
la lista de opciones y hace que las órdenes futuras funcionen sin tocar el
menú.
