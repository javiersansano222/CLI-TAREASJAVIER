# Guía de defensa de «tareas»

Este documento sirve para preparar la defensa oral. Está ordenado para que lo
leas una vez de arriba abajo y luego uses el guion de demo y el bloque de
preguntas como repaso rápido.

La idea que hay que transmitir en una frase:

> «tareas» automatiza tareas repetitivas con ficheros desde la terminal; las
> acciones no están en el código sino en un `acciones.json` validado, la IA es
> opcional y sin clave o sin red la herramienta sigue funcionando.

---

## 1. Guion de demo (5-7 minutos)

Todo lo que se enseña se puede ejecutar delante del profesor. Usa una carpeta
de pruebas, nunca tus carpetas reales.

```bash
# 0. Preparar una caja de arena (no toca nada real)
mkdir -p ~/pruebas-tareas/Demo
printf 'a' > ~/pruebas-tareas/Demo/foto1.jpg
printf 'b' > ~/pruebas-tareas/Demo/foto2.PNG
printf 'c' > ~/pruebas-tareas/Demo/viejo.tmp
touch -d '40 days ago' ~/pruebas-tareas/Demo/viejo.tmp
```

### 1.1. Qué hay instalado y qué acciones existen

```bash
tareas version
tareas acciones
tareas --config acciones.json validar
```

Qué decir: «La versión, las 8 acciones que lee del JSON y que el esquema está
validado antes de tocar ningún fichero. `acciones` marca con "sí" las que usan
IA y aclara que el resto funciona sin red.»

### 1.2. Simulación antes de ejecutar

```bash
tareas --config acciones.json ejecutar mover-imagenes --simular
```

Qué decir: «En simulación no se mueve nada: la tabla dice qué fichero iría a
qué destino. Es la red de seguridad antes de cualquier acción.»

Luego ejecuta de verdad sobre una carpeta de pruebas (cambiando `origen` en un
JSON de pruebas o pasando `CARPETA`):

```bash
tareas --config acciones.json ejecutar mover-imagenes ~/pruebas-tareas/Demo
```

### 1.3. Confirmación antes de borrar

```bash
tareas --config acciones.json ejecutar limpiar-temporales ~/pruebas-tareas/Demo
```

Qué decir: «`limpiar-temporales` es de tipo `borrar`, así que pide confirmación
antes de borrar. Con `--simular` solo enseña qué borraría. En el JSON se puede
poner `confirmar: false`, pero por defecto es `true`.»

### 1.4. Historial y deshacer

```bash
tareas historial
tareas deshacer --simular
tareas deshacer
```

Qué decir: «Cada operación que cambia ficheros queda apuntada. `deshacer`
devuelve el último lote; lo que no se puede deshacer (un borrado) se avisa y el
lote se conserva, no se pierde.»

### 1.5. Errores humanos, sin traceback

```bash
tareas --config /tmp/no-existe.json validar          # código 3
tareas --config acciones.json ejecutar inventada      # código 1
tareas listar /carpeta/que/no/existe                  # código 1
env -u CENTRO_IA_KEY -u CENTRO_IA_URL tareas --config acciones.json ejecutar resumir-apuntes   # código 4
echo "codigo: $?"
```

Qué decir: «Ninguno de estos casos ensucia la pantalla con un traceback: cada
uno tiene su código de salida y su mensaje. Sin IA, la CLI lo explica y el
resto de acciones sigue disponible.»

### 1.6. IA (si hay clave y red)

```bash
tareas comprobar-ia
tareas ia sugerir "mueve los PDF de Descargas a Documentos/PDF"
```

Qué decir: «La propuesta de la IA se valida con el mismo validador que
`acciones.json` antes de enseñarla; si no cumple el esquema, no se muestra como
válida. La clave vive en `.env`, que está ignorado por git desde el primer
commit.»

---

## 2. Mapa de la rúbrica: dónde está cada cosa

