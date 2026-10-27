# ADR-0001: Las acciones viven en acciones.json, no en el código

- Estado: aceptada
- Fecha: 2026-10-27
- Autor: Javier Sansano

## Contexto

Mi herramienta «tareas» automatiza tareas repetitivas con ficheros: limpiar
temporales de Descargas, mover imágenes a mi carpeta de fotos y renombrar
capturas de pantalla con su fecha. Yo mismo voy a querer cambiar los filtros,
las carpetas y los nombres cada pocas semanas, y quiero que otra persona pueda
usar la herramienta con sus propias rutas y sus propias manías sin tocar mi
código.

## Decisión

Las acciones se describen en un fichero JSON externo (`acciones.json`) con un
esquema documentado en el README. El código solo contiene el motor que lee,
valida y ejecuta ese fichero. Añadir una acción normal equivale a editar el
JSON; añadir un tipo nuevo de acción sí exige una clase nueva.

## Alternativas consideradas

1. Escribir cada acción como una función en Python.
   - A favor: es lo más directo para tres acciones y no hace falta validar un
     formato externo.
   - En contra: cada cambio en un filtro o una carpeta exige tocar el código y
     reinstalar; quien no programa no puede adaptar la herramienta.
2. Usar YAML o TOML en vez de JSON.
   - A favor: YAML es más cómodo para textos largos y TOML se lee muy bien.
   - En contra: JSON viene en la biblioteca estándar, no añade dependencias y
     Typer ya trabaja con estructuras de datos sencillas. Para este esquema no
     compensa aprender otra sintaxis ni instalar un lector.
3. Guardar las acciones en una base de datos SQLite.
   - A favor: permitiría historial, consultas y cambios sin editar ficheros a
     mano.
   - En contra: para tres acciones es una complejidad innecesaria; además, el
     fichero de texto se puede revisar y versionar con git.

## Consecuencias

- Positivas: añadir o cambiar una acción no toca el código; el JSON se valida
  antes de ejecutar; puedo tener una configuración de pruebas separada y el
  historial de git muestra cómo evolucionan mis acciones.
- Negativas: hay que mantener la validación al día cuando crezca el esquema;
  los errores de escritura solo se detectan al ejecutar `tareas validar`; y un
  tipo de acción nuevo sigue necesitando código.
- Qué haré si el esquema cambia: subiré el campo `version` a 2, mantendré la
  lectura de la versión 1 mientras sea posible y documentaré la migración en el
  README y en la skill `acciones-json`.
