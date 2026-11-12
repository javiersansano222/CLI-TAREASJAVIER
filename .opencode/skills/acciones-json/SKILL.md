---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI tareas (campos, tipos, filtros, plantillas y validación). Úsala siempre que crees o cambies acciones o el código que las lee (config.py, acciones.py, motor.py).
---
# Esquema de acciones.json

- Raíz: `{"version": 1, "acciones": [...]}`. La versión debe ser el entero 1 y la lista no puede estar vacía.
- Cada acción: `nombre` (único, minúsculas, números y guiones), `descripcion` y `tipo`.
- Tipos sin IA: `mover` y `copiar` (requieren `destino`), `renombrar` (requiere `plantilla`) y `borrar` (confirma antes de actuar salvo `--si`).
- `mirar_espacio` es de solo lectura: no requiere `destino` ni `plantilla`, informa del tamaño y número de ficheros y no borra, mueve ni crea nada.
- Tipos con IA (están en `TIPOS_IA`): `resumir` (escribe `{stem}.resumen.md` en `destino` o junto al fichero), `renombrar_ia` (cambia solo la base del nombre, la extensión no se toca) y `clasificar` (mueve a `destino/<categoría>/`; requiere `destino` y `categorias`).
- Campos de los tipos con IA, validados en `_validar_ia`: `instrucciones` (obligatorio: qué pide al modelo), `max_caracteres` (entero 500-50000, por defecto 12000: tope de texto enviado) y `categorias` (obligatorio solo en `clasificar`: lista no vacía sin repetidos).
- Las acciones con IA necesitan `proveedor`: lo inyecta el motor, y en `--simular` no se pide nada al modelo, solo se cuenta el presupuesto en la columna Detalle.
- `origen` es opcional: si falta, se usa la carpeta indicada en la orden.
- `filtro` opcional: `extensiones` (lista con punto, por ejemplo `.pdf`), `patron` (regex válida sobre el nombre), `mas_antiguo_que_dias` y `mayor_que_mb`.
- `plantilla` para renombrar: huecos `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}` y `{nombre}`. No puede contener barras. Se prueba con un nombre de muestra y se rechazan formatos inválidos, caracteres prohibidos en Windows, nombres reservados y finales en punto o espacio.
- `confirmar` es booleano y solo afecta a las acciones destructivas; por defecto es `true`.
- No se admiten campos desconocidos ni en la raíz ni en cada acción: un typo como `filtros` debe ser un error de configuración, no un filtro ignorado.

## Acciones actuales

- `limpiar-temporales`: borra `.tmp` de `~/Descargas` con más de 30 días.
- `mover-imagenes`: mueve imágenes de `~/Descargas` a `~/Imágenes/Fotos`.
- `renombrar-capturas`: renombra capturas de `~/Imágenes/Capturas` como `AAAA-MM-DD_001.png`.
- `copiar-instaladores`: copia `.exe` y `.deb` a `~/Documentos/Instaladores`.
- `mirar-espacio`: informa del tamaño de `~/`.
- `resumir-apuntes`, `renombrar-apuntes`, `clasificar-apuntes`: las tres con IA, sobre `~/pruebas-tareas/Apuntes`.

## Reglas al programar

- Valida el JSON en `config.py` ANTES de ejecutar; los errores usan `AccionNoValida(accion, campo, motivo)`. Lee con `utf-8-sig` y convierte `UnicodeDecodeError` en `ConfigError`.
- `pathlib` y `shutil`; nunca `shell=True` ni `os.system`; nunca sobrescribir: usa `destino_libre` con el sufijo ` (1)` y comprueba también symlinks rotos.
- Todas las acciones admiten `--simular` y devuelven `list[Resultado]`.
- Con `simular=True` no se llama a `mkdir`, `move`, `rename` ni `unlink`.
- `Resultado` puede ser `hecho`, `simulado`, `saltado` o `error`; el error lleva un `detalle` y no aborta el resto del lote. La CLI termina con código 1 si hay algún error.
- La simulación reserva los destinos ya calculados y tiene en cuenta los ficheros que se van a mover o renombrar en el mismo lote.
- Los filtros numéricos deben ser finitos; `mayor_que_mb` es estrictamente mayor que N MB.
- Si añades un campo o un tipo nuevo, documenta el cambio en el README y en esta skill.

## Reglas de los tipos con IA

- Nunca importes `ia.py` desde `config.py` ni desde `motor.py`: `errores.py` define `IANoDisponible` y es lo único que hace falta para propagar el error.
- `AccionIA.preguntar_texto` es el único punto de llamada al modelo; comprueba antes que haya proveedor y lanza `IANoDisponible` (salida 4) si no lo hay.
- Todo lo que devuelva el modelo pasa por una función de limpieza antes de tocar el disco: `a_nombre_seguro` para nombres, `_categoria_mas_cercana` para categorías. Si no hay nada válido, el resultado es `saltado` con detalle, nunca una carpeta o un nombre inventado.
- En `--simular` no se llama a `preguntar`: se devuelve `presupuesto(caracteres)` para la columna Detalle.
- Un fallo de red durante el lote propaga `IANoDisponible` y termina con código 4; el resto de órdenes de la CLI no se entera.