| Criterio | Evidencia principal | Nivel |
| --- | --- | --- |
| Acciones predefinidas (20) | `acciones.json` con 8 acciones; `--simular`; confirmación en `borrar`; `destino_libre` evita sobrescribir | Excelente |
| Configuración externa (15) | `src/tareas/config.py` (validación completa); esquema en README; `docs/adr/0001-configuracion-externa.md` | Excelente |
| IA y secretos (15) | `src/tareas/ia.py`; `resumir`, `renombrar_ia`, `clasificar`; `.env` en `.gitignore`; `.env.example`; código 4 sin clave/red | Excelente |
| Robustez (15) | `src/tareas/errores.py`; `_mostrar_error` en `cli.py`; códigos 1/2/3/4; `assert` de invariantes | Excelente |
| Diseño en clases/módulos (10) | `cli`, `motor`, `acciones`, `config`, `ia`; fábricas `desde_config` y `desde_entorno` | Excelente |
| Pruebas y calidad (15) | `tests/` (238 casos: 237 en verde y 1 omitida), `pytest`, `.github/workflows/pruebas.yml` en 3 sistemas | Excelente |
| Instalación y proceso (10) | README con `uv tool install`; tag `v1.0.0` con changelog; rama `release-1.0` y PR #2 | Excelente |

---

## 3. Cómo explicar las aserciones

La rúbrica pide que sepas explicar cada aserción. No hace falta recitar las
238: agrupa por idea y ten un ejemplo concreto de cada grupo. La estructura de
respuesta que funciona es:

1. **Qué comprueba** la aserción.
2. **Por qué importa** (qué fallo del usuario o del sistema evita).
3. **Qué se rompería** si se quitara.

### 3.1. Configuración: `tests/test_config.py`

- `test_cargar_acciones_sin_fichero`: `pytest.raises(ConfigError)`.
  Comprueba que un JSON que no existe no revienta con `FileNotFoundError`.
  Importa porque es el error más probable al empezar. Si se quitara, el
  usuario vería un traceback.
- `test_version_invalida`: espera `ConfigError` y que el texto diga «no es
  compatible». Protege el contrato del esquema: una versión futura no se
  ejecuta a ciegas.
- `test_accion_sin_nombre` y `test_accion_repetida_nombre`: esperan
  `AccionNoValida` y que el mensaje contenga «repetido». El motor indexa las
  acciones por nombre; dos nombres iguales harían desaparecer una acción.
- `test_el_error_dice_que_campo_falla` (parametrizado): comprueba
  `error.value.campo == campo`. Es la prueba de que el error no es genérico:
  señala el campo exacto que el usuario escribió mal.
- `test_json_roto_dice_la_linea`: espera `match="línea 1"`. Un JSON roto es un
  caso feo típico; el mensaje da línea y columna, no «error».

### 3.2. Acciones y ficheros: `tests/test_acciones.py`

- `test_simular_no_toca_el_disco`: compara `sorted(descargas.iterdir()) ==
  antes` y `assert not destino.exists()`. Aquí está la promesa de `--simular`:
  ni siquiera se crea la carpeta de destino. Si se quitara, una simulación
  podría dejar basura en disco.
- `test_nunca_sobrescribe`: crea un fichero que ya existe en destino y
  comprueba que el original conserva su contenido y que el nuevo aparece con
  sufijo. Es la prueba de `destino_libre` (`acciones.py:51`): nunca se pierde
  un fichero por colisión de nombres.
- `test_borrar_solo_los_viejos`: comprueba que `viejo.tmp` desaparece y
  `nuevo.tmp` sigue. Valida el filtro `mas_antiguo_que_dias`; sin él, una
  acción destructiva podría borrar de más.
- `test_la_extension_en_mayusculas_cuenta`: `FOTO1.JPG` entra con filtro
  `.jpg`. Evita que el filtro dependa de mayúsculas.
