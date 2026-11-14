# tareas 🎯

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 27/10/2026) 📋

1. **Problema:** cada semana pierdo tiempo ordenando Descargas, limpiando temporales antiguos y poniendo nombre a las capturas a mano.
2. **Para quién:** para mí y para mis compañeros de clase.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes:** `--help`, `version`, `hola`, `cambio`, `listar`, `capturas`, `temporales`, `informe`, `imagenes`, `chuleta`, `sistema`, `cita`, `acciones`, `validar`, `ejecutar`, `doctor`, `comprobar-ia` y `ia sugerir`/`ia explicar`.
5. **Mis acciones:** limpiar temporales de más de 30 días, mover imágenes a `~/Imágenes/Fotos`, renombrar capturas por fecha y copiar instaladores `.exe`/`.deb` a una carpeta de respaldo.
6. **Nunca hará:** borrar sin pedir confirmación (salvo `--si`) ni tocar ficheros fuera del origen y destino configurados.
7. **Plataformas:** Linux primero; también Windows y macOS.
8. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
9. **Seguridad:** toda acción, `capturas`, `temporales` e `imagenes` se pueden simular con `--simular`; nunca se sobrescribe un fichero ni un enlace existente y las imágenes siempre se guardan como copias.
10. **Instalación:** `uv tool install --editable .` (se completa en la semana 4).

## Instalación en otro equipo

Antes de instalar en otro equipo, sube los últimos cambios con `git push`.

Requisitos: Git y `uv` instalados. `uv` puede instalar Python 3.12.

### Windows (PowerShell)

Abre PowerShell y instala Git y `uv` con `winget`:

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
```

Cierra y vuelve a abrir PowerShell. Comprueba que funcionan:

```powershell
git --version
uv --version
```

Los comandos de instalación de las secciones siguientes funcionan igual en
PowerShell. Si `winget` no está disponible, instala Git y `uv` desde sus
instaladores oficiales.

### Solo para usar la terminal

Si no vas a modificar el código, instala directamente desde GitHub:

```bash
uv python install 3.12
uv tool install git+https://github.com/javiersansano222/CLI-TAREASJAVIER --force
uv tool update-shell   # si «tareas» no aparece en el PATH
# cierra y abre una terminal nueva
tareas --help
tareas sistema
hola
```

### Para desarrollar y probar cambios

```bash
git clone https://github.com/javiersansano222/CLI-TAREASJAVIER.git
cd CLI-TAREASJAVIER
uv python install 3.12
uv sync
uv run tareas --help
uv tool install --editable . --force
uv tool update-shell   # si «tareas» no aparece en el PATH
# cierra y abre una terminal nueva
tareas --help
```

`uv run tareas` solo funciona dentro del repositorio. Para usarla desde
cualquier carpeta, usa `tareas` después de instalarla como herramienta.

### Actualizar

Instalación desde GitHub:

```bash
uv tool install git+https://github.com/javiersansano222/CLI-TAREASJAVIER --force
```

Instalación editable:

```bash
cd CLI-TAREASJAVIER
git pull
uv sync
uv tool install --editable . --force
```

Si cambia una dependencia y aparece `ModuleNotFoundError`, reinstala con
`--force`; `uv sync` actualiza el proyecto, pero no el entorno global de la
herramienta. Después de `uv tool update-shell`, cierra y abre la terminal.

### Si `tareas` no se reconoce en Windows

```powershell
uv tool update-shell
```

Cierra y abre PowerShell. Si sigue sin aparecer, añade esta carpeta al PATH:

```text
%USERPROFILE%\.local\bin
```

### Rutas de acciones en Windows y macOS

`acciones.json` usa rutas de Linux en español (`~/Descargas`, `~/Imágenes`,
`~/Documentos`). En Windows y macOS las carpetas del home se llaman `Downloads`,
`Pictures` y `Documents` **en disco** (Finder puede mostrarlas traducidas, pero
la ruta real es la inglesa). Cambia el JSON o usa uno de los ficheros listos
con `--config`:

- `acciones-win.json`: capturas en `~/Pictures/Screenshots`, instaladores
  `.exe`/`.msi`.
- `acciones-mac.json`: capturas en `~/Desktop` (ahí las guarda macOS por
  defecto), instaladores `.dmg`/`.pkg`.

```powershell
# Ejemplo en Windows (en macOS, igual con tareas en vez de uv run tareas)
uv run tareas --config acciones-win.json validar
uv run tareas --config acciones-win.json ejecutar renombrar-capturas --simular
```

## Uso rápido

```bash
tareas                  # abre el menú interactivo
tareas --help           # ayuda general
tareas cambio           # abre el menú en rojo
tareas chuleta          # referencia rápida de Git y Linux
tareas sistema          # disco y memoria en uso

