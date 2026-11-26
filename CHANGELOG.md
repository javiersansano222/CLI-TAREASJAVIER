# Changelog

Todos los cambios que notará quien USA la herramienta. Formato:
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · versiones:
[SemVer](https://semver.org/lang/es/).

## [No publicado]

## [1.2.0] - 2026-11-26

### Añadido

- `tareas buscar <texto>`: busca ficheros por nombre de forma recursiva y los
  lista en una tabla con tamaño y fecha. Sin `--en`, busca en la carpeta de
  descargas; `--ext` (repetible) filtra por extensión, `--regex` trata el texto
  como expresión regular y omite `.git`, `__pycache__`, `.venv` y
  `node_modules`. Si pasa de 200 coincidencias, corta y avisa. Solo lee.
- Nuevas opciones `--config` para `doctor`: la ruta de búsqueda por defecto es
  `./acciones.json` y, si no existe, `~/acciones.json`, donde el instalador
  copia la plantilla. El mensaje de error explica qué hacer.
- README: sección «Buscar ficheros por nombre» y sección «Diagnóstico del
  entorno» actualizadas con el orden de búsqueda y ejemplos copiables en
  Windows (PowerShell) y Linux/macOS.
- `tareas historial`: muestra los últimos lotes de operaciones con su fecha,
  la orden que los produjo y si se pueden deshacer. Se guarda en
  `historial.jsonl`, junto a los ajustes, y las simulaciones no se apuntan.
- `tareas deshacer`: revierte el último lote. Devuelve a su sitio los ficheros
  movidos, renombrados u organizados y manda a la papelera las copias y los
  ficheros creados (`imagenes --comprimir`, `resumir`). Avisa de lo que no se
  puede revertir (`capturas`, `temporales`, `borrar`) sin perder el lote.
  Con `--simular` enseña qué haría sin tocar nada. Guarda rutas absolutas, así
  que funciona aunque se lance desde otra carpeta.

### Cambiado

- `tareas buscar` recorre las carpetas con `os.scandir` en vez de `rglob`:
  no baja de las carpetas omitidas (`.git`, `node_modules`, `__pycache__`,
  entornos virtuales) y salta enlaces simbólicos, así no se enreda si alguno
  apunta a una carpeta madre. Los resultados no cambian.
- `mover`, `organizar`, `capturas`, `temporales`, `imagenes` y `ejecutar`
  apuntan automáticamente sus operaciones en el historial.
- README: la instalación «Solo para usar la terminal» va paso a paso (instalar
  `curl` si falta, instalar `uv`, cargarlo con `source ~/.local/bin/env`,
  instalar desde el `.tar.gz` sin necesitar `git` y dejarlo en el PATH), con el
  caso de Windows aparte.
- El menú de inicio es ahora un panel de mando: cabecera con la versión,
  bloque «Empieza por aquí» con los atajos `1`, `2` y `3`, categorías
  generadas desde Typer (con **OTRAS** para las órdenes nuevas), seguridad e
  IA en una línea y un consejo en lugar de la cita. Cabe en una pantalla y ya
  no repite la lista de órdenes. En pantallas anchas los paneles no pasan de 84
  columnas, y por debajo de 80 se muestra una línea por categoría.

### Corregido

- `mirar-espacio` mide la carpeta una sola vez: antes repetía el mismo total
  en una fila por cada fichero, lo que hacía la salida confusa.
- La excepción `IANoDisponible` ya no está duplicada en `ia.py`: hay una sola
  en `errores.py`, así el mismo código de salida 4 y el mismo consejo valen
  para la IA de las acciones y para `comprobar-ia`.
- README: aviso de que, si `tareas` se instaló desde la carpeta del repositorio
  sin `--editable`, los cambios de código no se ven hasta
  `uv tool install --reinstall .`.
- `instalar.ps1` se guarda sin BOM y en ASCII puro: `irm … | iex` ya no falla
  en la primera línea y `-File` funciona igual en PowerShell 5.1 y 7. Al
  terminar recuerda cómo usar `tareas` en la ventana actual y que hay que
  cerrar todas las ventanas tras cambiar el PATH.
- README: la solución de Windows explica el PATH paso a paso (`Test-Path`,
  `$env:Path`, `uv tool update-shell` y cerrar todas las ventanas), y aclara
  que la orden es `tareas version`.

## [1.1.0] - 2026-11-20

### Añadido

- `tareas mover <archivo> <carpeta>`: mueve un fichero concreto a la carpeta
  que elijas. Si solo das el nombre, lo busca en la carpeta actual y en
  Descargas; si la carpeta destino no existe, la crea; nunca sobrescribe. Con
  `--simular` no toca nada y con `--copiar` deja el original.
- `tareas organizar <carpeta>`: mueve los ficheros del primer nivel a
  `Documentos`, `Imagenes`, `Videos`, `Audio`, `Comprimidos`, `Instaladores` y
  `Otros` según su extensión. Con `--simular` no toca nada y con `--copiar`
  deja el original. Nunca sobrescribe y no entra en subcarpetas.
- `tareas tema`: cambia los colores de toda la terminal (fondo, texto, cursor y
  los 16 colores ANSI), no solo el del menú. Seis temas: `medianoche`,
  `matrix`, `papel`, `ambar`, `oceano` y `contraste`.
- `tareas tema --ver <tema>`: vista previa sin aplicar ni guardar nada.
- `tareas tema --crear <nombre> --fondo … --texto … --cursor …`: tema propio a
  partir de los 16 colores de otro, con los colores en hexadecimal.
- `tareas tema --exportar <tema>`: genera el esquema de Windows Terminal, el
  `.itermcolors` de iTerm2 y un script de `gsettings` para GNOME Terminal, para
  que el cambio dure aunque se cierre la terminal.
- `tareas tema --restablecer`: vuelve a los colores originales y olvida el tema
  guardado.
- El tema elegido se recuerda en `ajustes.json` y se vuelve a aplicar al abrir
  el menú. Si el terminal no admite cambiar los colores, se avisa y se explica
  cómo exportarlo.

### Cambiado

- El README explica los temas, sus límites por terminal y cómo importarlos.
- `tareas doctor` traduce las carpetas personales: `~/Descargas` funciona
  aunque el sistema las llame `~/Downloads` (inglés) o `~/Baixades`
  (valenciano), y `~/Imágenes/Capturas` aunque sean `~/Pictures/Screenshots` o
  `~/Imatges/Captures de pantalla`. Lo mismo al ejecutar acciones.
- La IA sin configurar sale en `doctor` como ℹ «sin configurar» y ya no cuenta
  como aviso: fuera de la red del centro es lo esperado.

## [1.0.0] - 2026-11-19

### Añadido

- Acciones con IA: `resumir`, `renombrar-ia` y `clasificar`, con los modelos
  del centro. Cada acción se activa desde `acciones.json`, sin tocar el código.
- `tareas comprobar-ia`: dice si hay IA disponible y sale con código 4 si no
  la hay.
- `--simular` en las acciones con IA: dice cuántos caracteres se mandarían y
  cuántos tokens costaría, sin gastar ninguno.
- `.env.example` con las variables necesarias (`CENTRO_IA_URL`,
  `CENTRO_IA_KEY` y `CENTRO_IA_CA`), sin ninguna clave dentro.
- Instalación en un solo comando con `instalar.ps1` (Windows) e `instalar.sh`
  (macOS/Linux), y ficheros de acciones con rutas de cada sistema
  (`acciones-win.json`, `acciones-mac.json`).
- Pruebas automáticas de config, acciones, IA y CLI, ejecutadas en Linux,
  Windows y macOS en cada push.

### Cambiado

- `clasificar` no inventa categorías: si el modelo no elige una de las que
  hay en `categorias`, el fichero se salta y se explica el motivo en la
  columna Detalle.
- Los errores de uso, configuración y falta de IA salen con los códigos 1,
  2, 3 y 4, con un mensaje humano y sin traceback.
- Sin clave o sin red, la CLI lo explica y el resto de órdenes sigue
  funcionando igual.

### Arreglado

- `renombrar-ia` ya no duplica la extensión si el modelo la añade. El nombre
  base se limpia y la extensión original se añade una sola vez: si el modelo
  responde `redes-ip-protocolos.pdf`, el fichero queda como
  `redes-ip-protocolos.pdf`, no como `redes-ip-protocolos.pdf.pdf`.