- `test_mover_solo_lo_que_cumple_el_filtro`: compara la lista de nombres del
  destino y los estados `["hecho", "hecho"]`. Comprueba que la acción no se
  aplica a ficheros que no cumplen el filtro.
- `test_renombrar_con_plantilla`: espera `foto-001.png` y `foto-002.jpg`.
  Valida los huecos `{n}` y `{ext}` de la plantilla.
- `test_nombre_seguro_quita_lo_prohibido`: varias aserciones sobre
  `a_nombre_seguro`: quita `/:`, colapsa espacios, recorta a 60, trata `CON`
  como nombre reservado de Windows y devuelve vacío si no queda nada. Es la
  barrera entre «lo que dice la IA» y «un nombre válido en los tres sistemas».
- `test_categoria_con_tildes_y_mayusculas`: `Programación` casa con
  `programacion` y `inventada` devuelve `None`. Evita que la IA cree carpetas
  nuevas por una tilde o una mayúscula.
- `test_presupuesto_sin_gastar`: comprueba que en simulación se enseña
  «1200 caracteres», «300 tokens» y «sin gastar». Es la prueba de que simular
  una acción con IA no gasta tokens.

### 3.3. Motor: `tests/test_motor.py`

- `test_motor_obtener_accion_inexistente`: espera `TareasError` con «no hay
  ninguna acción». El motor no devuelve `None` silencioso: falla con mensaje y
  la CLI lo traduce a código 1.
- `test_motor_seleccionar_sin_filtro` y `..._con_extensiones`: cuentan
  ficheros y comprueban `all(ruta.suffix == ".txt")`. Demuestran que los
  filtros se combinan y que solo se seleccionan ficheros.
- `test_mirar_espacio_resume_la_carpeta_en_una_sola_fila`: `len(resultados) ==
  1` y «3 ficheros» en el detalle. Evita la salida confusa de repetir el total
  una vez por fichero.

### 3.4. CLI y códigos de salida: `tests/test_cli.py`

- `test_validar_una_config_buena_sale_con_0`: código 0 y «1 acción válida».
- `test_accion_que_no_existe_sale_con_1`: código 1 (orden correcta, acción
  inexistente).
- `test_opcion_que_no_existe_sale_con_2`: código 2 (error de uso de Typer).
- `test_json_roto_sale_con_3_y_sin_traza`: código 3 y, muy importante,
  `assert "Traceback" not in salida(resultado)`.
- `test_ia_sin_clave_sale_con_4`: código 4 y «siguen funcionando».
- Los `test_organizar_*` y `test_mover_*` repiten el patrón: en simulación el
  fichero sigue y el destino no existe; de verdad el fichero se mueve. La
  doble aserción (`is_file` en un sitio y `not exists` en el otro) es lo que
  demuestra que el movimiento fue completo.
- `test_mirar_espacio_ensena_un_solo_resumen`: `texto.count("2 ficheros") == 1`
  comprueba que no se duplica el resumen.

### 3.5. IA: `tests/test_ia.py`

- `test_falta_clave_sin_red`: espera `FaltaClaveIA` y comprueba que el mensaje
  menciona `CENTRO_IA_KEY` pero **no** contiene `sk`. Es la prueba de que la
  clave no se filtra en el error.
- `test_sin_red_el_mensaje_es_humano`: conecta a `127.0.0.1:9` (puerto
  cerrado) y espera `IANoDisponible` con «conexión». No hay traceback ni
  espera eterna.
- `test_codigo_salida_sin_ia`: `IANoDisponible.codigo_salida == 4` para la
  base y sus dos subclases.
- `test_ianodisponible_es_una_sola_clase`: comprueba que la clase de `ia.py`
  es exactamente la de `errores.py`. Evita el fallo sutil de tener dos clases
  con el mismo nombre y que un `except` no capture la que toca.
- `test_sugerir_propuesta_invalida`: espera `ErrorIA` con «validación». La IA
  no puede colar una acción que el esquema rechaza.
- `test_simular_no_pregunta_al_modelo`: `falso.preguntas == []`. Demuestra que
  simular no llama a la red.
