# tareas

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 27/10/2026)

1. **Problema:** cada semana pierdo tiempo ordenando Descargas, limpiando temporales antiguos y poniendo nombre a las capturas a mano.
2. **Para quién:** para mí y para mis compañeros de clase.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes:** `--help`, `version`, `hola`, `cambio`, `listar`, `capturas`, `informe`, `imagenes`, `acciones`, `validar` y `ejecutar`.
5. **Mis 3 acciones:** limpiar temporales de más de 30 días, mover imágenes a `~/Imágenes/Fotos` y renombrar capturas por fecha.
6. **Nunca hará:** borrar sin pedir confirmación (salvo `--si`) ni tocar ficheros fuera del origen y destino configurados.
7. **Plataformas:** Linux primero; también Windows y macOS.
8. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
9. **Seguridad:** toda acción, `capturas` e `imagenes` se pueden simular con `--simular`; nunca se sobrescribe un fichero ni un enlace existente y las imágenes siempre se guardan como copias.
10. **Instalación:** `uv tool install --editable .` (se completa en la semana 4).

## Puesta en marcha

```bash
git clone https://github.com/javiersansano222/CLI-TAREASJAVIER.git
cd CLI-TAREASJAVIER
uv python install 3.12
uv sync
uv run tareas --help
uv tool install --editable .
uv tool update-shell   # si «tareas» no aparece en el PATH
# abre una terminal nueva y comprueba:
tareas --help
```

Para instalarla directamente desde GitHub:

```bash
uv tool install git+https://github.com/javiersansano222/CLI-TAREASJAVIER
uv tool update-shell   # si «tareas» no aparece en el PATH
```

## Uso rápido

```bash
tareas                  # abre el menú interactivo
tareas --help           # ayuda general
tareas cambio           # abre el menú en rojo

hola
tareas hola

tareas capturas --simular
tareas capturas
tareas capturas --carpeta ~/pruebas-tareas/capturas --horas 5

tareas informe
tareas informe --carpeta ~/pruebas-tareas/capturas --top 3

tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --simular
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --si

tareas validar
tareas acciones
tareas ejecutar limpiar-temporales --simular
tareas ejecutar mover-imagenes --simular
tareas ejecutar renombrar-capturas --simular

# Solo cuando la simulación sea la esperada:
tareas ejecutar limpiar-temporales
tareas ejecutar limpiar-temporales --si

# Otro fichero de acciones:
tareas --config ~/pruebas-tareas/acciones.json acciones
```

Todas las órdenes funcionan desde cualquier carpeta. `--config` es una opción
global y va **antes** de la orden. Por defecto se lee `./acciones.json`, en la
carpeta desde la que se lanza la orden.

## Menú interactivo

Al escribir `tareas` sin argumentos se abre un menú con todas las órdenes
disponibles. Desde ahí se escribe la orden igual que en la terminal:

```text
tareas> version
tareas> hola
tareas> cambio
tareas> capturas --simular
tareas> informe --top 3
tareas> imagenes --comprimir --simular
tareas> salir
```

También se pueden usar `ayuda` o `?` para ver la ayuda, y `salir`, `exit`,
`quit` o `q` para terminar. El menú lee las órdenes registradas en Typer, así
que las que se añadan en el futuro aparecen automáticamente.

## Cambiar el color del menú

Dentro del menú, `cambio` pone el panel, las tablas y el prompt `tareas>` en
rojo. `cambio normal` vuelve al color habitual:

```text
tareas> cambio
tareas> cambio normal
```

También admite `azul`, `verde` y `amarillo`. Desde fuera se puede abrir el
menú directamente con el color elegido:

```bash
tareas cambio
tareas cambio azul
```

El cambio afecta al menú de esa sesión, no al tema ni al fondo de la ventana de
la terminal.

## Bienvenida personalizada

La orden `hola` pinta un banner ASCII y el mensaje de bienvenida. Se puede usar
dentro de la CLI o directamente como ejecutable:

```bash
tareas hola
hola
```

No necesita `acciones.json` ni toca ningún fichero. Funciona desde cualquier
carpeta, igual que el resto de órdenes.

## Capturas de pantalla

