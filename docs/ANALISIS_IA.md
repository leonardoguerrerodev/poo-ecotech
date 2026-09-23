# Análisis del código generado con IA

**Caso EcoTech Solutions · Evaluación Sumativa 2, Unidades 2 y 3 · TI3V21**
Criterios 2.1.5 (secciones 1 a 3) y 3.1.4 (secciones 4 a 7)

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

---

## 6. Auditoría contra la rúbrica — 23-sep-2026

**Herramienta usada:** Claude (Anthropic), modelo Opus 5.5, a través de Claude Code. La IA auditó el
código contra la rúbrica y ejecutó el plan `docs/planes/2026-09-23_auditoria-rubrica-por-etapas.md`
por etapas: después de cada una, un control mecánico (la autoverificación en `OK`, un recuento con
script o un render del diagrama) antes de pasar a la siguiente. **Cada fila ocurrió en esa sesión**
y se registró al terminarla.

**Cómo se probó lo generado:** la autoverificación de `ecotech.py`, ampliada con proyectos, horas y
cuentas vinculadas; **cinco pruebas de mutación** (romper una regla a propósito y confirmar que la
autoverificación falla); una sesión completa del menú con red real y otra con la red caída
(`SALIDA_TERMINAL.md` §5); y la medición de la demora del login (`AUDITORIA.md` §2.12).