- `test_categoria_rara_no_inventa_carpeta`: estado «saltado», no se crea
  carpeta y el fichero sigue donde estaba. Es la garantía de que una respuesta
  rara de la IA no mueve nada a ciegas.
- `test_respuesta_rota`: el servidor devuelve JSON sin los campos esperados y
  se convierte en `ErrorRedIA`, no en `KeyError`.

### 3.6. Historial y deshacer: `tests/test_historial.py`

- `test_registrar_apunta_solo_lo_que_cambio`: un resultado «saltado» no se
  apunta. El historial solo guarda operaciones reales.
- `test_registrar_guarda_rutas_absolutas`: `Path(...).is_absolute()`. Así
  `deshacer` funciona aunque se lance desde otra carpeta.
- `test_leer_ignora_lineas_rotas`: una línea corrupta no invalida el resto.
- `test_deshacer_devuelve_un_movimiento`: origen vuelve a existir, destino ya
  no, y el historial queda vacío. Las tres aserciones juntas prueban que el
  lote se revirtió y se consumió.
- `test_deshacer_simular_no_toca_nada`: el destino sigue, el origen no existe y
  el lote permanece. Simular no consume el historial.
- `test_deshacer_borrar_avisa_y_conserva_el_lote`: estado «saltado», detalle
  «no se puede deshacer» y el lote sigue. Un borrado no se finge reversible.

### 3.7. Rutas, temas, menú e instaladores

- `tests/test_rutas.py`: comprueba que `~/Descargas` se traduce a `Downloads`
  (inglés), `Baixades` (valenciano), sin depender de tildes ni mayúsculas, y
  que fuera de la carpeta personal no se traduce nada. Es la prueba de que el
  mismo `acciones.json` vale en varios sistemas.
- `tests/test_terminal.py`: cada paleta tiene 16 colores válidos, `normalizar_hex`
  acepta y rechaza con mensaje humano, y `detectar` no promete color donde no
  lo hay (`TERM=dumb`, consola clásica de Windows, tmux). Evita “mentir” al
  usuario.
- `tests/test_menu.py`: todas las órdenes aparecen, ninguna se repite, una
  orden nueva cae en «OTRAS», los atajos coinciden y el menú cabe en 26 líneas
  a distintos anchos. Es una prueba de usabilidad automatizada.
- `tests/test_instaladores.py`: los instaladores no llevan BOM y el `.ps1` es
  solo ASCII. Evita que Windows PowerShell se atragante con el script.

### 3.8. Buscar, doctor, ajustes y exportación

- `tests/test_buscar.py`: `test_asterisco_actua_como_global` demuestra que el
  texto se trata como glob; `test_regex_rota_es_error` y
  `test_carpeta_inexistente_es_error` son casos feos con mensaje humano;
  `test_omite_carpetas_ruidosas` comprueba que no baja a `.git`, `.venv`,
  `__pycache__` ni `node_modules`; `test_ordenar_por_fecha_descendente`
  garantiza el orden de la tabla.
- `tests/test_doctor.py`: `test_origen_en_otro_idioma_cuenta_como_ok` prueba
  que `~/Descargas` vale si existe `~/Downloads`;
  `test_ia_sin_clave_es_info_no_aviso` fija que fuera del centro la falta de
  clave es informativa, no un aviso; `test_cada_estado_tiene_simbolo_y_color`
  evita que un estado nuevo rompa la tabla.
- `tests/test_ajustes.py`: `test_leer_json_roto_no_falla` y
  `test_leer_json_que_no_es_objeto` cubren un ajuste corrupto sin tumbar la
  CLI; `test_guardar_en_carpeta_imposible_da_error_humano` comprueba que un
  fallo de permisos sale como error propio.
- `tests/test_exportar_tema.py`: los tres formatos (Windows, iTerm y GNOME)
  llevan sus 16 colores; `test_guardar_en_ruta_imposible_da_error_humano`
  confirma que exportar a una ruta mala no deja un traceback.