`tareas capturas` busca capturas en la carpeta de descargas del sistema y envía
a la papelera las que llevan **5 horas o más** sin modificarse. En este equipo
la carpeta de descargas es `~/Baixades`; también reconoce `~/Descargas`,
`~/Downloads` y la ruta configurada en XDG.

Detecta los nombres habituales de captura (`Screenshot`, `Screen Shot`,
`Captura de pantalla`, `Capture d'écran`…) con extensión `.png`, `.jpg`,
`.jpeg`, `.webp` o `.bmp`.

```bash
tareas capturas --simular                 # ver qué haría, sin tocar nada
tareas capturas                           # pide confirmación y usa la papelera
tareas capturas --si                      # sin confirmación
tareas capturas --horas 8                 # cambiar la antigüedad mínima
tareas capturas --carpeta ~/pruebas-tareas/capturas
```

No borra definitivamente: usa la papelera del sistema mediante `send2trash`.
La orden nunca toca subcarpetas ni enlaces simbólicos.

## Informe de descargas

`tareas informe` muestra un resumen de solo lectura de la carpeta de descargas:
número de ficheros y carpetas, tamaño total, tipos de fichero, capturas
pendientes de limpiar y los ficheros más antiguos y más grandes.

```bash
tareas informe
tareas informe --top 10
tareas informe --carpeta ~/pruebas-tareas/capturas
tareas informe --horas 8
```

No mueve, renombra ni borra nada. Solo cuenta el primer nivel de la carpeta e
ignora enlaces simbólicos. `--top` limita las filas de cada tabla y `--horas`
cambia la antigüedad con la que se cuentan las capturas pendientes.

## Comprimir imágenes

`tareas imagenes` lista las imágenes JPEG, PNG y WebP del primer nivel de una
carpeta (por defecto, la de descargas). Con `--comprimir` crea copias más
ligeras en `comprimidas` sin modificar ni borrar los originales.

```bash
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --simular
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --si
tareas imagenes --comprimir --calidad 80 --destino ~/pruebas-tareas/comprimidas
```

`--calidad` va de 1 a 95 y se aplica a JPEG y WebP; PNG se guarda con
compresión sin pérdida. Si una copia no reduce el tamaño, se descarta y la
imagen aparece como «saltada». Si el nombre ya existe en el destino, se usa
` (1)`, ` (2)`… y nunca se sobrescribe nada. Los enlaces simbólicos, las
subcarpetas y las imágenes animadas se ignoran o se marcan como no
compatibles.

`--simular` enseña qué se haría sin crear la carpeta de destino ni escribir
ficheros. Sin `--si`, la compresión real pide confirmación. Usa Pillow para
leer y guardar las imágenes.

## Esquema de acciones.json

La raíz contiene dos campos:

| Campo | Obligatorio | Tipo | Qué hace |
| --- | --- | --- | --- |
| `version` | sí | entero `1` | Versión del esquema. |
| `acciones` | sí | lista no vacía | Acciones que puede ejecutar la herramienta. |

Cada acción tiene estos campos:

| Campo | Obligatorio | Tipo | Qué hace |
| --- | --- | --- | --- |
| `nombre` | sí | texto | Identificador único: minúsculas, números y guiones. |
| `descripcion` | sí | texto | Frase que aparece en `tareas acciones`. |
| `tipo` | sí | texto | `mover`, `copiar`, `renombrar` o `borrar`. |
| `origen` | no | ruta | Carpeta por defecto si no se pasa `CARPETA`. Admite `~`. |
| `filtro` | no | objeto | Limita qué ficheros se tocan. Sin filtro se seleccionan todos. |
| `destino` | mover/copiar | ruta | Carpeta de destino. Se crea si no existe. |
| `plantilla` | renombrar | texto | Nombre nuevo con huecos `{fecha}`, `{n}`, `{ext}` y `{nombre}`. |
| `confirmar` | no | booleano | Pide confirmación antes de borrar. Por defecto, `true`; si se pone `false`, no pregunta. |

Dentro de `filtro` se pueden combinar estas opciones; si hay varias, el fichero
debe cumplirlas todas:

| Filtro | Tipo | Ejemplo | Qué hace |
| --- | --- | --- | --- |
| `extensiones` | lista de textos | `[".jpg", ".png"]` | Solo esas extensiones, sin distinguir mayúsculas. |
| `patron` | regex | `"(?i).*\\.tmp$"` | Expresión regular sobre el nombre del fichero. |
| `mas_antiguo_que_dias` | entero > 0 | `30` | Solo ficheros modificados hace más de N días. |
| `mayor_que_mb` | número > 0 | `100` | Solo ficheros de más de N MB. |

En las plantillas de `renombrar` se pueden usar estos huecos:

| Hueco | Ejemplo de resultado | Qué representa |
| --- | --- | --- |
| `{fecha:%Y-%m-%d}` | `2026-10-27` | Fecha de modificación del fichero. |
| `{n:03}` | `001` | Contador de la ejecución, con ceros a la izquierda. |
| `{ext}` | `.jpg` | Extensión original en minúsculas. |
| `{nombre}` | `IMG_2041` | Nombre original sin extensión. |

La plantilla no puede contener barras: el fichero se renombra en su misma
carpeta. Se prueba con un nombre de muestra y se rechazan formatos inválidos,
caracteres prohibidos en Windows (`/ \ < > : " | ? *`), nombres reservados
(`CON`, `NUL`, `COM1`…) y nombres que acaban en punto o espacio. Si el destino
ya existe, se añade ` (1)`, ` (2)`… y nunca se sobrescribe nada.

`tareas validar` rechaza también campos desconocidos en la raíz y en cada
acción: así un typo como `"filtros"` en vez de `"filtro"` no puede hacer que una
acción destructiva vea todos los ficheros.

### Mis acciones

| Nombre | Tipo | Qué hace |
| --- | --- | --- |
| `limpiar-temporales` | borrar | Borra `.tmp` de `~/Descargas` con más de 30 días; confirma antes. |
| `mover-imagenes` | mover | Mueve imágenes de `~/Descargas` a `~/Imágenes/Fotos`. |
| `renombrar-capturas` | renombrar | Renombra capturas de `~/Imágenes/Capturas` como `2026-10-27_001.png`. |

Las rutas de `acciones.json` son las de mi equipo Linux en español. En Windows
o macOS pueden llamarse `Downloads` o `Pictures`: se cambian en el JSON o se
crea otro fichero y se pasa con `--config`.

## Estructura

```text
cli-tareas/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── .gitattributes
├── opencode.json              Permisos del agente
├── AGENTS.md                  Normas del proyecto
├── README.md
├── acciones.json              Mis acciones
├── .opencode/
│   ├── skills/acciones-json/SKILL.md
│   ├── commands/nueva-accion.md
│   └── agents/revisor.md
├── docs/
│   ├── prompts.md             Cuaderno de prompts
│   └── adr/0001-configuracion-externa.md
└── src/
    └── tareas/
        ├── __init__.py        Versión del paquete
        ├── __main__.py        python -m tareas
        ├── bienvenida.py      Banner ASCII de bienvenida
        ├── capturas.py        Detecta capturas y las manda a la papelera
        ├── cli.py             Órdenes, opciones y salida
        ├── config.py          Carga y valida acciones.json
        ├── imagenes.py        Comprime imágenes sin tocar los originales
        ├── informe.py         Cuenta ficheros, tipos y capturas pendientes
        ├── menu.py            Menú interactivo de todas las órdenes
        ├── errores.py         Excepciones propias
        ├── acciones.py        Clases Mover, Copiar, Renombrar y Borrar
        └── motor.py           Selecciona ficheros y ejecuta la acción
```

## Estado de la semana 1

Órdenes comprobadas:

- `tareas --help` y `tareas version`.
- `tareas listar ~/pruebas-tareas`: tabla con carpetas primero, tamaños legibles y fechas.
- `tareas listar` sin carpeta: usa la carpeta actual.
- Carpeta vacía: aviso sin tabla.
- Ruta inexistente o fichero: mensaje en stderr y código 1.
- Nombres con corchetes (`[borrador].pdf`) y espacios: se muestran enteros.
- `uv run python -m tareas version`: funciona.
- `uv tool install --editable .`: comandos disponibles desde cualquier carpeta.