| # | Aspecto revisado | Problema detectado | Tipo | Decisión | Fundamento técnico |
|---|---|---|---|---|---|
| 44 | El plan de la auditoría, escrito por la IA el 21-sep | Contrastado con el código antes de ejecutarlo, tenía cuatro hechos falsos o incompletos: proponía agregar la columna `usuario.empleado_id`, que **ya existía** (con un `ON DELETE CASCADE` que nadie había declarado); no preveía cómo leer horas con decimales; el `UNIQUE` de esa columna habría caído en el mensaje «Ese correo ya está registrado»; y mandaba corregir en `DEFENSA_ORAL.md` dos frases que ya estaban corregidas | Error | **Modificar** | Un plan que otra sesión ejecuta sin verificar convierte cada suposición en código. Se rehízo por etapas, con cada hecho verificado contra `archivo:línea` |
| 45 | Conteo de los miembros del diagrama para la matriz de la rúbrica | La IA sumó **68** a mano y lo escribió en la matriz; un script que extrae las celdas del XML dio **66** | Error | **Descartar** el conteo manual | Toda cifra de `RUBRICA.md` sale ahora de un script. El error venía de atribuir 8 filas a `Proyecto` y a `RegistroTiempo`, que tienen 7 |
| 46 | Getters `obtener_ciudad()` y `obtener_moneda()` | La IA propuso agregarlos al código **sin** ponerlos en el diagrama, por ser «lectura trivial» | Coherencia | **Modificar** | Contradice la regla del proyecto: ningún método fuera del UML salvo el CRUD. Van al diagrama. Es el mismo criterio de las filas 9 y 41, aplicado al revés: allí se descartaron porque el menú no los necesitaba; aquí el menú sí los necesita |
| 47 | `Proyecto` en el diagrama | Al sumar cinco filas y partir dos métodos en dos líneas, la caja creció 168 px y **atravesaba el borde del marco «Módulo Dominio»** | Error | **Modificar** | Detectado **renderizando**, como la fila 42. Se agrandó el marco, se bajaron 132 px los módulos Informes y Servicios externos y 117 px el de Seguridad, y las flechas con `exitY` relativo se recalcularon para el mismo punto absoluto (y = 479) |
| 48 | Prueba «un EMPLEADO solo registra sus propias horas» | Pasaba, pero **por el motivo equivocado**: el otro empleado ni siquiera participaba en el proyecto, así que lo frenaba la regla de asignación y no la de permiso | Error | **Modificar** | Lo destapó una **prueba de mutación**: al quitar la regla de permiso, la autoverificación falló con un error que no era el esperado. Se asigna al otro empleado antes de la prueba, para que el permiso sea la única barrera. Es el mismo patrón de la fila 38 |
| 49 | `proyecto = empleado and buscar_proyecto()` | Encadenar con `and` para ahorrar un `if` | Coherencia | **Modificar** | Hace lo correcto, pero hay que detenerse a descifrarlo. Se reemplazó por el `return` temprano que ya usa `asignar_a_departamento`: lo que se lee igual en todo el archivo se revisa más rápido |
| 50 | Planilla del proyecto | `valor` solo se asignaba en la rama de moneda extranjera y se usaba en otra rama con la misma condición | Coherencia | **Modificar** | Correcto hoy, pero un analizador lo marca como posible variable sin asignar, y un cambio en una de las dos condiciones la volvería real. `valor = 1.0` en la rama CLP |
| 51 | Mensaje al asignar a un proyecto | «Camila Reyes Ortiz quedó **asignado**…» | Coherencia | **Modificar** | El programa no sabe el género de nadie. Visto en la sesión real; ahora dice «ahora participa en el proyecto» |
| 52 | Guion de la sesión de prueba | En el caso «proyecto donde no participa», la IA escribió `x` como descripción: la acción se canceló y el caso no se probó | Error | **Modificar** | Una prueba que no llega al caso no prueba nada. Detectado al leer la salida, no al ver que «pasaba»: se cambió la entrada y apareció el rechazo esperado |
| 53 | Commits de las etapas 5c y 5d | El plan los pedía separados | Alcance | **Modificar el plan** | Separados, el commit de 5c dejaba `registrar_tiempo` apuntando a una lista ya borrada: un punto de retorno roto. Se hicieron juntos y se declaró. Lo mismo con las sub-etapas del menú, que tocan las mismas líneas |
| 54 | Arreglo del login con hash corrupto | La IA había dejado el hueco como «sospecha sin verificar» el 21-sep | Vulnerabilidad | **Modificar** | Se escribió primero la prueba y se corrió contra el código **anterior**: murió con traceback. Recién entonces se corrigió, y la misma prueba pasó. Sin ver la prueba fallar, no hay forma de saber que prueba el defecto |
| 55 | Firma de `autenticar` en el diagrama y en el código | El diagrama decía `autenticar(nombre, clave)` y el código `autenticar(nombre_usuario, clave)`. La revisión a ojo del 21-sep no lo vio | Coherencia | **Modificar** | Lo encontró un **comparador automático** escrito en esta auditoría: lee el diagrama y el código y compara nombre, visibilidad y parámetros de los 68 miembros. Se corrigió el código, porque `nombreUsuario` no cabe en la fila de la caja y todas las llamadas pasan el argumento por posición. Tras el cambio: 68 de 68 |

### Lo que agrega esta pasada

Un séptimo sesgo, que se suma a los de las secciones 3 y 5:

7. **Da por buenas sus propias cifras y sus propios planes.** Las filas 44, 45 y 46 son errores de la
   IA sobre trabajo de la IA: un plan que no se contrastó con el código, una suma hecha de memoria y
   una regla del proyecto olvidada al escribir el paso. Las tres, y la 55, las atrapó un control
   mecánico, no una relectura. **Lo que la IA escribió ayer se verifica igual que lo que sugiere hoy.**

Y una técnica nueva de prueba: **la mutación**. Que la autoverificación pase no dice nada si no se la
ha visto fallar. Romper la regla a propósito y mirar **qué** `assert` cae (fila 48) es lo que
distingue una prueba que protege la regla de una que pasa por casualidad.

---

## 7. El código cliente, revisado con los cinco aspectos del docente — 23-sep-2026

La lámina 31 del bloque 5 fija lo que hay que revisar en todo código que consume servicios, y la
lámina 35 pide pedirle a una IA que revise el cliente y anotar qué se decidió en cada aspecto. La
revisión la hizo Claude (Anthropic), modelo Opus 5.5, sobre `servicios.py` final. Cada decisión se
comprobó con la autoverificación y con un fallo provocado (`SALIDA_TERMINAL.md` §6).