### 3.9. Aserciones dentro del código (rubric «aserciones en desarrollo»)

No son tests, son invariantes que se comprueban mientras el programa corre:

- `config.py:124`: tras validar, `len(nombres) == len(acciones)`. Si alguien
  saltara la validación, el motor no podría indexar dos acciones iguales.
- `motor.py:27`: el diccionario de acciones conserva todas las del JSON.
- `motor.py:88`: lo seleccionado son ficheros de verdad.
- `acciones.py:68`: `destino_libre` no devuelve una ruta ya reservada.

Se pueden desactivar con `python -O`; en desarrollo avisan de un error de
programación, no de un error del usuario.

---

## 4. Los casos feos que hay que nombrar (mínimo 3)

La rúbrica pide «camino feliz y 3 casos feos». Estos están cubiertos:

1. **JSON roto o con campos mal**: `test_json_roto_dice_la_linea`,
   `test_el_error_dice_que_campo_falla`, `test_accion_repetida_nombre`.
2. **Carpeta o fichero que no existe**: `test_organizar_carpeta_inexistente_sale_con_1`,
   `test_mover_fichero_inexistente_sale_con_1`, `test_cargar_acciones_sin_fichero`.
3. **Sin clave o sin red para la IA**: `test_falta_clave_sin_red`,
   `test_sin_red_el_mensaje_es_humano`, `test_ia_sin_clave_sale_con_4`.
4. **Colisión de nombres (no sobrescribir)**: `test_nunca_sobrescribe`
   (acciones y mover/organizar).
5. **Respuesta rara de la IA**: `test_categoria_rara_no_inventa_carpeta`,
   `test_respuesta_rota`.
6. **Historial corrupto o irreversible**: `test_leer_ignora_lineas_rotas`,
   `test_deshacer_borrar_avisa_y_conserva_el_lote`.

---

## 5. Preguntas probables y respuestas cortas

**¿Por qué las acciones están en JSON y no en código?**
Para que cambiar un filtro o una carpeta no obligue a tocar Python ni a
reinstalar, y para que otra persona use sus rutas sin leer el código. Está
razonado en `docs/adr/0001-configuracion-externa.md`. El coste es mantener el
validador; lo asumimos.

**¿Qué pasa si el JSON es válido pero la acción es peligrosa?**
Se valida el esquema, pero además `borrar` pide confirmación por defecto, todo
se puede simular y `destino_libre` evita sobrescribir. La validación no decide
por el usuario: evita que un typo haga que una acción destructiva vea de más.

**¿Dónde está la clave de la IA?**
En `.env` o en variables de entorno. `.env` está en `.gitignore` desde el
primer commit y nunca se ha subido; el historial está auditado y no hay
`sk-` reales. `.env.example` documenta las variables sin valores.

**¿Y si no hay internet en clase?**
Las acciones sin IA funcionan igual. Las de IA salen con código 4, explican el
motivo y dan un consejo; no hay traceback. Simular una acción con IA tampoco
llama a la red.

**¿Por qué una excepción por tipo de error?**
Porque el código de salida importa: 3 es configuración, 4 es IA, 1 es error de
la operación, 2 es uso. Así un script que llama a `tareas` puede reaccionar
distinto sin mirar el texto del mensaje.

**¿Por qué `Path` y no `os.path`?**
Es más legible, funciona igual en Linux, Windows y macOS y evita concatenar
barras a mano. Todo se escribe con `encoding="utf-8"`.

**¿Cómo sé que no se pierde un fichero a medias?**
Las operaciones son por fichero y `destino_libre` reserva el nombre antes de
mover/copiar. Si una falla, se marca «error» y las demás siguen; el historial
permite deshacer lo que sí se hizo. Además, borrar usa la papelera en las
órdenes que la usan y pide confirmación.

