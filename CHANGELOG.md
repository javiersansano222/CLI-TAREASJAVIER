# Changelog

Todos los cambios que notará quien USA la herramienta. Formato:
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · versiones:
[SemVer](https://semver.org/lang/es/).

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
