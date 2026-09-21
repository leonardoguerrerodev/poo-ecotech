# Análisis del código generado con IA

**Caso EcoTech Solutions · Evaluación Sumativa 2, Unidades 2 y 3 · TI3V21**
Criterios 2.1.5 (secciones 1 a 3) y 3.1.4 (secciones 4 y 5)

**Herramienta usada:** Claude (Anthropic), a través de Claude Code en el editor.
**Modo de uso:** iterativo. Cada fragmento se pidió con el contexto puesto —la clase, la tabla y las
restricciones técnicas— se leyó antes de aceptarlo, se corrigió sobre la propuesta y se registró la
decisión aquí mismo, mientras se programaba.

> La guía advierte que *«el uso de código generado exclusivamente por IA, sin análisis ni ajustes,
> será considerado insuficiente»*. Esta tabla es la evidencia de lo contrario: de los
> **veinticinco** fragmentos revisados, **dos se adoptaron —uno de ellos con un matiz—, trece se
> modificaron y diez se descartaron**.

> ⚠ Las filas 22 a 25 salieron de la auditoría de seguridad que se le hizo al código terminado,
> documentada aparte en `AUDITORIA.md`.

---

## 1. Qué se adoptó, qué se modificó y qué se descartó

| # | Aspecto revisado | Problema detectado | Decisión | Fundamento técnico |
|---|---|---|---|---|
| 1 | Estructura de la persistencia | La propuesta era una sola clase `RepositorioEcoTech` con métodos para las seis entidades | **Modificar** | Cohesión. Una clase que habla de seis temas y acumula dieciocho métodos no tiene responsabilidad única. El CRUD quedó como métodos de cada clase, agrupados bajo su comentario `# --- Persistencia (CRUD) ---` |
| 2 | Manejo de la conexión | Se abría en el constructor y se guardaba en un atributo. Nunca se cerraba | **Modificar** | Deja el archivo bloqueado toda la sesión. Ahora cada método abre y cierra la suya con el gestor de contexto `conectar()`, y la ruta es la variable de módulo `RUTA_ACTIVA` |
| 3 | Consulta de lectura | `SELECT * FROM empleado` | **Modificar** | El asterisco arrastra el salario a consultas que no lo necesitan, y rompe al agregar una columna. Se nombran las columnas |
| 4 | Lectura del salario en el `INSERT` | El repositorio leía el atributo privado directamente | **Modificar** | Saltaba el control de acceso de `obtener_salario()`. Ahora el método pide un `solicitante` con permiso, igual que el objeto |
| 5 | Validación de nombres | Una expresión regular `[A-Za-z ]+` para el nombre y la dirección | **Descartar** | Rechaza tildes, apóstrofes y apellidos compuestos. Se reemplazó por «no vacío y con tope de largo», que es lo exigible de verdad |
| 6 | Política de contraseñas | Un regex con anticipaciones múltiples, `(?=.*[a-z])(?=.*[A-Z])...` | **Descartar** | Ilegible y por lo tanto no defendible. Cuatro `any()` hacen lo mismo y se explican en voz alta |
| 7 | Comparación de hash | `hmac.compare_digest` | **Modificar** | Es la misma función que `secrets.compare_digest`. Se dejó una sola, para que todo lo criptográfico entre por un módulo |
| 8 | Getters de apoyo | Proponía `obtener_fecha()` en `RegistroTiempo` y `obtener_nombre()` en `Proyecto` | **Descartar** | Ninguno de los dos está en el diagrama UML, y agregarlos rompe la correspondencia del criterio 2.1.1. Con el SQL dentro de la clase no hacen falta: leer `self.__fecha` desde su propio método es acceso legítimo |
| 9 | Getters en `Usuario` | Proponía `obtener_nombre_usuario()` y `obtener_rol()` | **Descartar** | Mismo motivo. `Usuario` tiene cinco métodos en el diagrama y habría quedado con siete |
| 10 | Persistencia genérica | Un método `guardar(objeto)` que decidía la tabla según el tipo | **Descartar** | Es un `isinstance()` disfrazado, justo lo que `Informe.generar()` evita, y acopla el repositorio a las seis clases a la vez |
| 11 | Base de datos para las pruebas | `:memory:` | **Modificar** | Dejó de servir al abrir y cerrar la conexión por método: cada llamada crearía una base nueva. Se usa un archivo temporal que se borra al terminar |
| 12 | Comentario en `quitar_empleado` | El comentario afirmaba lo contrario de lo que hace el código | **Modificar** | Detectado auditando el archivo. Un comentario que miente es peor que no tener comentario |
| 13 | Conexión y transacción | `with sqlite3.connect(...)` como cierre de la conexión | **Adoptar con matiz** | `with` confirma la transacción pero **no** cierra la conexión. Se adoptó la forma y se agregó el `close()` en un `finally` |
| 14 | Esquema y restricciones | `CREATE TABLE` con claves foráneas, `CHECK` y clave primaria compuesta | **Adoptar** | Correcto y coherente con el diagrama. Se verificó restricción por restricción contra las relaciones del modelo |
| 15 | El programa principal | Un menú de consola de catorce opciones con inicio de sesión, 344 líneas | **Descartar** | La actividad pide un `main.py` que ejecute las cuatro operaciones y muestre el resultado. Catorce opciones y un inicio de sesión resolvían un problema que nadie planteó. Se descartó el alcance, no la forma: el menú de diez opciones que quedó es la fila 19 |
| 16 | Dónde vive el SQL | Propuso dejar la persistencia como funciones de módulo debajo de las clases, para «no mezclar dominio y persistencia» | **Descartar** | Fuera de la clase, escribir una fila obliga a leer atributos privados por su nombre mangleado, `empleado._Persona__direccion`, que es un agujero de encapsulamiento que el diagrama no autoriza. Adentro se cierra solo. El costo asumido es acoplamiento: `Empleado` sabe de SQL. Es aceptable porque hay un solo motor de base y ninguna intención de cambiarlo; con dos, el patrón repositorio volvería |
| 17 | `Empleado.actualizar_contacto` | Propuso sobrescribirlo para agregar el `UPDATE`, llamando a `super()` para validar | **Modificar** | La forma es correcta y es reutilización real, pero `Persona.__init__` invocaba ese mismo método público: cada objeto reconstruido desde una fila habría escrito en la base al leerse. Se hizo privado el asignador del constructor |
| 18 | Acceso a los campos de `Persona` | Propuso bajar `__nombre`, `__direccion`, `__telefono` y `__correo` a un solo guion bajo para que `Empleado` los viera | **Descartar** | El diagrama los marca con `-`, privados. Cambiar la visibilidad para acomodar el código rompe la correspondencia del criterio 2.1.1. Se agregó `_datos_contacto()`, protegido: la clase decide qué expone a sus hijas |
| 19 | El menú de terminal | Volvió a proponer el menú del punto 15, ahora sí pedido explícitamente | **Modificar** | Se conservó la forma y se recortó el alcance: diez opciones en vez de catorce, sin inicio de sesión, que es Unidad 3. El `try/except` pasó a estar **dentro** del bucle, que es lo que hace que el menú sobreviva a un error |
| 20 | Despacho por diccionario | Propuso un `dict` que mapeara cada tecla a una función | **Descartar** | Cada opción pide datos distintos, así que uniformar las firmas obliga a inventar parámetros que nadie usa. Un `if/elif` de once ramas es aburrido y se lee de corrido |
| 21 | Archivo de pruebas | Mantener los 233 assert de `pruebas.py` como tercer archivo | **Modificar** | La rúbrica no pide un archivo de pruebas y el docente pidió menos archivos. Quedaron 38 `assert` en la autoverificación de `ecotech.py`, cubriendo las mismas reglas |
| 22 | Validación del entero del menú | `valor.isdigit()` para aceptar un número tecleado | **Modificar** | Los dos predicados suenan igual y no lo son: `"²".isdigit()` es `True` y `int("²")` falla. Se cambió por `isdecimal()`, que acepta exactamente lo que `int()` convierte. Detectado auditando, no ejecutando |
| 23 | Rango del salario | `if salario <= 0`, solo cota inferior | **Modificar** | Sin techo, un número de 25 dígitos pasaba y reventaba en SQLite con `OverflowError`, que no estaba en la cadena de `except`: el programa moría. Se agregó `SALARIO_MAXIMO`, un tope en `pedir_entero()` y el `CHECK` en la tabla. Detalle en `AUDITORIA.md`, sección 3 |
| 24 | Alcance del control de acceso | Comprobar el permiso solo donde se lee un dato sensible | **Descartar** | El criterio no es qué se lee, es qué se escribe. Con esa regla, borrar un empleado no pedía permiso y leer su sueldo sí. Los siete métodos que escriben o exponen datos pasan ahora por `autorizar()`. Sección 4 de `AUDITORIA.md` |
| 25 | `except Exception` final | Lo desaconsejó, citando que oculta errores | **Modificar** | Tiene razón sobre `except: pass`. Pero puesto último y nombrando el tipo del error, es lo que hace cierta la promesa de «no se interrumpe» del indicador 2.1.4.G.7. Se adoptó en esa forma, no en la que la herramienta rechazaba |