hola
tareas hola

tareas capturas --simular
tareas capturas
tareas capturas --carpeta ~/pruebas-tareas/capturas --horas 5

tareas temporales --simular
tareas temporales --carpeta ~/pruebas-tareas/temporales --dias 30

tareas informe
tareas informe --carpeta ~/pruebas-tareas/capturas --top 3

tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --simular
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --si
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --webp --simular

tareas validar
tareas acciones
tareas ejecutar limpiar-temporales --simular
tareas ejecutar mover-imagenes --simular
tareas ejecutar renombrar-capturas --simular
tareas ejecutar copiar-instaladores --simular

tareas mirar-espacio --simular
tareas mirar-espacio /ruta/a/carpeta

# Solo cuando la simulación sea la esperada:
tareas ejecutar limpiar-temporales
tareas ejecutar limpiar-temporales --si

# Otro fichero de acciones:
tareas --config ~/pruebas-tareas/acciones.json acciones
```

Todas las órdenes funcionan desde cualquier carpeta. `--config` es una opción
global y va **antes** de la orden. Por defecto se lee `./acciones.json`, en la
carpeta desde la que se lanza la orden.

## Chuleta de Git y Linux

`tareas chuleta` muestra una referencia rápida de Git, navegación, archivos,
permisos, procesos, red y compresión. Dentro del menú interactivo también
funciona `/chuleta` (y `chuleta`).

## Estado del sistema

`tareas sistema` muestra el tamaño total, usado y libre del disco de la carpeta
personal, además del uso de la memoria RAM. Dentro del menú interactivo también
funciona `/sistema` (y `sistema`).

## Diagnóstico del entorno

`tareas doctor` hace un chequeo de solo lectura y pinta una tabla con el estado
de cada comprobación: `acciones.json`, las dependencias opcionales (`send2trash`,
Pillow, `psutil`), la carpeta de descargas, el origen de cada acción y la carpeta
de pruebas `~/pruebas-tareas`.

```bash
tareas doctor
```

No crea, mueve ni borra nada. Los ⚠ son avisos (código 0): algo funciona a medias,
como una carpeta que falta o una dependencia opcional. Un ✘ es bloqueante (código 3):
`acciones.json` no se puede leer o no cumple el esquema. Si todo sale ✔, «Todo listo».

## IA del centro

El servidor del centro (`CENTRO_IA_URL` + `CENTRO_IA_KEY`) se usa desde dos
sitios: las órdenes `ia` y las **acciones con IA** de `acciones.json`.

```bash
# Comprobar que el modelo responde (no enseña la clave)
tareas comprobar-ia

# Órdenes sueltas
tareas ia sugerir "quiero mover los PDF de Descargas a Documentos/pdf"
tareas ia explicar renombrar-capturas ~/pruebas-tareas/capturas

