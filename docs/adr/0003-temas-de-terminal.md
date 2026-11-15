# ADR-0003: Los temas de terminal se aplican con OSC y se exportan para durar

- Estado: aceptada
- Fecha: 2026-11-15
- Autor: Javier Sansano

## Contexto

`tareas cambio` solo pinta el menú interactivo con otro color de Rich, y solo
mientras dura esa ejecución. Lo que se pedía era cambiar los colores del
**terminal** de verdad, con varias opciones y posibilidad de personalizarlo.

El problema es que un programa no es dueño del tema de la terminal: el tema
vive en la configuración del emulador (Windows Terminal, iTerm2, GNOME
Terminal, kitty, Alacritty…), y cada uno lo guarda en un formato distinto. Un
programa solo puede:

1. Mandar secuencias de escape **OSC** que cambian los colores de la sesión
   actual (`OSC 10` texto, `OSC 11` fondo, `OSC 12` cursor, `OSC 4` los 16
   colores ANSI).
2. Generar un fichero que el usuario importe en su emulador.
3. Escribir directamente en la configuración del emulador.

La tercera opción depende de la versión y de la ruta de cada terminal, puede
romper la configuración del usuario y no se puede probar en los tres sistemas.
La consola clásica de Windows (`conhost`) no admite OSC; tmux y screen se
quedan las secuencias.

## Decisión

1. **Un módulo sin efectos, `terminal.py`**, con las paletas y funciones que
   **devuelven** el texto de las secuencias: `aplicar()`, `restablecer()`,
   `secuencia_fondo()`… Así se pueden probar sin abrir un terminal.
2. **Aplicar por OSC solo a la sesión actual**, avisando cuando el terminal no
   lo admite (`detectar()` mira `WT_SESSION`, `TERM_PROGRAM`, `VTE_VERSION`,
   `KITTY_WINDOW_ID`, `TMUX` y `TERM`) en vez de fallar en silencio.
3. **Exportar para que dure**: `exportar_tema.py` genera el esquema JSON de
   Windows Terminal, el `.itermcolors` de iTerm2 y un script de `gsettings`
   para GNOME Terminal/Tilix. La herramienta **no** toca la configuración de
   nadie.
4. **Guardar solo lo mínimo** en `ajustes.json` (`%APPDATA%\tareas` en
   Windows, `~/.config/tareas` en el resto): el tema elegido y los temas
   propios. Si el fichero falta o está roto, se empieza de cero.
5. **Reaplicar el tema al abrir el menú**, no en cada orden: así `tareas
   version` o una salida redirigida a un fichero no se llenan de secuencias.
6. **`cambio` se queda** con su comportamiento (color del menú) y apunta a
   `tema` en la documentación. Nada de lo que ya existía cambia de nombre.

## Alternativas consideradas

1. Editar el `settings.json` de Windows Terminal automáticamente.
   - A favor: el cambio quedaría puesto sin pasos manuales.
   - En contra: puede romper la configuración, depende de la versión y de la
     ruta, y solo cubre Windows; en Linux y macOS habría que hacer lo mismo con
     `gsettings` y con plists. Demasiado riesgo para lo que aporta.
2. Cambiar solo el color del menú y llamarlo «tema».
   - A favor: cero riesgo y cero código nuevo.
   - En contra: no es lo que se pidió; el fondo y el texto del terminal siguen
     igual.
3. Temas definidos en un fichero JSON de configuración en vez de en código.
   - A favor: se podrían añadir temas sin tocar Python.
   - En contra: hay que validar el fichero, y un tema mal escrito dejaría la
     terminal ilegible. Los seis de fábrica se revisan mejor en una prueba.
4. Un tema por variable de entorno (`TAREAS_TEMA`).
   - A favor: sin fichero de ajustes.
   - En contra: no se recuerda solo y complica el uso normal.

## Consecuencias

- Positivas: seis temas probados, uno propio con validación de colores, aviso
  claro cuando el terminal no admite OSC, y un camino fiable (`--exportar`)
  para que el cambio sea permanente en los tres sistemas.
- Negativas: dentro de tmux/screen y en `conhost` solo funciona exportando; en
  Windows Terminal el cambio de fondo depende de la versión; y un tema propio
  copia los 16 colores de otro (no se editan uno a uno desde la CLI).
- Qué haré si el formato de algún terminal cambia: los exportadores están
  aislados en `exportar_tema.py` y sus pruebas leen el resultado con
  `json`/`plistlib`, así que un formato nuevo es una función más.