---

## 2. Los tres criterios con que se decidió

La guía pide exponer los criterios técnicos. Fueron estos tres, en este orden:

**Seguridad.** Descartó los puntos 4, 5 y 6, y forzó los puntos 2 y 3. Un repositorio que lee un
salario sin permiso abre por la puerta de atrás lo que el objeto cierra por la de adelante.

**Coherencia con el modelo.** Descartó los puntos 8, 9 y 10. El criterio 2.1.1 evalúa la
correspondencia entre el diagrama y el código: un método que no está en el diagrama es una
incoherencia, aunque sea cómodo.

**Legibilidad.** Descartó los puntos 6 y 15, y motivó el 12. Lo que no se puede explicar en voz alta
no se puede defender, y la evaluación es en parte oral. El punto 15 además enseña algo más general:
la herramienta responde a lo que se le pide y agranda el alcance sin avisar. Un inicio de sesión
funciona, pero es Unidad 3, y con catorce opciones había que navegar para llegar a las cuatro
operaciones que la actividad pedía mostrar.

---

## 3. Los errores que la herramienta comete de forma sistemática

Vale la pena tenerlos anotados, porque se repiten y porque la lámina 54 los enumera igual:

1. **Optimiza que el ejemplo funcione la primera vez**, no que resista. La conexión sin cerrar y el
   `SELECT *` corren perfecto en la primera prueba y fallan en uso real.