| Aspecto | Qué se revisó | Problema detectado | Decisión | Fundamento técnico |
|---|---|---|---|---|
| **Credenciales** | Llaves de API y datos sensibles en el código o en el repositorio | Ninguna de las dos APIs pide llave, pero la configuración estaba escrita en constantes y no había cómo cambiarla sin tocar el código | **Modificar** | Las direcciones y el tiempo de espera se leen del entorno o de un `.env` que `.gitignore` excluye; `.env.example` trae los nombres y no los valores (láminas 20-21). Si un servicio pidiera llave, iría ahí (fila 40) |
| **Protocolo** | `https` en toda solicitud | Solo HTTPS en las direcciones por defecto, pero una variable de entorno podía cambiarlo a `http` | **Modificar** | `__consultar` rechaza, **antes de salir a la red**, cualquier dirección que no empiece con `https://`, con un mensaje que no la repite (lámina 24: por `http` la consulta y una llave viajan sin cifrar) |
| **Timeout** | Que ningún llamado espere para siempre | Ya existía, `(3.05, 10)` (filas 26-43); al volverlo configurable, un valor como `0`, `abc` o `61` lo habría anulado | **Adoptar**, con un control nuevo | Conexión fija en 3,05 s; lectura configurable, validada en (0, 60]. Fuera de eso, no se sale a la red |
| **Manejo de errores** | `try`, excepciones de lo concreto a lo general, que el sistema no se detenga | El manejo ya era completo (`Timeout` → `ConnectionError` → `RequestException`, código HTTP antes del cuerpo), pero ante una falla el dato simplemente faltaba | **Modificar** | Degradar antes que interrumpir (lámina 16): el último dato bueno de la sesión y, si no hay, el último guardado en la base, **siempre avisado como referencial**. Un error de quien pide (ciudad inválida) no se tapa con un dato viejo |
| **Uso de la respuesta** | Que se compruebe antes de usarla | Ya se comprobaban las claves, el tipo, `Infinity` y `NaN`, pero un tipo de cambio de un millón de pesos pasaba | **Modificar** | La función de validación `__extraer_valor` (láminas 26 y 35) agrega el rango (0, 1.000.000]; el dato se vuelve a validar al guardarse (`TipoCambio`, `RegistroClima`) y la base lo repite con `CHECK` |

### Filas nuevas (cierre de la Unidad 3)

