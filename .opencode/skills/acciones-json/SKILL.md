---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI tareas (campos, tipos, filtros, plantillas y validación). Úsala siempre que crees o cambies acciones o el código que las lee (config.py, acciones.py, motor.py).
---
# Esquema de acciones.json

- Raíz: `{"version": 1, "acciones": [...]}`. La versión debe ser el entero 1 y la lista no puede estar vacía.
- Cada acción: `nombre` (único, minúsculas, números y guiones), `descripcion` y `tipo`.
- Tipos: `mover` y `copiar` (requieren `destino`), `renombrar` (requiere `plantilla`) y `borrar` (confirma antes de actuar salvo `--si`).
- `origen` es opcional: si falta, se usa la carpeta indicada en la orden.
- `filtro` opcional: `extensiones` (lista con punto, por ejemplo `.pdf`), `patron` (regex válida sobre el nombre), `mas_antiguo_que_dias` y `mayor_que_mb`.
- `plantilla` para renombrar: huecos `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}` y `{nombre}`. No puede contener barras. Se prueba con un nombre de muestra y se rechazan formatos inválidos, caracteres prohibidos en Windows, nombres reservados y finales en punto o espacio.
- `confirmar` es booleano y solo afecta a las acciones destructivas; por defecto es `true`.
- No se admiten campos desconocidos ni en la raíz ni en cada acción: un typo como `filtros` debe ser un error de configuración, no un filtro ignorado.

## Acciones actuales

- `limpiar-temporales`: borra `.tmp` de `~/Descargas` con más de 30 días.
- `mover-imagenes`: mueve imágenes de `~/Descargas` a `~/Imágenes/Fotos`.
- `renombrar-capturas`: renombra capturas de `~/Imágenes/Capturas` como `AAAA-MM-DD_001.png`.

## Reglas al programar

- Valida el JSON en `config.py` ANTES de ejecutar; los errores usan `AccionNoValida(accion, campo, motivo)`. Lee con `utf-8-sig` y convierte `UnicodeDecodeError` en `ConfigError`.
- `pathlib` y `shutil`; nunca `shell=True` ni `os.system`; nunca sobrescribir: usa `destino_libre` con el sufijo ` (1)` y comprueba también symlinks rotos.
- Todas las acciones admiten `--simular` y devuelven `list[Resultado]`.
- Con `simular=True` no se llama a `mkdir`, `move`, `rename` ni `unlink`.
- `Resultado` puede ser `hecho`, `simulado`, `saltado` o `error`; el error lleva un `detalle` y no aborta el resto del lote. La CLI termina con código 1 si hay algún error.
- La simulación reserva los destinos ya calculados y tiene en cuenta los ficheros que se van a mover o renombrar en el mismo lote.
- Los filtros numéricos deben ser finitos; `mayor_que_mb` es estrictamente mayor que N MB.
- Si añades un campo o un tipo nuevo, documenta el cambio en el README y en esta skill.