2. **Propone la comodidad antes que el contrato.** Ofrece getters porque simplifican el código de al
   lado, sin mirar si el modelo los tiene.
3. **Escribe comentarios que describen la intención, no el código.** El caso 12 es exactamente eso:
   el comentario decía lo que se quiso escribir.
4. **Prefiere lo genérico.** El `guardar(objeto)` del caso 10 parece elegante y es acoplamiento.
5. **Agranda el alcance.** Si se le deja, entrega más de lo pedido: el menú del caso 15 son 344
   líneas para un requisito de cuarenta.

La conclusión práctica: **lo que la herramienta produce sirve como borrador y nunca como versión
final.** El filtro que funcionó fue leer cada fragmento contra tres cosas concretas: el diagrama de
clases, el material de clases y el enunciado.

---

# Unidad 3 — APIs, autenticación y errores de red

Criterio 3.1.4 · indicadores **3.1.4.G.20** (evidenciar y documentar el uso de IA, analizando el
código sugerido) y **3.1.4.G.21** (identificar errores, redundancias o vulnerabilidades en ese código
y refactorizarlo con justificación).

**Herramienta usada:** Claude (Anthropic), modelo Opus 5, a través de Claude Code en *plan mode*: la
IA leyó la rúbrica, la guía y toda la documentación del proyecto, propuso un plan que se aprobó por
decisiones (qué APIs, qué librería, dónde vive el cliente HTTP), y después lo ejecutó por pasos,
con verificación en cada uno. **Cada fila de esta tabla ocurrió en esa sesión, el 21-sep-2026**, y se
registró mientras se programaba.

**Cómo se probó lo generado:** tres autoverificaciones y una sesión real. `python3 ecotech.py`
(login y bloqueo sobre una base temporal), `python3 servicios.py` (códigos HTTP, errores de red y cuerpos malformados con
respuestas simuladas, sin conectarse), y el menú completo con red real, con la red cortada y
contra un host inalcanzable (`docs/SALIDA_TERMINAL.md`, sección Unidad 3).

## 4. Qué se adoptó, qué se modificó y qué se descartó

