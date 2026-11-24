# tareas 🎯

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 27/10/2026) 📋

1. **Problema:** cada semana pierdo tiempo ordenando Descargas, limpiando temporales antiguos y poniendo nombre a las capturas a mano.
2. **Para quién:** para mí y para mis compañeros de clase.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes:** `--help`, `version`, `hola`, `cambio`, `tema`, `listar`, `buscar`, `organizar`, `mover`, `capturas`, `temporales`, `informe`, `imagenes`, `chuleta`, `sistema`, `cita`, `acciones`, `validar`, `ejecutar`, `doctor`, `historial`, `deshacer`, `comprobar-ia` y `ia sugerir`/`ia explicar`.
5. **Mis acciones:** limpiar temporales de más de 30 días, mover imágenes a `~/Imágenes/Fotos`, renombrar capturas por fecha y copiar instaladores `.exe`/`.deb` a una carpeta de respaldo.
6. **Nunca hará:** borrar sin pedir confirmación (salvo `--si`) ni tocar ficheros fuera del origen y destino configurados.
7. **Plataformas:** Linux primero; también Windows y macOS.
8. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida · 4 IA no disponible (las demás órdenes siguen).
9. **Seguridad:** toda acción, `capturas`, `temporales` e `imagenes` se pueden simular con `--simular`; nunca se sobrescribe un fichero ni un enlace existente y las imágenes siempre se guardan como copias.
10. **Instalación:** un solo comando con `instalar.ps1` (Windows) o `instalar.sh` (macOS/Linux); para desarrollar, `uv tool install --editable .`.

## Instalación en otro equipo

Antes de instalar en otro equipo, sube los últimos cambios con `git push`.

Las órdenes de instalación de esta sección (el comando de un solo paso y la
instalación a mano) se han probado y funcionan en los tres sistemas: Windows,
Linux y macOS. Los dos scripts (`instalar.ps1` en Windows y `instalar.sh` en
Linux y macOS) instalan `uv` y Python, bajan la CLI desde GitHub, la dejan
disponible como comando `tareas` desde cualquier carpeta y comprueban al final
que todo está correcto. Además, las pruebas automáticas se ejecutan en los tres
sistemas en cada cambio, así que el código queda verificado también en equipos
distintos al mío.

### Un solo comando (recomendado)

Baja todo de GitHub: no hace falta Git ni clonar el repo.

**Windows (PowerShell):**

```powershell
powershell -c "irm https://raw.githubusercontent.com/javiersansano222/CLI-TAREASJAVIER/main/instalar.ps1 | iex"
```

**macOS / Linux (terminal):**

```bash
curl -fsSL https://raw.githubusercontent.com/javiersansano222/CLI-TAREASJAVIER/main/instalar.sh | bash
```

El script (está en el repo: `instalar.ps1` y `instalar.sh`) hace, en este
orden:

1. Instala `uv` y Python 3.12 si faltan.
2. Baja la CLI desde GitHub y la instala (`uv tool install … --force`).
3. La pone en el PATH (`uv tool update-shell`).
4. Copia a tu carpeta de inicio `.env` (plantilla) y `acciones.json`
   (rutas de tu sistema) **solo si no existen**: nunca pisa tu `.env`.
5. Crea `~/pruebas-tareas` con `Apuntes`, `Resúmenes` y `Clasificados`.
6. Comprueba la instalación con `tareas version` y `tareas validar`.

Al terminar, **cierra y vuelve a abrir la terminal** y escribe
`tareas --help`, `hola` y `tareas validar`. Recuerda rellenar `.env` con tu
clave: sin ella las órdenes de IA salen con código 4. Para actualizar,
vuelve a lanzar la misma línea.