Modelo del centro: comprobado con `opencode run`; responde correctamente con la clave configurada en `CENTRO_IA_KEY`.

## Estado de la bienvenida

- `tareas hola` y el ejecutable directo `hola` muestran el banner ASCII.
- El mensaje «Bienvenido a mi terminal personalizado» aparece centrado.
- Funciona sin `acciones.json` y no modifica ningún fichero.
- Comprobado desde cualquier carpeta, también con la instalación global.

## Estado del menú interactivo

- `tareas` sin argumentos abre el menú; `tareas --help` sigue mostrando la ayuda.
- Desde el menú funcionan `version`, `hola`, `cambio`, `listar`, `capturas`, `informe`, `validar`, `acciones` y `ejecutar`.
- `cambio` pone el menú en rojo y vuelve a pintarlo; `cambio normal` lo restaura.
- `salir`, `exit`, `quit` y `q` cierran el menú; `ayuda` y `?` muestran la ayuda.
- También acepta el prefijo `tareas`, por ejemplo `tareas version`.
- Las órdenes nuevas aparecen en el menú automáticamente.
- Probado con entrada por tubería (`printf 'version\nsalir\n' | tareas`) y sin entrada.

## Estado de la semana 2

Comprobado en `~/pruebas-tareas/semana2`, sin tocar ficheros reales:

- `tareas validar`: detecta 3 acciones válidas y devuelve código 3 con JSON roto, tipo inexistente, nombre repetido, regex inválida o falta de `destino`.
- `validar` rechaza campos desconocidos (por ejemplo `filtros`), JSON que no está en UTF-8, números `NaN`/`Infinity` y plantillas que generarían nombres inválidos en Windows.
- `tareas acciones`: muestra nombre, tipo y descripción de las 3 acciones.
- `tareas ejecutar ... --simular`: enseña origen, destino y estado sin crear carpetas ni mover, renombrar o borrar nada.
- Ejecución real en la carpeta de pruebas: mover, renombrar y borrar funcionan con tildes, eñes, espacios y extensiones en mayúsculas.
- Destino ocupado: se usa `FOTO1 (1).JPG`; tampoco se sustituye un symlink roto.
- Acción o carpeta inexistente: mensaje humano y código 1, sin traceback.
- Borrar sin `--si`: pregunta; si se responde que no, no borra y termina con código 1.
- Repetir mover o renombrar: la segunda vez no encuentra ficheros y no duplica nombres.
- Dos ficheros que generarían el mismo nombre: la simulación reserva `(1)` y la ejecución real coincide con lo enseñado.
- Renombrar cuando un destino queda libre al mover otro fichero del mismo lote: la simulación también lo tiene en cuenta.
- Fallo de permisos en un fichero: los demás terminan, se muestra el error de ese fichero y la orden sale con código 1 sin traceback.

## Estado de la orden capturas

Comprobado en `~/pruebas-tareas/semana3/capturas`:

- Detecta la carpeta de descargas configurada en XDG (`~/Baixades` en este equipo).
- Reconoce `Screenshot`, `Screen Shot`, `Captura de pantalla` y `Capture d'écran`.
- Solo selecciona imágenes y descarta otros ficheros y los enlaces simbólicos.
- Con `--simular` no envía nada a la papelera.
- Con `--si` envía las capturas antiguas a la papelera del sistema.
- `--horas` cambia el límite y `--carpeta` permite probar en una carpeta aislada.

## Estado de la orden informe

Comprobado en `~/pruebas-tareas/semana3/capturas`:

- Cuenta ficheros y carpetas del primer nivel, sin seguir enlaces simbólicos.
- Suma el tamaño total y agrupa por extensión.
- Distingue capturas totales de las pendientes de papelera.
- Muestra los ficheros más antiguos y los más grandes.
- `--top` limita las tablas y `--horas` cambia el límite de capturas pendientes.
- Carpeta vacía: resumen a cero sin errores.
- Ruta inexistente o fichero: código 1 sin traceback.
- `--top 0` o `--horas 0`: error de uso con código 2.

Pendiente para las semanas 3 y 4: capa de IA, pruebas automáticas con `pytest`,
GitHub Actions, release v1.0 y prueba de instalación en otro sistema.