| # | Aspecto revisado | Problema detectado | Tipo | Decisión | Fundamento técnico |
|---|---|---|---|---|---|
| 26 | Suposición sobre la API de geocodificación | Se asumió que una ciudad inexistente respondería `404`. **Consultada la API real antes de programar**, responde `200` con un JSON sin la clave `results` | Error | **Modificar** | Si se hubiera programado sobre la suposición, «ciudad no encontrada» habría salido como formato inesperado o como `KeyError`. Se trata como `ValueError` con mensaje claro, y hay una prueba con ese cuerpo exacto |
| 27 | Revisar el `Content-Type` de la respuesta | Un chequeo de `application/json` parecía una buena validación | Error | **Descartar** | mindicador.cl devuelve el euro con `text/html` aunque el cuerpo es JSON válido: el chequeo habría rechazado datos correctos. Lo que se valida es el contenido: que sea JSON, que sea un objeto y que el campo tenga el tipo esperado |
| 28 | Tipo de cambio recibido | La primera versión solo exigía `valor > 0` | Vulnerabilidad | **Modificar** | El parser de JSON de Python acepta `Infinity` y `NaN`. `Infinity > 0` es verdadero y el pago quedaba en `0,00 USD`. Se agregó `math.isfinite()` y se rechaza también un `bool`, que en Python es un entero |
| 29 | Nombre de la ciudad que devuelve la API | Se imprimía tal cual en la terminal | Vulnerabilidad | **Modificar** | Lo que llega de la red es tan poco confiable como lo que se teclea. Un nombre con `\x1b[2J` habría borrado la pantalla, la misma familia de ataque que la U2 cerró para la entrada del usuario (AUDITORIA §2.5). Si no es imprimible o supera 120 caracteres, se muestra el nombre que escribió el usuario, que ya fue validado |
| 30 | Alta de la cuenta inicial | Primer diseño: consultar si la tabla está vacía y, si lo está, insertar | Vulnerabilidad | **Modificar** | Es un *check-then-act*: entre la consulta y el `INSERT` otro proceso puede crear su cuenta, y las dos quedarían como administrador sin sesión. Se reemplazó por una sola sentencia, `INSERT … SELECT … WHERE NOT EXISTS (SELECT 1 FROM usuario)`, y se mira `rowcount` |
| 31 | Hash señuelo para usuarios inexistentes | El plan proponía guardar un `Usuario` señuelo con su propio hash | Redundancia | **Modificar** | Lo que iguala el tiempo es calcular un scrypt con el mismo costo, no tener un objeto. `_hashear(clave, bytes(16))` hace exactamente eso en una línea, sin un atributo ni un método más en la clase |
| 32 | `autenticar` | `correcta = verificar_clave(clave) and not bloqueada`, seguido de `if bloqueada: return None` | Redundancia | **Modificar** | La segunda condición ya excluía el caso, así que el `and` no aportaba nada y hacía creer que el orden importaba. Quedó `verificar_clave` siempre primero (para que una cuenta bloqueada tarde lo mismo) y la salida anticipada después |
| 33 | Cuándo se revisa el permiso | Cada método revisaba el permiso **al final**, al escribir | Error | **Modificar** | Con roles reales, un gerente llenaba los seis datos de «contratar» para recibir «No autorizado», y «Datos de ejemplo» alcanzaba a crear los departamentos antes de fallar en los empleados: quedaba una carga a medias. Se agregó un mapa `PERMISO` en `ejecutar()`: el permiso se revisa **antes de pedir un dato**. Los métodos lo siguen revisando: dos capas |
| 34 | Mensajes de error del menú | `OperationalError` imprimía el texto de SQLite y `except Exception` el mensaje de la excepción | Vulnerabilidad | **Modificar** | La guía lo nombra: «los mensajes de error exponen información sensible del sistema». El texto de una excepción puede traer rutas, consultas o nombres de tablas. Ahora el primero da un mensaje fijo y el segundo solo el **tipo** del error |
| 35 | Excepciones de red | El orden `Timeout` → `ConnectionError` → `RequestException` | — | **Adoptar con matiz** | `ConnectTimeout` hereda de **las dos** primeras, así que el orden decide el mensaje; con `ConnectionError` primero, un tiempo de espera se reportaría como falta de red. Matiz descubierto al probar: detrás de un proxy, `requests` informa el tiempo agotado como `ProxyError`, hija de `ConnectionError`. El mensaje sigue siendo correcto para el usuario, y el timeout real se verificó contra un host inalcanzable: 3,05 s |
| 36 | Moneda consultada | Validar la moneda con un patrón de tres letras | Vulnerabilidad | **Modificar** | La moneda termina **en la ruta** de la URL (`/api/dolar`). Un patrón deja pasar códigos que la API no tiene (responde `500`); una **lista blanca** `{"USD", "EUR", "UF"}` no deja pasar nada que no se haya decidido, y de paso hace imposible inyectar una ruta como `../` |
| 37 | Despacho de las opciones del menú | Pasar de la cadena `if/elif` a un diccionario de funciones | — | **Adoptar, revisando la fila 20** | En la U2 se descartó (fila 20) porque obligaba a inventar parámetros. Con catorce opciones la cadena supera el umbral de complejidad cognitiva de SonarCloud (15), el mismo issue S3776 que ya se corrigió en `main.py` (AUDITORIA §2.10). El costo es real y se asume: dos funciones reciben un `_solicitante` que no usan y dos lecturas van envueltas en `lambda` |
| 38 | Autoverificación del login | Una prueba creaba `Usuario("g", …)` para comprobar que un gerente no crea cuentas | Error | **Modificar** | La prueba fallaba por el motivo equivocado: `"g"` no cumple `PATRON_USUARIO` y el constructor lanzaba `ValueError` antes de llegar al permiso. Se detectó al ejecutarla. Una prueba que pasa por la razón incorrecta no prueba nada |
| 39 | El diagrama `modelo_u3.drawio` | Las filas nuevas de `Usuario` se agregaron al final del XML con su coordenada `y` | Error | **Modificar** | La caja usa `stackLayout`, que ordena las filas por su posición en el XML e ignora la `y`: los tres métodos nuevos habrían aparecido debajo de `validarClave`. Se reubicaron en el XML, después de `rol` y de `tienePermiso` |
| 40 | Llave de API por variable de entorno | Leer una llave opcional de Open-Meteo desde el entorno | Alcance | **Descartar** | Ninguna de las dos APIs la exige y el código para una llave que no existe no se puede probar. La regla queda declarada: si un servicio la pidiera, iría en una variable de entorno o en `.env`, que ya está en el `.gitignore`, nunca en el código |
| 41 | Getters para mostrar la sesión | Para escribir «Sesión: usuario (ROL)» en el menú hacían falta `obtener_rol()` y `obtener_nombre_usuario()` | Coherencia | **Descartar** | Son los mismos getters descartados en la fila 9, y el diagrama no los tiene. El menú muestra el nombre que el usuario acaba de escribir, que ya tiene: el dato no hacía falta pedírselo a la clase |
| 42 | Flechas del diagrama tras agrandar cajas | Se agrandaron `Usuario` (+120 px) y el marco del Módulo Seguridad (+120 px) sin revisar las flechas ancladas a ellos | Error | **Modificar** | Detectado **renderizando** el diagrama con el visor oficial de draw.io, no leyendo el XML. «identifica a» sale del marco con `exitY` relativo, y al crecer el marco el punto de salida bajó 19 px y la flecha se quebró: se recalculó `exitY` para el mismo punto absoluto. «tiene» quedó doblada porque el centro de `Usuario` bajó: se alineó `Rol` y se separaron las etiquetas |
| 43 | Visibilidad de las constantes de `ServicioExterno` | El diagrama las marcó privadas, `- TIEMPO_ESPERA` y `- MONEDAS` | Error | **Modificar** | En el código son públicas y `main.py` lee `ServicioExterno.MONEDAS` para mostrar las opciones. Se cambiaron a `+`. Es el error que el criterio 2.1.1 castiga: el diagrama diciendo algo distinto del código |

## 5. Lo que cambió respecto de la Unidad 2

Los tres criterios siguen siendo los mismos —seguridad, eficiencia y coherencia con el modelo—,
pero la Unidad 3 agregó una fuente de error que la 2 no tenía: **la red**. Y ahí la herramienta
mostró un sesgo nuevo, que se suma a los cinco de la sección 3:

6. **Supone el contrato de la API en vez de consultarlo.** Las filas 26 y 27 salieron de preguntarle
   a la API real antes de escribir el código: una ciudad inexistente no es un `404`, y un JSON válido
   puede llegar etiquetado como HTML. La documentación de una API dice cómo debería responder; solo
   una llamada real dice cómo responde.

Y una lección que vale para las dos unidades: **los datos que vienen de afuera se validan igual,
vengan del teclado o de la red** (filas 28 y 29). La autenticación protege quién entra; la
validación protege lo que entra.