# Acciones con IA (primero siempre --simular)
tareas ejecutar resumir-apuntes ~/pruebas-tareas/Apuntes --simular
```

- `comprobar-ia` manda una pregunta mínima y dice si el modelo responde, con
  su tiempo. Muestra la URL y «clave: definida», nunca la clave.
- `ia sugerir` pide una descripción en lenguaje natural y devuelve una acción
  **validada con el esquema real de `acciones.json`**, lista para pegar en el
  fichero. No escribe nada: la propuesta se revisa con `tareas validar` y
  `--simular` antes de nada.
- `ia explicar` ejecuta la **simulación** de una acción (no toca ningún
  fichero) y la IA la traduce a lenguaje claro: qué pasaría y a qué
  prestar atención.

### Acciones con IA

`tareas acciones` enseña una columna **IA** que marca cuáles necesitan el
modelo. Ahora mismo son tres, todas sobre `~/pruebas-tareas/Apuntes`:

| Acción | Tipo | Qué hace |
| --- | --- | --- |
| 📝 `resumir-apuntes` | `resumir` | Escribe `{nombre}.resumen.md` en `~/pruebas-tareas/Resúmenes`. |
| 🏷️ `renombrar-apuntes` | `renombrar_ia` | Les pone un nombre claro; la extensión no cambia. |
| 🗂️ `clasificar-apuntes` | `clasificar` | Los mueve a `~/pruebas-tareas/Clasificados/<asignatura>`. |

Cómo funciona por dentro:

- **`--simular` no gasta tokens**: solo cuenta caracteres y enseña el
  presupuesto en la columna Detalle («enviaría 12000 caracteres (~3000
  tokens, sin gastar)»). Tampoco pide clave.
- **Sin clave o sin red**, la acción sale con **código 4** y un mensaje que
  recuerda que *las acciones sin IA siguen funcionando*; no se toca ningún
  fichero.
- Lo que devuelva el modelo pasa siempre por una limpieza (`a_nombre_seguro`
  o la lista de `categorias`): si no hay nada válido, el fichero queda
  **saltado** con su motivo, nunca se inventa un nombre ni una carpeta.
- El texto se recorta a `max_caracteres` (500-50000) antes de enviarse, y un
  PDF sin texto extraíble se salta.

### Si algo falla

**Sin clave o sin red**, las órdenes `ia` y las acciones con IA lo explican en
un mensaje humano y terminan con **código 4**; **el resto de órdenes no
dependen de la IA y siguen funcionando igual** (verificado con `validar`,
`acciones`, `doctor` y `ejecutar` sin IA, todos a 0). El servidor del centro
usa un certificado propio de la red del instituto: `tareas` lo valida con la
CA si la encuentra en `~/.config/opencode/ca-simarro.crt`; en caso contrario
el error indica cómo añadir la CA (o `IA_TLS_VERIFICAR=0` solo dentro de la
red del centro).

## Menú interactivo

Al escribir `tareas` sin argumentos se abre un menú con todas las órdenes
disponibles. Desde ahí se escribe la orden igual que en la terminal:

```text
tareas> version
tareas> hola
tareas> cambio
tareas> capturas --simular
tareas> temporales --simular
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

## Ficheros temporales

`tareas temporales` busca ficheros temporales antiguos en el primer nivel de una
carpeta (por defecto, la de descargas) y los envía a la papelera. Considera
temporales las extensiones `.tmp`, `.temp`, `.bak`, `.old`, `.part`, `.partial`,
`.crdownload`, `.download`, `.swp` y `.swo`, los nombres `.DS_Store` y
`Thumbs.db`, los bloqueos de Office `~$…` y los respaldos que acaban en `~`.

```bash
tareas temporales --simular
tareas temporales --carpeta ~/pruebas-tareas/temporales
tareas temporales --carpeta ~/pruebas-tareas/temporales --dias 7
tareas temporales --carpeta ~/pruebas-tareas/temporales --si
```

Por defecto solo toca ficheros con **30 días o más**; `--dias` cambia esa
antigüedad. Ignora subcarpetas, enlaces simbólicos y ficheros recientes. Sin
`--si`, pide confirmación, y `--simular` enseña la lista sin enviar nada a la
papelera.

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

## Comprimir y convertir imágenes

`tareas imagenes` lista las imágenes JPEG, PNG y WebP del primer nivel de una
carpeta (por defecto, la de descargas). Con `--comprimir` crea copias más
ligeras en `comprimidas` sin modificar ni borrar los originales.

```bash
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --simular
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --comprimir --si
tareas imagenes --comprimir --calidad 80 --destino ~/pruebas-tareas/comprimidas

tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --webp --simular
tareas imagenes --carpeta ~/pruebas-tareas/semana4/imagenes --webp --si
tareas imagenes --webp --calidad 85 --destino ~/pruebas-tareas/webp
```