Si al abrirla `tareas` sigue sin reconocerse, salta a
[«Si `tareas` no se reconoce en Linux o macOS»](#si-tareas-no-se-reconoce-en-linux-o-macos).

Si prefieres verlo antes de ejecutarlo:

```powershell
git clone https://github.com/javiersansano222/CLI-TAREASJAVIER.git
cd CLI-TAREASJAVIER
powershell -ExecutionPolicy Bypass -File instalar.ps1   # Windows
bash instalar.sh                                        # macOS / Linux
```

### Instalación a mano

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

Para usar `tareas` sin tocar el código. Hace falta conexión a internet y **no
hace falta `git`**. Todo se instala en tu carpeta personal; el único paso que
puede pedir contraseña es instalar `curl` si no viene de serie.

**1. Instala `uv`**, el gestor que baja Python y la herramienta:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Si dice `curl: command not found`:

```bash
sudo apt update && sudo apt install -y curl     # Ubuntu, Debian, Lliurex
```

En macOS `curl` ya viene instalado. En Windows, usa `winget install --id
astral-sh.uv -e` y sigue desde el paso 3.

**2. Carga `uv` en esta terminal.** El instalador corre en una subshell, así que
su PATH no se queda en tu ventana: hay que cargarlo a mano una vez.

```bash
source ~/.local/bin/env
uv --version
```

**3. Instala Python y la última versión de `main`:**

```bash
uv python install 3.12
uv tool install https://github.com/javiersansano222/CLI-TAREASJAVIER/archive/refs/heads/main.tar.gz --force
```

El `.tar.gz` evita depender de `git`. Si lo tienes y lo prefieres, esta orden
hace lo mismo:

```bash
uv tool install git+https://github.com/javiersansano222/CLI-TAREASJAVIER --force
```

**4. Comprueba que funciona:**

```bash
tareas version
tareas --help | grep -E "historial|deshacer|mover|organizar"
```

`version` dice `1.1.0` en toda esta entrega, así que la segunda orden es la que
confirma que tienes las órdenes más recientes.

**5. Para que `uv` y `tareas` sigan ahí en la próxima terminal** (solo una vez):

```bash
echo '. "$HOME/.local/bin/env"' >> ~/.bashrc
source ~/.bashrc
```

En zsh (el shell por defecto de macOS) usa `~/.zshrc`. En Windows este paso no
hace falta: `winget` ya deja `uv` en el PATH y `uv tool update-shell` hace lo
mismo con `tareas`. Si al abrir otra terminal `tareas` sigue sin reconocerse, mira
[«Si `tareas` no se reconoce en Linux o macOS»](#si-tareas-no-se-reconoce-en-linux-o-macos).

Para **actualizar** más adelante, repite el paso 3: el `--force` reemplaza la
versión instalada. Para **congelar** una versión concreta, usa su etiqueta:

```bash
uv tool install https://github.com/javiersansano222/CLI-TAREASJAVIER/archive/refs/tags/v1.0.0.tar.gz --force
uv tool install git+https://github.com/javiersansano222/CLI-TAREASJAVIER@v1.0.0 --force
```

### Primeros pasos

1. Copia `acciones.json` de este repo en tu carpeta de inicio (`acciones-win.json`
   si estás en Windows, `acciones-mac.json` en macOS) y cambia las rutas por
   las tuyas.
2. Comprueba que está bien escrito: `tareas validar`.
3. Mira qué haría, sin tocar nada: `tareas ejecutar ordenar-descargas --simular`.
4. Cuando te convenza, repite la orden sin `--simular`.

### IA (opcional)

Las acciones `resumir`, `renombrar-ia` y `clasificar` usan los modelos del
centro. Copia `.env.example` como `.env`, rellena `CENTRO_IA_URL` y
`CENTRO_IA_KEY`, y comprueba la conexión con `tareas comprobar-ia`. Sin clave
o sin red, la CLI sale con **código 4** y avisa de que las acciones sin IA
siguen funcionando igual.

### Desinstalar

```bash
uv tool uninstall tareas
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

Si instalaste desde la carpeta del repositorio **sin** `--editable` (por
ejemplo `uv tool install .`), la herramienta se queda con una copia del código
en `...\uv\tools\tareas\`: los cambios que hagas en el repositorio no se ven
hasta reinstalar. Para refrescarla:

```bash
uv tool install --reinstall .
```

Con `uv tool install --editable .` no hace falta: `tareas` lee siempre el
código del repositorio.

### Si `tareas` no se reconoce en Windows

El instalador de una línea corre en un PowerShell hijo, así que el PATH que
prepara no se queda en tu ventana. Estos pasos van en orden: para en cuanto
`tareas version` responda.

**1. Comprueba que el ejecutable está instalado:**

```powershell
Test-Path "$env:USERPROFILE\.local\bin\tareas.exe"
```

Si dice `False`, reinstala con:

```powershell
uv tool install https://github.com/javiersansano222/CLI-TAREASJAVIER/archive/refs/heads/main.tar.gz --force
```

**2. Úsalo ya en esta ventana** (solo dura hasta cerrarla):

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
tareas version
```

**3. Déjalo en el PATH de usuario:**

```powershell
uv tool update-shell
```

Si `uv` tampoco se reconoce, usa la ruta completa:
`& "$env:USERPROFILE\.local\bin\uv.exe" tool update-shell`.

**4. Cierra TODAS las ventanas de la terminal**, no solo la pestaña: en Windows
Terminal, las pestañas nuevas heredan el entorno de la ventana que ya estaba
abierta. Si sigue igual, cierra sesión y vuelve a entrar.

La carpeta que debe estar en el PATH es:

```text
%USERPROFILE%\.local\bin
```

Y ojo: la orden es `tareas version`, no `tareas --version`.

### Si `tareas` no se reconoce en Linux o macOS

El instalador se ejecuta en una subshell, así que no puede cambiar el PATH de
tu terminal. Estos pasos van en orden: para en cuanto `tareas` responda. Si el
instalador detecta el problema, ya te muestra al final las dos líneas del
paso 3.

**1. Comprueba si el ejecutable está instalado:**

```bash
ls -l ~/.local/bin/tareas
```

Si dice «No such file or directory», salta al paso 5. Si tampoco existe
`~/.local/bin/uv`, lo que falta es `uv`: vuelve a «Solo para usar la terminal».

**2. Pruébalo con la ruta completa:**

```bash
~/.local/bin/tareas version
```

- Si responde `tareas 1.1.0`, el programa está bien y solo falta el PATH: paso 3.
- Si dice «Permission denied»: paso 4.

**3. Añade `~/.local/bin` al PATH para siempre:**

```bash
echo '. "$HOME/.local/bin/env"' >> ~/.bashrc
source ~/.bashrc
command -v tareas
```

En zsh, cambia `~/.bashrc` por `~/.zshrc`. Después abre una terminal nueva (una
pestaña también sirve: arranca un shell que lee ese fichero) y comprueba:

```bash
tareas version
```

`uv tool update-shell` hace lo mismo en muchos equipos; si esa orden no cambia
nada, usa las dos líneas de arriba.

**4. Si aparece «Permission denied»:**

```bash
chmod +x ~/.local/bin/tareas ~/.local/bin/hola
```

**5. Si el fichero no existe, reinstala y vuelve al paso 1:**

```bash
uv tool install https://github.com/javiersansano222/CLI-TAREASJAVIER/archive/refs/heads/main.tar.gz --force
```

Si tienes `git`, `uv tool install git+https://github.com/javiersansano222/CLI-TAREASJAVIER --force`
hace lo mismo.

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
tareas tema matrix      # cambia los colores de toda la terminal
tareas chuleta          # referencia rápida de Git y Linux
tareas sistema          # disco y memoria en uso
tareas doctor           # diagnostica el entorno

hola
tareas hola

tareas listar ~/Descargas

tareas buscar apuntes --en ~/Documentos
tareas buscar factura --ext pdf
tareas buscar "IMG_[0-9]+\.jpg" --regex

tareas organizar ~/pruebas-tareas/mezcla --simular
tareas organizar ~/pruebas-tareas/mezcla

tareas mover ~/Descargas/apuntes.pdf ~/Documentos --simular
tareas mover ~/Descargas/apuntes.pdf ~/Documentos

tareas historial
tareas deshacer --simular
tareas deshacer

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
global y va **antes** de la orden. Por defecto se busca `./acciones.json` en la
carpeta desde la que se lanza la orden y, si no existe, `~/acciones.json` (donde
lo deja el instalador).

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

`doctor` busca primero `./acciones.json` en la carpeta desde la que lo lanzas y,
si no está, `~/acciones.json` (el que crea el instalador). Si guardas el fichero
en otro sitio, pásale la ruta completa con `--config` (opción global, va **antes**
de la orden):

```bash
tareas --config ~/Documents/CLI-TAREASJAVIER/acciones.json doctor
```

### Si sale «No encuentro acciones.json»

El ✘ significa que no ha aparecido en ninguno de los dos sitios de búsqueda.
Tres salidas, de más a menos automática:

1. **Reinstala** o copia la plantilla (`acciones.json`, `acciones-win.json` o
   `acciones-mac.json`) a tu carpeta de inicio como `~/acciones.json`: es donde
   la buscan todas las órdenes desde cualquier carpeta.
2. **Deja un `acciones.json` en la carpeta actual** si trabajas dentro del repo.
3. **Pásale la ruta exacta** con `--config`, que va siempre antes de la orden.

Después de cualquiera de las tres, `tareas doctor` debe enseñar `acciones.json`
en ✔; si el problema era el contenido, el ✘ te dirá la línea y el campo exactos.

Ejemplo completo en Linux/macOS:

```bash
$ cd ~ && tareas doctor
│ acciones.json │ ✘ error │ No encuentro «acciones.json». ... │   # fallo

# 1) Copiar la plantilla al home (lo que ya hace el instalador)
$ cp ~/Documents/CLI-TAREASJAVIER/acciones.json ~/acciones.json
$ tareas doctor
│ acciones.json │ ✔ ok │ 8 acciones válidas en /home/alumna/acciones.json │

# 2) O, si trabajas dentro del repo, ejecutarlo desde su carpeta
$ cd ~/Documents/CLI-TAREASJAVIER && tareas doctor   # encuentra ./acciones.json

# 3) O, si lo tienes en otro sitio, pasarle la ruta (--config va antes)
$ tareas --config ~/Documents/CLI-TAREASJAVIER/acciones.json doctor
```

Ejemplo completo en Windows (PowerShell):

```powershell
PS C:\> tareas doctor
│ acciones.json │ ✘ error │ No encuentro «acciones.json». ... │   # fallo

# 1) Copiar la plantilla al home (lo que ya hace el instalador)
PS C:\> Copy-Item "$HOME\Documentos\CLI-TAREASJAVIER\acciones.json" "$HOME\acciones.json"
PS C:\> tareas doctor
│ acciones.json │ ✔ ok │ 8 acciones válidas en C:\Users\alumna\acciones.json │

# 2) O, si trabajas dentro del repo, ejecutarlo desde su carpeta
PS C:\> cd "$HOME\Documentos\CLI-TAREASJAVIER"; tareas doctor   # encuentra .\acciones.json

# 3) O, si lo tienes en otro sitio, pasarle la ruta (--config va antes)
PS C:\> tareas --config "$HOME\Documentos\CLI-TAREASJAVIER\acciones.json" doctor
```

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
- Si la IA **no** está disponible, la orden sale con **código 4** y, además
  del motivo, un aviso en amarillo con el **«Qué hacer»** paso a paso y en
  lenguaje normal (qué fichero tocar, si hace falta estar en la red del
  instituto o a quién pedir la clave). El mismo aviso sale en `tareas ia`,
  `tareas doctor` y las acciones con IA: nadie necesita saber de terminales
  para arreglarlo, y el resto de órdenes siguen funcionando sin la IA.
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

Al escribir `tareas` sin argumentos se abre un **panel de mando** pensado para
caber en una pantalla. Arriba están los tres primeros pasos; debajo, las
órdenes agrupadas por lo que quieres hacer; al final, un consejo:

```text
╭─ tareas 1.1.0 ─────────────────────────────────────────────╮
│ Ordena, limpia y entiende tus ficheros sin miedo.          │
╰────────────────────────────────────────────────────────────╯

╭─ Empieza por aquí ─────────────────────────────────────────╮
│ 1  informe              Ver Descargas (solo lectura)       │
│ 2  organizar --simular  Ordenar sin tocar nada             │
│ 3  historial            Ver lo último (y deshacer)         │
╰────────────────────────────────────────────────────────────╯

  ARCHIVOS              SISTEMA                APRENDER
  ───────────────       ───────────────        ───────────────
  organizar  ordena     doctor    diagnostica  chuleta  Git/Linux
  mover      traslada   sistema   disco/RAM    tema     colores
  capturas   limpia     mirar-espacio  mide    cambio   menú
  temporales limpia     informe   resumen      hola     bienvenida
  imagenes   comprime   validar   acciones     cita     frase
  listar     muestra    ejecutar  lanza
  buscar     encuentra

  SEGURIDAD  historial · deshacer
  IA  comprobar-ia · ia sugerir · ia explicar

  Consejo: prueba --simular primero; no toca nada
  escribe una orden · ayuda · salir
```

Los números `1`, `2` y `3` ejecutan el ejemplo correspondiente. También se
puede escribir la orden completa, con sus opciones:

```text
tareas> 2
tareas> capturas --simular
tareas> informe --top 3
tareas> organizar ~/pruebas-tareas/mezcla --simular
tareas> mover ~/Descargas/apuntes.pdf ~/Documentos --simular
tareas> salir
```

`ayuda` o `?` abre la ayuda completa; `salir`, `exit`, `quit` o `q` termina.
Las categorías se generan desde las órdenes registradas en Typer: una orden
nueva que no esté clasificada aparece en **OTRAS**, nunca desaparece. La cita
motivacional ya no ocupa el inicio; sigue disponible con `tareas cita`.

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
la terminal. Para eso último está `tareas tema`, en el apartado siguiente.

## Colores de la terminal

`tareas tema` cambia los colores de **todo** el terminal (fondo, texto, cursor
y los 16 colores ANSI), no solo el del menú. Trae seis temas:

| Tema | Aspecto |
|---|---|
| `medianoche` | Azules oscuros, cómodo de noche |
| `matrix` | Verde sobre negro, tipo consola antigua |
| `papel` | Claro, tipo folio, para trabajar de día |
| `ambar` | Naranjas de fósforo, contraste suave |
| `oceano` | Azules y turquesas, tono frío |
| `contraste` | Negro y blanco puros, para verlo todo |

```bash
tareas tema                     # tabla con los seis y el elegido
tareas tema --ver matrix        # vista previa, sin aplicar ni guardar
tareas tema matrix              # lo aplica a esta sesión y lo recuerda
tareas tema --restablecer       # vuelve a los colores originales
```

Sin argumentos no toca nada: solo enseña la tabla con una muestra de cada tema.

### Un tema propio

`--crear` copia los 16 colores de un tema existente y cambia fondo, texto y
cursor:

```bash
tareas tema --crear mi-tema --desde oceano \
  --fondo "#001018" --texto "#c8f0ff" --cursor "#22d3ee"
tareas tema --ver mi-tema
tareas tema mi-tema
```

El nombre admite letras sin tilde, números, guion y guion bajo (hasta 24
caracteres). Los colores se escriben en hexadecimal de seis dígitos; si no,
la orden sale con **código 2** y lo explica.

Los temas propios se guardan en `ajustes.json`, dentro de la carpeta de
configuración del sistema:

- Windows: `%APPDATA%\tareas\ajustes.json`
- Linux y macOS: `~/.config/tareas/ajustes.json`

Si el fichero no existe o está roto, se empieza de cero sin avisar y sin
perder nada más. El tema elegido se vuelve a aplicar al abrir el menú de
`tareas`.

### Para que dure: exportar

Una secuencia de escape solo dura la sesión. Para dejarlo puesto siempre hay
que importar el tema en el emulador:

```bash
tareas tema --exportar matrix
tareas tema --exportar matrix --destino ~/Escritorio/temas
```

Genera tres ficheros con el nombre del tema:

- `tareas-matrix-windows-terminal.json`: el objeto se pega dentro de
  `"schemes"` en el `settings.json` de Windows Terminal y luego se elige en el
  perfil.
- `tareas-matrix.itermcolors`: se importa en iTerm2 desde
  *Profiles → Colors → Color Presets → Import*.
- `tareas-matrix-gnome.sh`: se ejecuta una vez con `sh` en GNOME Terminal,
  Tilix o Xfce y cambia el perfil por `gsettings`.

### Hasta dónde llega

Funciona en Windows Terminal (fondo y colores, según versión), iTerm2, kitty,
WezTerm, Alacritty, VS Code y GNOME Terminal/Tilix. En la consola clásica de
Windows (`conhost`) y en `TERM=dumb` no se puede: la orden lo dice, explica el
motivo y recuerda `--exportar` en vez de fallar en silencio. Dentro de tmux o
screen tampoco, porque el multiplexor se queda las secuencias.

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

## Organizar una carpeta

`tareas organizar` mueve los ficheros del primer nivel de una carpeta a
subcarpetas según su tipo: `Documentos`, `Imagenes`, `Videos`, `Audio`,
`Comprimidos`, `Instaladores` y `Otros`.

```bash
tareas organizar ~/Descargas --simular
tareas organizar ~/Descargas
tareas organizar ~/Descargas --copiar
```

- Por defecto **mueve**; con `--copiar` deja el original y crea una copia
  clasificada.
- `--simular` enseña la tabla con el destino de cada fichero sin tocar nada.
- Nunca sobrescribe: si el destino existe, añade ` (1)`, ` (2)`…
- No entra en subcarpetas (las que crea él incluidas) ni toca ficheros
  ocultos como `.env`.
- Si un fichero falla, la orden sigue con los demás y sale con código 1.

## Mover un fichero concreto

`tareas mover` lleva **un fichero** de donde esté a la carpeta que le indiques.
No clasifica ni filtra por extensión: tú eliges el archivo y el destino.

```bash
tareas mover ~/Descargas/apuntes.pdf ~/Documentos
tareas mover apuntes.pdf ~/Documentos
tareas mover apuntes.pdf ~/Documentos --simular
tareas mover apuntes.pdf ~/Documentos --copiar
```

- Si solo escribes el nombre, lo busca en la carpeta actual y, si no está, en
  Descargas (`Descargas`, `Downloads`, `Baixades`).
- `~/Documentos` funciona también en un Windows en inglés: se traduce a
  `~/Documents`.
- Si la carpeta destino no existe, la crea.
- Nunca sobrescribe: si el nombre ya está ocupado, usa `apuntes (1).pdf`.
- `--simular` enseña la tabla sin tocar nada y `--copiar` deja el original.
- Una carpeta no se mueve con esta orden: para ordenar carpetas está
  `tareas organizar`.

## Historial y deshacer

Cada orden que cambia ficheros apunta un lote en `historial.jsonl`, dentro de
la misma carpeta de configuración que los temas (`~/.config/tareas` en Linux).
Así puedes ver qué se hizo y revertir lo último sin buscar a mano.

```bash
tareas historial
tareas historial --n 5
tareas deshacer --simular
tareas deshacer
```

`tareas historial` muestra los últimos 10 lotes (fecha, orden, número de
operaciones y si se pueden deshacer). `tareas deshacer` revierte el último
lote en orden inverso:

- `mover`, `organizar`, `ejecutar` con `mover`/`clasificar` y los renombrados
  vuelven a su ruta original.
- Las copias de `mover --copiar`, `organizar --copiar`, `imagenes --comprimir`
  y los ficheros creados con `resumir` se mandan a la papelera del sistema.
- Si el origen ya existe o el destino desapareció, ese fichero se salta y se
  explica el motivo; nunca se sobrescribe nada.
- `capturas`, `temporales` y la acción `borrar` también se apuntan, pero
  `deshacer` avisa de que no se pueden revertir desde aquí (la papelera del
  sistema no se restaura de forma portable). Si el último lote es de ese tipo,
  lo salta y revierte el lote reversible más reciente, diciendo cuántos ha
  saltado.
- Las simulaciones no se apuntan. El historial guarda rutas absolutas, así que
  `deshacer` funciona aunque lo lances desde otra carpeta.

Si un lote solo tiene operaciones imposibles de deshacer, `deshacer` sale con
código 1 y lo deja en el historial para que sepas qué pasó. Cuando revierte
algo, elimina ese lote del historial y el siguiente `deshacer` va al anterior.

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

## Buscar ficheros por nombre

`tareas buscar <texto>` recorre recursivamente una carpeta y lista los ficheros
cuyo nombre encaja. No escribe ni borra nada: solo lee nombres.

```bash
tareas buscar apuntes                     # subcadena en ~/Descargas
tareas buscar factura --ext pdf --ext jpg # filtra por extensión
tareas buscar foto --en ~/Imágenes        # otra carpeta raíz
tareas buscar "IMG_[0-9]+\.jpg" --regex   # expresión regular
```

- Sin `--en`, busca en la carpeta de descargas de tu sistema.
- El texto sin comodines se comporta como subcadena; si lleva `*?[` se trata
  como un *glob* (por ejemplo `IMG_*.jpg`). Con `--regex` se interpreta como
  expresión regular.
- `--ext` se puede repetir (`--ext pdf --ext jpg`) y acepta `pdf` o `.pdf`.
- Omite `.git`, `__pycache__`, `.venv` y `node_modules`.
- Si hay más de 200 coincidencias, corta y avisa.

No falla si no encuentra nada: dice «Sin resultados para «…» dentro de «…»».

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

`acciones.json` no se empaqueta con la instalación: el instalador copia una
plantilla a `~/acciones.json`, que es la segunda ruta que buscan las órdenes que
lo necesitan (`validar`, `acciones`, `ejecutar`, `doctor`) cuando no hay
`./acciones.json` ni les pasas `--config`. `version`, `hola`, `sistema` y
`comprobar-ia` no lo necesitan.

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
├── instalar.ps1               Instalación en un solo comando (Windows)
├── instalar.sh                Ídem, para macOS y Linux
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
│       ├── 0002-ia-interfaz-y-salida-4.md
│       └── 0003-temas-de-terminal.md
├── tests/                     Suite con pytest (238 en verde)
└── src/
    └── tareas/
        ├── __init__.py        Versión y salida en UTF-8
        ├── __main__.py        python -m tareas
        ├── acciones.py        Resultado, destino_libre y las acciones con IA
        ├── ajustes.py         Preferencias guardadas (tema elegido)
        ├── bienvenida.py      Banner ASCII de bienvenida
        ├── buscar.py          Busca ficheros por nombre de forma recursiva
        ├── capturas.py        Detecta capturas y las manda a la papelera
        ├── chuleta.py         Chuleta de Git y comandos de Linux
        ├── cli.py             Órdenes, opciones y salida
        ├── config.py          Carga y valida acciones.json
        ├── doctor.py          Diagnóstico de solo lectura del entorno
        ├── errores.py         Excepciones propias y códigos de salida
        ├── exportar_tema.py   Esquemas de terminal para cada tema
        ├── ia.py              ProveedorIA y ProveedorCentro (httpx, .env)
        ├── imagenes.py        Comprime imágenes sin tocar los originales
        ├── informe.py         Cuenta ficheros, tipos y capturas pendientes
        ├── menu.py            Menú interactivo de todas las órdenes
        ├── motor.py           Selecciona ficheros y ejecuta la acción
        ├── mover.py           Lleva un fichero concreto a otra carpeta
        ├── organizar.py       Ordena una carpeta en subcarpetas por tipo
        ├── rutas.py           Carpetas habituales del sistema en varios idiomas
        ├── sistema.py         Disco y memoria en uso
        ├── temporales.py      Detecta temporales antiguos y los manda a la papelera
        └── terminal.py        Temas de color para la terminal
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

### Compromiso: cero claves en el repositorio

Requisito cumplido: **no hay ninguna clave ni secreto ni en el repositorio ni
en su historial**. Así se garantiza y así se comprueba:

- La clave vive **solo** en mi máquina: en el `.env` local (excluido por
  `.gitignore`) o exportada como variable de entorno (`CENTRO_IA_KEY`).
- El repo solo publica `.env.example`, que es la plantilla con los nombres de
  variable y **ningún valor**.
- En el código no hay claves literales: las pruebas usan un proveedor falso
  con el valor inventado `sk-test-falsa`, que no abre ninguna conexión.
- El historial está auditado con `git log --all -S"sk-"` y `git grep -E
  "sk-[A-Za-z0-9]{15,}" $(git rev-list --all)`: **cero coincidencias** de
  claves reales en ningún commit ni rama.
- Si el proyecto crece, se puede añadir un análisis automático de secretos en
  CI (por ejemplo, `gitleaks`); por ahora la comprobación manual de arriba
  basta y no instala nada en tu equipo.

## Estado de la bienvenida

- `tareas hola` y el ejecutable directo `hola` muestran el banner ASCII.
- El mensaje «Bienvenido a mi terminal personalizado» aparece centrado.
- Funciona sin `acciones.json` y no modifica ningún fichero.
- Comprobado desde cualquier carpeta, también con la instalación global.

## Estado del menú interactivo

- `tareas` sin argumentos abre el panel de mando; `tareas --help` sigue mostrando la ayuda completa.
- El panel cabe en 80×24: cabecera con la versión, «Empieza por aquí» (`1`-`3`), categorías, seguridad/IA y un consejo.
- `1`, `2` y `3` ejecutan `informe`, `organizar --simular` e `historial`.
- Las categorías se generan desde Typer; una orden nueva sin clasificar aparece en **OTRAS**.
- `cambio` recolorea títulos, rayas y bordes; `cambio normal` lo restaura.
- `salir`, `exit`, `quit` y `q` cierran el menú; `ayuda` y `?` muestran la ayuda.
- También acepta el prefijo `tareas`, por ejemplo `tareas version`.
- Las órdenes nuevas aparecen en el menú automáticamente.
- Probado con entrada por tubería (`printf 'version\nsalir\n' | tareas`) y sin entrada.
- `tests/test_menu.py` comprueba anchos de 60, 80 y 120, los atajos, las categorías y que ninguna orden se repita.

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

## Estado de la orden temporales

Comprobado en `~/pruebas-tareas/estado-semana/temporales` con 8 ficheros de
prueba (todos de 40 días salvo uno):

- `--simular` enseña los 5 que cumplen y no envía nada a la papelera:
  `.DS_Store`, `Thumbs.db`, `respaldo.txt~`, `~$informe.docx` y `viejo.tmp`.
  Código 0.
- Se quedan fuera `reciente.tmp` (modificado hoy), `notas.txt` (no es un
  fichero temporal) y `sub/viejo.tmp` (está en una subcarpeta).
- Sin `--si` pregunta «¿Enviar 5 ficheros temporales a la papelera?»; si se
  responde que no, no toca nada y sale con **código 1**.
- `--dias 10` selecciona los mismos 5, porque todos pasan de 40 días.
  `--dias 0` o negativo es error de uso: «debe ser 1 o más», **código 2**.
- Carpeta inexistente o que en realidad es un fichero: mensaje humano,
  **código 1**, sin traceback.
- Carpeta vacía: «No hay ficheros temporales con al menos 30 días…»,
  **código 0**.
- Usa `send2trash`, la papelera del sistema: nada se borra de forma
  definitiva y se puede recuperar.

## Estado de comprimir imágenes

Comprobado en `~/pruebas-tareas/estado-semana/imagenes` (4 imágenes
compatibles, un GIF animado y un `.txt`) y en `estado-semana/animadas` (una
WebP animada y un PNG con contenido JPEG dentro):

- `--simular` lista las 4 imágenes (`.jpg` y `.png`) con su destino y estado
  «simulado», y no crea la carpeta `comprimidas` ni escribe un solo fichero.
  En la simulación la columna Final sale «—»: no abre las imágenes, así que
  tampoco promete un ahorro que luego no se cumpla. Código 0.
- Compresión real con la calidad por defecto (75): `foto.jpg` pasa de
  624.6 KB a 265.7 KB (57 % menos) y `logo.png` de 591 B a 470 B.
  `dibujo.png` y `pixel.png` salen **saltadas** («no reduce el tamaño») y no
  dejan copia en el destino.
- `--webp` convierte las 4: `dibujo.png` de 1.5 MB a 330.8 KB (79 % menos) y
  `pixel.png` de 69 B a 44 B. Las copias se guardan como `.webp` en
  `comprimidas`.
- Los originales quedan intactos después de las dos órdenes: mismo tamaño y
  misma fecha de modificación (comprobado antes y después).
- El GIF animado y `nota.txt` no aparecen en la tabla. Una `.webp` animada o un
  `.png` que en realidad contiene un JPEG sí se listan, pero al comprimir
  acaban en **error** con su motivo («es animada; se omite», «no coincide con
  su extensión (contiene JPEG)»), no dejan copia y la orden sale con
  **código 1**.
- `--calidad 0` o mayor de 95 es error de uso con **código 2**; carpeta
  inexistente, **código 1**; carpeta sin imágenes compatibles, «No hay
  imágenes compatibles…» y **código 0**.

## Estado de `tareas doctor`

- Tabla ✔/ℹ/⚠/✘ de config, dependencias, descargas, orígenes, IA y `~/pruebas-tareas`.
- Sin tocar disco: solo lectura; ninguna creación, borrado ni escritura.
- JSON roto con `--config` → ✘ con el motivo exacto (línea y columna) y código 3.
- Config válida con avisos → resumen amarillo y código 0.
- Los orígenes se traducen: si `~/Descargas` no existe pero sí `~/Downloads`
  (Windows en inglés) o `~/Baixades` (en valenciano), la acción cuenta como ✔.
  Igual con `~/Imágenes/Capturas` → `~/Pictures/Screenshots` o
  `~/Imatges/Captures de pantalla`. Así el mismo `acciones.json` vale en casa y
  en clase.
- La IA sin `CENTRO_IA_KEY`/`CENTRO_IA_URL` sale como ℹ «sin configurar», no
  como aviso: fuera del centro es lo normal y `tareas ia …` sigue saliendo con
  código 4 si se usa.

## Estado de la semana 3

La semana 3 fue la capa de IA de acciones. El diseño, las pruebas sin red y
todo lo comprobado están en [Estado de la capa IA](#estado-de-la-capa-ia), y
la decisión del proveedor inyectable y del código 4, en
`docs/adr/0002-ia-interfaz-y-salida-4.md`. Resumen:

- Tres acciones con IA (`resumir-apuntes`, `renombrar-apuntes` y
  `clasificar-apuntes`) que se activan desde `acciones.json`; las otras 5
  siguen funcionando sin red.
- `ProveedorIA` como interfaz: `ProveedorCentro` (httpx) en el equipo y un
  proveedor falso en las pruebas, así la suite no gasta ni un token.
- Sin clave o sin red: **código 4**, mensaje humano y ningún fichero tocado.
- `--simular` calcula caracteres y tokens por fichero sin preguntar al modelo.
- 21 pruebas de esta capa sin red ni claves (`tests/test_ia.py`), dentro de
  los 68 de la semana 4.
- Pendiente: probar las tres acciones contra el servidor real del centro
  desde la red del instituto.

Las órdenes de ficheros de estas semanas (`capturas`, `temporales`, `informe`,
`doctor` e `imagenes`) tienen su estado comprobado en las secciones anteriores.

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
- Salida en UTF-8 desde el arranque (`src/tareas/__init__.py`): en Windows
  la salida va en cp1252 y el `✔` de `validar` o el banner de `hola`
  reventaban con `UnicodeEncodeError` (sobre todo con la salida redirigida
  a un fichero o a un tubo, que es como trabajan los tests). Ahora se
  reconfiguran `stdout` y `stderr` a UTF-8 con `errors="replace"` y todo
  escribe igual en Linux, Windows y macOS.
- Para probar la capa IA existe `~/pruebas-tareas` con `Apuntes` (2 `.txt`
  de ejemplo), `Resúmenes` y `Clasificados`: con `--simular`, las tres
  acciones de IA encuentran los 2 apuntes y salen 0.

`uv.lock` ya incluye `httpx`, `python-dotenv` y `pypdf`. Queda pendiente
probar las tres acciones contra el servidor real del centro desde la red del
instituto.

## Estado de la semana 4

Pruebas automáticas y release 1.0.0:

- **237 tests en verde** con `uv run pytest -q`, todos en carpetas temporales
  y sin red.
  - `tests/conftest.py`: fixture `aislado` (autouse) con `tmp_path`, `HOME`,
    `USERPROFILE` y sin las variables del centro; `descargas` con ficheros
    feos, `escribir_config` y `ProveedorFalso`.
  - `tests/test_config.py` (12): `parametrize` con tipo inexistente, destino
    vacío, sin descripción y regex rota; nombre repetido y JSON roto.
  - `tests/test_acciones.py` (23): mover, `--simular` que no crea ni la
    carpeta, nunca sobrescribir, `.JPG` en mayúsculas, borrar solo lo viejo y
    renombrar con plantilla.
  - `tests/test_ia.py` (21): `a_nombre_seguro` (tildes, ruta peligrosa,
    extensión duplicada y respuesta vacía), resumen y clasificación con
    `ProveedorFalso`, sin clave y sin red.
  - `tests/test_cli.py` (7): `CliRunner` con los códigos de salida 0, 1, 2,
    3 y 4.
  - `tests/test_buscar.py` (12): subcadena, glob, `--regex`, extensión
    normalizada, carpetas omitidas (`.git`, `.venv`…), orden por fecha y
    errores humanos de carpeta, regex y extensión.
- Mutación comprobada: sacar el `mkdir` de `Mover` fuera del
  `if not simular` pone en rojo `test_simular_no_toca_el_disco`
  (1 failed, 67 passed); después se restauró el código.
- GitHub Actions (`.github/workflows/pruebas.yml`): `uv run pytest -v` en
  Ubuntu, Windows y macOS en cada push y pull request.
- Versión **1.0.0** en `pyproject.toml` y `src/tareas/__init__.py`,
  `CHANGELOG.md` para quien usa la herramienta y README con la instalación
  en una orden y la desinstalación.
- `scripts/revisar.sh`: el diff preparado se revisa con
  `opencode run --agent revisor`, con `timeout 180` y veredicto convertido en
  código de salida (0 si OK, 1 si hay que cambiar).

## Estado de los temas

Comprobado en Windows Terminal con una carpeta de configuración temporal
(`TAREAS_CONFIG`), para no tocar los ajustes de verdad:

- `tareas tema` enseña la tabla con los seis temas (`medianoche`, `matrix`,
  `papel`, `ambar`, `oceano` y `contraste`) y sale con **código 0**. No cambia
  ningún color ni escribe ajustes.
- `tareas tema --ver matrix` pinta la vista previa y **no crea**
  `ajustes.json`; código 0.
- `tareas tema matrix` manda por la salida estándar `OSC 11` (fondo
  `rgb:05/08/05`), `OSC 10` (texto `rgb:b9/ff/b3`), `OSC 12` (cursor
  `rgb:00/ff/66`) y **16 secuencias `OSC 4`**, una por color ANSI. Después
  guarda `{"version": 1, "tema": "matrix"}` en `ajustes.json`; código 0.
- `tareas tema --exportar papel --destino …` deja los tres ficheros y se
  pueden leer con sus herramientas: el JSON de Windows Terminal tiene **20
  claves** (`name`, `background`, `foreground`, `cursorColor` y los 16
  colores), el `.itermcolors` se abre con `plistlib` y tiene **19 claves**, y
  el script de GNOME lleva **6 `gsettings set`** y los **16 colores**; código 0.
- `tareas tema --crear "con espacios" …`, un color que no es hex o `--crear`
  sin los tres colores salen con **código 2** y explican qué falta, sin
  traceback.
- `tareas tema neon` sale con **código 1** y el mensaje nombra los temas que
  hay, incluidos los propios.
- `tareas tema --restablecer` manda `OSC 104`, `110`, `111` y `112` y deja el
  tema guardado vacío, así que el menú ya no lo reaplica; código 0.
- Con `TERM=dumb` (y sin `WT_SESSION`) avisa de que el terminal no admite
  cambiar los colores, recuerda `--exportar` y **no guarda** el tema; código 0.
- En el resto de terminales la detección se prueba con entornos simulados
  (`WT_SESSION`, `TERM_PROGRAM`, `VTE_VERSION`, `KITTY_WINDOW_ID`, `TMUX` y
  `TERM`), sin depender del equipo donde se ejecuten las pruebas.

## Estado de `organizar` y `mover`

Comprobado en carpetas temporales de `%TEMP%`, nunca sobre carpetas reales:

- `tareas organizar <carpeta> --simular` enseña la tabla con los 5 ficheros en
  estado «simulado» y no crea ninguna carpeta de categoría; código 0.
- `tareas organizar <carpeta>` mueve esos 5 ficheros a `Documentos`,
  `Imagenes`, `Videos`, `Comprimidos` y `Otros`. El `.env` se queda donde
  estaba y un `apuntes.pdf` que ya existía en `Documentos` no se pisa: aparece
  `apuntes (1).pdf`. Código 0.
- `--copiar` deja el original y crea la copia clasificada.
- `tareas organizar` con una carpeta que no existe sale con **código 1** y un
  mensaje claro, sin traceback.
- `tareas mover <archivo> <carpeta>` mueve un solo fichero y crea la carpeta
  destino si no existe; código 0.
- Si solo se escribe el nombre, lo busca primero en la carpeta actual y
  después en Descargas (`Descargas`, `Downloads`, `Baixades`).
- `--simular` no toca nada, `--copiar` deja el original y, si el nombre ya
  existe en destino, se usa `apuntes (1).pdf`: nunca se sobrescribe.
- Fichero inexistente, fichero que ya está en esa carpeta, o un destino que es
  un fichero y no una carpeta: **código 1** con el motivo. Si lo que se pasa es
  una carpeta, se rechaza y se remite a `tareas organizar`.
- Todo esto está cubierto por `tests/test_organizar.py` y
  `tests/test_mover.py`, más los casos de CLI de `tests/test_cli.py`.

## Estado de `tareas buscar`

Comprobado sobre carpetas del propio repo (solo lectura) y en carpetas
temporales con pytest; nunca se toca el disco salvo para leer nombres:

- `tareas buscar README --en ~/Documents/CLI-TAREASJAVIER`: encuentra el
  `README.md` y lo saca en tabla con tamaño y fecha; código 0.
- Sin `--en`, busca en la carpeta de descargas (en esta máquina, `~/Baixades`)
  y, si no hay nada, dice «Sin resultados para…» con **código 0**: no es un
  error, es que no estaba ahí.
- Con `--ext` la extensión se normaliza: `pdf` y `.pdf` valen, mayúsculas
  incluidas; se puede repetir (`--ext pdf --ext jpg`).
- Con `--regex`, el texto se trata como expresión regular (`test_.*\.py`);
  una expresión rota sale con **código 1** y el motivo, sin traceback.
- El texto sin comodines busca como subcadena; si lleva `*?[` se comporta
  como glob.
- Omite `.git`, `__pycache__`, `.venv` y `node_modules` para no llenar la
  tabla de basura.
- Carpeta que no existe (`--en /ruta/inventada`) y texto vacío: **código 1**
  con mensaje claro.
- Más de 200 coincidencias: corta y lo avisa en el pie.
- 12 pruebas automáticas en `tests/test_buscar.py` (subcadena, glob, regex,
  extensión, carpetas omitidas, orden por fecha y todos los errores).