| # | Aspecto revisado | Problema detectado | Tipo | Decisión | Fundamento técnico |
|---|---|---|---|---|---|
| 56 | Supresión de un falso positivo de SonarCloud | La IA marcó los dos S4487 con `# NOSONAR: se lee en autenticar()`; el analizador no acepta esa sintaxis y abrió dos issues nuevos (S7632) | Error | **Descartar** el comentario | El falso positivo se marca en la interfaz de SonarCloud con su justificación; un comentario que el propio analizador rechaza empeora el reporte que quería limpiar |
| 57 | Degradación en dos métodos públicos | La primera forma pensada anidaba un `try` dentro de `obtener_clima` y repetía la lógica de respaldo en `obtener_tipo_cambio` | Coherencia | **Modificar** | Un método privado `__con_respaldo(clave, consulta)` concentra la regla; el cuerpo del clima pasa sin cambios a `__clima_de`. Una regla en un lugar, y sin subir la complejidad cognitiva que SonarCloud ya marcó en este proyecto (S3776) |
| 58 | Pruebas con red real | Dos verificaciones fallaron porque mindicador.cl y Open-Meteo **se demoraron de verdad**; el programa respondió bien, pero la prueba dependía de la red | Error | **Modificar** | Las pruebas de lógica usan respuestas fijas con el formato real de las APIs (`api_fija`); la red real se prueba en una sesión aparte. Una prueba que falla por el clima de internet no prueba el código |
| 59 | Pruebas con una sola instancia del servicio | Con memoria de respaldo, las pruebas de fallos habrían **pasado degradando** en vez de fallar: la instancia compartida ya tenía el dato | Error | **Modificar** | Cada prueba de fallo usa una instancia nueva. Detectado antes de ejecutar, al razonar qué cambiaba la memoria: el mismo patrón que las filas 38 y 48 (pasar por el motivo equivocado) |
| 60 | Comparador UML ↔ código | El comparador escrito en la pasada 7 no veía las clases nuevas (tenía la lista fija) ni los atributos con anotación de tipo (`self.__ultimos: dict = {}`) | Error | **Modificar** | Ahora recorre todas las cajas del diagrama y reconoce `AnnAssign`: 89 de 89. Una herramienta de verificación también se verifica |
| 61 | Lector del `.env` | La opción obvia era instalar `python-dotenv` | Alcance | **Descartar** | Diez líneas de biblioteca estándar leen `CLAVE=VALOR`; una dependencia más es superficie de cadena de suministro (OWASP A03:2025) para algo trivial |
| 62 | El dato de la API guardado | El diseño inicial del cierre solo mostraba el dato; la guía pide «persistir datos localmente» y el docente muestra pedir → validar → **guardar** → informar | Alcance | **Modificar** | `RegistroClima` y `TipoCambio` con C, R y D, **sin U**: un dato que vino de la API es evidencia, igual que las horas. La guía y las láminas 16 y 29-30 son la fuente |
| 63 | Pruebas de configuración insegura | Para probar que una dirección `http` se rechaza, la IA escribió `"http://mindicador.cl/api"` como literal en la prueba; SonarCloud lo marcó como vulnerabilidad (S5332) y el Quality Gate cayó en Seguridad | Error | **Modificar** | La prueba arma la dirección insegura desde la segura (`URL_INDICADORES.replace("https", "http", 1)`): prueba lo mismo, sin dejar en el código un literal que cualquier analizador —o un copiar y pegar— trate como real. Confirmado con mutación: quitar la exigencia de `https` hace caer la prueba |
| 64 | Versiones exactas en `requirements.txt` | Al fijar las versiones (lámina 8), la IA congeló `requests` 2.32.5, `urllib3` 2.6.3 e `idna` 3.11, con 8 avisos de seguridad conocidos; lo encontró la consulta a OSV.dev de la pasada 8 | Vulnerabilidad | **Modificar** | Se subió a versiones sin avisos y se probó en un entorno aislado antes de cambiar el archivo. Fijar versiones protege contra cambios inesperados, pero también congela vulnerabilidades: hay que revisarlas contra una base de avisos |
| 65 | Pruebas de la fecha de la serie | Al exigir la fecha, las pruebas que debían fallar **por el valor** (tope, cero, `inf`) habrían fallado por la fecha ausente: la mutación del tope ya no se habría detectado | Error | **Modificar** | Se agregó una fecha válida a los 11 cuerpos de prueba para que fallen solo por lo que prueban. Se confirmó con mutación: quitar el tope vuelve a hacer caer su `assert` |
| 66 | Respuesta fija de las pruebas deterministas | `api_fija` informaba la fecha de hoy, así que no distinguía entre guardar la fecha de la API y guardar `date.today()` | Error | **Modificar** | La respuesta fija informa un sábado (19-09): la prueba solo pasa si el historial guarda esa fecha |
| 67 | Revisión por un agente independiente | La autoauditoría no había visto tres fallas Medias (sesión que no caduca en la pausa, clima sin rango, contacto visible para todos); las encontró un agente de contexto limpio | — | **Adoptar**, re-verificando | Cada hallazgo del agente se **reprodujo en ejecución** antes de aceptarlo. Quien construye tiende a confirmar lo que ya cree (Método Auditoría §1.2.5): la independencia encontró lo que la relectura no |
| 68 | Plan de corrección | El plan cambiaba el UML en una etapa posterior a la que exigía el UML igual al código: esa puerta habría fallado siempre | Error | **Modificar** | Lo detectó la autorrevisión del plan antes de ejecutarlo; el cambio del UML pasó a la misma etapa |