`--calidad` va de 1 a 95 y se aplica a JPEG y WebP; PNG se guarda con
compresión sin pérdida. Si una copia no reduce el tamaño, se descarta y la
imagen aparece como «saltada». Si el nombre ya existe en el destino, se usa
` (1)`, ` (2)`… y nunca se sobrescribe nada. Los enlaces simbólicos, las
subcarpetas y las imágenes animadas se ignoran o se marcan como no
compatibles.

Con `--webp` se convierte cada imagen a WebP y la copia se guarda como
`.webp`, aunque no sea más pequeña. Esta opción implica `--comprimir`; el
original se conserva y el destino por defecto sigue siendo `comprimidas`.

`--simular` enseña qué se haría sin crear la carpeta de destino ni escribir
ficheros. Sin `--si`, la compresión o conversión real pide confirmación. Usa
Pillow para leer y guardar las imágenes.

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
| `tipo` | sí | texto | `mover`, `copiar`, `renombrar`, `borrar`, `mirar_espacio`, `resumir`, `renombrar_ia` o `clasificar`. |
| `origen` | no | ruta | Carpeta por defecto si no se pasa `CARPETA`. Admite `~`. |
| `filtro` | no | objeto | Limita qué ficheros se tocan. Sin filtro se seleccionan todos. |
| `destino` | mover/copiar/clasificar/resumir | ruta | Carpeta de destino. Se crea si no existe. |
| `plantilla` | renombrar | texto | Nombre nuevo con huecos `{fecha}`, `{n}`, `{ext}` y `{nombre}`. |
| `confirmar` | no | booleano | Pide confirmación antes de borrar. Por defecto, `true`; si se pone `false`, no pregunta. |
| `instrucciones` | con IA | texto | Qué se le pide al modelo. Obligatorio en `resumir`, `renombrar_ia` y `clasificar`. |
| `max_caracteres` | con IA | entero 500-50000 | Tope de texto que se envía. Por defecto, `12000`. |
| `categorias` | clasificar | lista no vacía | Categorías entre las que elige el modelo. Sin repetidos. |

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
| 🧹 `limpiar-temporales` | borrar | Borra `.tmp` de `~/Descargas` con más de 30 días; confirma antes. |
| 🖼️ `mover-imagenes` | mover | Mueve imágenes de `~/Descargas` a `~/Imágenes/Fotos`. |
| 🖋️ `renombrar-capturas` | renombrar | Renombra capturas de `~/Imágenes/Capturas` como `2026-10-27_001.png`. |
| 📦 `copiar-instaladores` | copiar | Copia los instaladores `.exe` y `.deb` de `~/Descargas` a `~/Documentos/Instaladores`. |
| 👁️ `mirar-espacio` | mirar_espacio | Muestra el espacio total y número de ficheros de una carpeta. |
| 📝 `resumir-apuntes` | resumir | Resume con IA los apuntes de `~/pruebas-tareas/Apuntes` en `.resumen.md`. |
| 🏷️ `renombrar-apuntes` | renombrar_ia | Les pone un nombre claro con IA; la extensión no cambia. |
| 🗂️ `clasificar-apuntes` | clasificar | Mueve cada apunte a la subcarpeta de su asignatura. |

Las rutas de `acciones.json` son las de mi equipo Linux en español. En Windows
y macOS las carpetas del home llevan nombre inglés en disco, así que hay un
fichero listo por sistema, con las mismas 8 acciones y solo cambian dos cosas:
dónde van las capturas y qué extensión tienen los instaladores.

```powershell
# Windows: capturas en ~/Pictures/Screenshots, instaladores .exe/.msi
uv run tareas --config acciones-win.json validar
uv run tareas --config acciones-win.json ejecutar renombrar-capturas --simular
```

```bash
# macOS: capturas en ~/Desktop (el destino por defecto de screencapture),
# instaladores .dmg/.pkg
tareas --config acciones-mac.json validar
tareas --config acciones-mac.json ejecutar renombrar-capturas --simular
```

