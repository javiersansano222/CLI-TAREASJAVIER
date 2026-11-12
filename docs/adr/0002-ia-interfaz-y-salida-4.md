# ADR-0002: La IA va detrás de una interfaz y sin red la CLI sigue viva

- Estado: aceptada
- Fecha: 2026-11-05
- Autor: Javier Sansano

## Contexto

La semana 3 añade IA al proyecto: resumir apuntes, proponer nombres y
clasificar documentos. El problema no es escribir la llamada al modelo, sino
qué pasa cuando no puedo usarlo. En casa no tengo la red del centro; en clase
puede caer el servidor o faltar la clave. Si la herramienta se rompe por eso,
deja de servir para las 18 órdenes que no necesitan IA, que es lo que de
verdadero uso diario tiene.

Además, el servidor del centro habla una API compatible con OpenAI y usa un
certificado auto-firmado con su propia CA. Eso puede cambiar: otro modelo,
otra URL, o directamente otro proveedor.

## Decisión

1. **Interfaz `ProveedorIA`** con un único método `completar(sistema, usuario,
   max_tokens) -> RespuestaIA`. El resto del programa no sabe con quién habla;
   `ProveedorCentro` es la implementación con `httpx`, y se construye con
   `ProveedorCentro.desde_entorno()`.
2. **`IANoDisponible` con `codigo_salida = 4`** para todo lo que sea "no hay
   IA ahora": falta de clave, sin red, servidor caído o certificado sin CA.
   Es un error distinto del 1 (algo ha ido mal) y del 3 (configuración rota).
3. **Las acciones con IA declaran `necesita_ia = True`.** La CLI solo crea el
   proveedor si la acción pedida lo necesita y no se pasa `--simular`. En
   simulación no se gasta un solo token: solo se cuenta el presupuesto.
4. **Ninguna acción sin IA importa `ia.py`.** `errores.py` es quien define
   `IANoDisponible`, para que no haya ciclos y para que el motor pueda
   propagar el error sin conocer la capa de red.

## Alternativas consideradas

1. Llamar al modelo directamente desde cada acción.
   - A favor: es lo más corto de leer.
   - En contra: repetiría la lectura de claves, el timeout y el manejo de
     errores en tres sitios; cambiar de proveedor obligaría a tocar las tres.
2. Que la falta de IA sea un error normal, código 1.
   - A favor: no hace falta una clase nueva.
   - En contra: un script que lance varias órdenes no podría distinguir
     "esto no funciona por configuración" de "esto ha fallado"; y el aviso de
     que el resto sigue funcionando pierde sentido si todo sale igual.
3. Reintentar en bucle hasta que haya red.
   - A favor: en clase funcionaría "solo".
   - En contra: escondería un problema real, tardaría sin avisar y rompería
     el contrato de que una orden termina siempre con un código conocido.
4. Que `--simular` también pida al modelo lo que haría.
   - A favor: enseñaría el resultado previsto.
   - En contra: una simulación gastaría tokens y necesitaría red, que es
     exactamente lo que la simulación debe evitar.

## Consecuencias

- Positivas: sin clave o sin red todo sigue igual para las órdenes que no son
  de IA, y las de IA salen con 4 y un mensaje que lo explica; cambiar de
  proveedor es implementar otra clase de `ProveedorIA`; probar sin red es
  inyectar un proveedor falso, sin mocks de red.
- Negativas: hay dos caminos de error que mantener (red y respuesta inútil);
  `RespuestaIA` arrastra el coste aunque a veces no interese; y quien añada un
  tipo con IA tiene que acordarse de marcar `necesita_ia`, si no la acción
  fallará al llegar a `preguntar`.
- Qué haré si cambia el esquema: si aparece un tipo de acción con IA que
  necesite campos nuevos, se añaden a `TIPOS_IA` y a `_validar_ia` en
  `config.py`, y se documentan en el README y en la skill `acciones-json`.