**¿Qué no cubre la herramienta?**
No es un gestor de copias de seguridad ni resuelve conflictos de contenido: si
dos ficheros se llaman igual, añade ` (1)` en vez de fusionarlos. La IA puede
equivocarse al clasificar; por eso lo dudoso se salta y se avisa.

**¿Cómo se ejecutan las pruebas?**
`uv run pytest`. En cada push y PR, GitHub Actions lo lanza en Ubuntu, Windows
y macOS (`.github/workflows/pruebas.yml`). En Linux hoy: 237 pasan y 1 se salta.

**¿Por qué hay una prueba que se salta?**
Es `tests/test_terminal.py:159` (`test_la_consola_clasica_de_windows_avisa`),
marcada con `@pytest.mark.skipif(os.name != "nt", ...)`: solo se puede
comprobar en Windows. Se salta por sistema operativo, no por un fallo. En el
trabajo de Windows del CI esa prueba sí corre y la que se salta es otra
(`test_ajustes.py::test_carpeta_usa_xdg_fuera_de_windows`, que no aplica en
Windows). El conjunto está pensado para que cada comportamiento se pruebe
donde tiene sentido.

---

## 6. Estructura del código (para el criterio de diseño)

```text
src/tareas/
  cli.py         Órdenes, opciones, tablas y códigos de salida. No mueve ficheros.
  config.py      Lee y valida acciones.json. No ejecuta nada.
  motor.py       Selecciona ficheros y llama a la acción.
  acciones.py    Clases Mover/Copiar/Renombrar/Borrar/MirarEspacio/IA.
  ia.py          ProveedorIA, ProveedorCentro, errores y utilidades de IA.
  errores.py     Excepciones propias con su código de salida.
  rutas.py       Traducción de carpetas personales entre idiomas.
  historial.py   Registro y deshacer de operaciones.
  ajustes.py     Preferencias del usuario (tema).
  menu.py        Menú interactivo.
  terminal.py    Paletas y secuencias de color.
  doctor.py      Diagnóstico de entorno.
  organizar.py   Ordenar por tipo.
  mover.py       Mover un fichero concreto.
  capturas.py / temporales.py / imagenes.py / informe.py
```

Fábricas que conviene mencionar:

- `Accion.desde_config(config)` (`acciones.py:164`): convierte un diccionario
  del JSON en la clase correcta usando el registro por `tipo`.
- `ProveedorCentro.desde_entorno()` (`ia.py:132`): lee el `.env` y devuelve el
  proveedor o lanza `FaltaClaveIA`.

---

## 7. Decisiones y ADRs

- `docs/adr/0001-configuracion-externa.md`: por qué JSON y no código.
- `docs/adr/0002-ia-interfaz-y-salida-4.md`: por qué la IA es una interfaz y
  por qué el código de salida 4.
- `docs/adr/0003-temas-de-terminal.md`: por qué los temas se aplican con
  secuencias OSC y se exportan a varios terminales.

Si preguntan «¿por qué no YAML/TOML/SQLite?», la respuesta está en el ADR-0001:
JSON viene en la biblioteca estándar, no añade dependencias y el fichero se
revisa y versiona con git.

---

## 8. Checklist de última hora

- [ ] `uv run pytest -q` termina en verde.
- [ ] `tareas --help`, `tareas acciones` y `tareas --config acciones.json validar` funcionan.
- [ ] Sabes explicar los códigos 0, 1, 2, 3 y 4 con un ejemplo cada uno.
- [ ] Sabes explicar qué hace `--simular` y por qué no toca disco.
- [ ] Sabes explicar por qué nunca se sobrescribe (`destino_libre`).
- [ ] Sabes explicar dónde está la clave y qué pasa sin red.
- [ ] Sabes nombrar 3 casos feos y el test que los cubre.
- [ ] Sabes decir qué assert de `config.py`/`motor.py`/`acciones.py` protege qué invariante.
- [ ] Tienes localizado el ADR-0001 y sabes resumirlo en 30 segundos.