Si en tu Mac guardas las capturas en otra carpeta, cámbialo con
`defaults write com.apple.screencapture location ~/Pictures/Screenshots` y
ajusta el `origen` de `renombrar-capturas` en el JSON.

`acciones.json` no se empaqueta con la instalación: fuera del repositorio,
las órdenes que lo necesitan (`validar`, `acciones`, `ejecutar`) dan código 3
si no les pasas `--config` con la ruta. `version`, `hola`, `sistema`,
`comprobar-ia` y el menú no lo necesitan.

## Estructura

```text
cli-tareas/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── .gitattributes
├── .env.example              Plantilla de claves (sin valores)
├── opencode.json              Permisos del agente
├── AGENTS.md                  Normas del proyecto
├── README.md
├── prompt.txt                 Lo que queda para clase
├── acciones.json              Mis acciones (rutas de Linux)
├── acciones-win.json          Lo mismo, con rutas de Windows
├── acciones-mac.json          Lo mismo, con rutas de macOS
├── .opencode/
│   ├── skills/acciones-json/SKILL.md
│   ├── commands/nueva-accion.md
│   └── agents/revisor.md
├── docs/
│   ├── prompts.md             Cuaderno de prompts
│   └── adr/
│       ├── 0001-configuracion-externa.md
│       └── 0002-ia-interfaz-y-salida-4.md
├── tests/                     Suite con pytest (37 en verde)
└── src/
    └── tareas/
        ├── __init__.py        Versión del paquete
        ├── __main__.py        python -m tareas
        ├── bienvenida.py      Banner ASCII de bienvenida
        ├── capturas.py        Detecta capturas y las manda a la papelera
        ├── chuleta.py         Chuleta de Git y comandos de Linux
         ├── cli.py             Órdenes, opciones y salida
         ├── sistema.py         Disco y memoria en uso
         ├── config.py          Carga y valida acciones.json
         ├── doctor.py          Diagnóstico de solo lectura del entorno
         ├── ia.py              ProveedorIA y ProveedorCentro (httpx, .env)
         ├── rutas.py           Detección de la carpeta de descargas (XDG)
         ├── imagenes.py        Comprime imágenes sin tocar los originales
        ├── informe.py         Cuenta ficheros, tipos y capturas pendientes
        ├── menu.py            Menú interactivo de todas las órdenes
        ├── temporales.py      Detecta temporales antiguos y los manda a la papelera
         ├── errores.py         Excepciones propias
         ├── acciones.py        Clases Mover, Copiar, Renombrar, Borrar y MirarEspacio
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

## Claves y configuración privada

Las claves de los modelos del centro van **siempre** en variables de entorno,
nunca en un fichero del repositorio. La CLI lee sola el `.env` de la carpeta
desde la que lanzas la orden (con `python-dotenv`, buscando hacia arriba);
si la variable ya está exportada en la terminal, manda esa y el `.env` se
ignora. El repo incluye `.env.example` como plantilla:

```bash
cp .env.example .env   # y edita .env con tu clave real
```

En Windows (PowerShell), como `copy` no crea bien ficheros vacíos desde una
plantilla, usa: `Copy-Item .env.example .env` o `notepad .env`.

- `.env` está en `.gitignore` desde el primer commit y no debe subirse jamás.
- `.env.example` sí se sube: es solo la plantilla, sin valores.
- Las variables usadas son `CENTRO_IA_KEY` (la clave) y, si hace falta,
  `CENTRO_IA_URL` (el servidor del centro).
- Sin clave, la herramienta sigue funcionando: solo las órdenes que necesiten
  IA la pedirán, y explicarán qué falta.

## Estado de la bienvenida

- `tareas hola` y el ejecutable directo `hola` muestran el banner ASCII.
- El mensaje «Bienvenido a mi terminal personalizado» aparece centrado.
- Funciona sin `acciones.json` y no modifica ningún fichero.
- Comprobado desde cualquier carpeta, también con la instalación global.

## Estado del menú interactivo

- `tareas` sin argumentos abre el menú; `tareas --help` sigue mostrando la ayuda.
- Desde el menú funcionan `version`, `hola`, `cambio`, `listar`, `capturas`, `informe`, `chuleta`, `sistema`, `validar`, `acciones`, `ejecutar` y `doctor`.
- `cambio` pone el menú en rojo y vuelve a pintarlo; `cambio normal` lo restaura.
- `salir`, `exit`, `quit` y `q` cierran el menú; `ayuda` y `?` muestran la ayuda.
- También acepta el prefijo `tareas`, por ejemplo `tareas version`.
- Las órdenes nuevas aparecen en el menú automáticamente.
- Probado con entrada por tubería (`printf 'version\nsalir\n' | tareas`) y sin entrada.

## Estado de la semana 2

Comprobado en `~/pruebas-tareas/semana2`, sin tocar ficheros reales:

- `tareas validar`: detecta 4 acciones válidas y devuelve código 3 con JSON roto, tipo inexistente, nombre repetido, regex inválida o falta de `destino`.
- `validar` rechaza campos desconocidos (por ejemplo `filtros`), JSON que no está en UTF-8, números `NaN`/`Infinity` y plantillas que generarían nombres inválidos en Windows.
- `tareas acciones`: muestra nombre, tipo y descripción de las 4 acciones.
- `tareas ejecutar ... --simular`: enseña origen, destino y estado sin crear carpetas ni mover, renombrar o borrar nada.
- `mirar-espacio` se añadió como nueva acción; simulación muestra espacio y ficheros sin tocar nada.
- `copiar-instaladores` se añadió con el flujo de `/nueva-accion`; la simulación detecta `.exe` y `.deb` y no escribe en el destino.
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

## Estado de `tareas doctor`

- Tabla ✔/⚠/✘ de config, dependencias, descargas, orígenes, IA y `~/pruebas-tareas`.
- Sin tocar disco: solo lectura; ninguna creación, borrado ni escritura.
- JSON roto con `--config` → ✘ con el motivo exacto (línea y columna) y código 3.
- Config válida con avisos → resumen amarillo y código 0.

## Estado de la capa IA

**Diseño:** `ProveedorIA` (interfaz) + `ProveedorCentro` (httpx) y
`IANoDisponible` con **código 4** — ver `docs/adr/0002-ia-interfaz-y-salida-4.md`.

Comprobado en modo aislado, sin red del centro:

- `tareas comprobar-ia` sin clave: «Falta CENTRO_IA_URL, CENTRO_IA_KEY…» +
  aviso de que el resto sigue, **código 4**.
- `tareas comprobar-ia` con el servidor caído: «No hay conexión con el
  servidor del centro…», **código 4**, sin traceback y sin enseñar la clave
  (solo «clave: definida»).
- `ejecutar resumir-apuntes --simular` sin clave: presupuesto por fichero
  («enviaría N caracteres (~M tokens, sin gastar)») y **código 0**.
- `ejecutar resumir-apuntes` / `clasificar-apuntes` / `renombrar-apuntes` sin
  clave: **código 4**, ningún fichero tocado.
- `max_caracteres: 400` en el JSON: «debe ser un entero entre 500 y 50000»,
  **código 3**. Lo mismo para `categorias` ausentes o repetidas y para
  `instrucciones` vacío.
- Fichero sin texto extraíble: estado `saltado` con su motivo, no un error.
- Las órdenes que no son de IA (`validar`, `acciones`, `version`, `doctor`,
  `ejecutar` sin IA) siguen saliendo **0** con el entorno vacío.
- `tareas acciones` enseña la columna **IA** y el pie «las N restantes
  funcionan sin red».
- `tests/test_ia.py`: 12 tests con `httpx.post` parcheado (sin red).
  `tests/test_acciones.py`: limpia de `a_nombre_seguro`, categorías con
  tildes y simulación que no mueve nada. Suite completa: **37 tests en
  verde** y 8 fallos preexistentes escritos en Linux (`uv`, `/home/...`).

`uv.lock` ya incluye `httpx`, `python-dotenv` y `pypdf`. Pendiente hasta la
semana 4: probar las tres acciones contra el servidor real del centro desde la
red del instituto.
