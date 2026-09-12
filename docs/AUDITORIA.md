# Auditoría de seguridad — EcoTech Solutions

**Caso EcoTech Solutions · Evaluación Sumativa 2, Unidad 2 · TI3V21**
**Fecha:** 11 de septiembre de 2026 · **Alcance:** `ecotech.py` y `main.py`

> Hay una segunda pasada, del 12 de septiembre, en `AUDITORIA2.md`: permisos del archivo de la base,
> inyección de fórmulas en el CSV, escapes de terminal, costo del hash de claves y autenticación.
> Entra en lo que la sección 8 de este informe declaró fuera de alcance.

Revisión dirigida a dos cosas: el **encapsulamiento de los datos**, que evalúan los indicadores
2.1.2.G.3 y 2.1.2.I.4, y el **control de las entradas**, que evalúan el 2.1.4.G.7 y el 2.1.4.I.8.

El método fue ejecutar ataques concretos contra el código, no leerlo y opinar. Cada hallazgo de
abajo trae la reproducción exacta y se puede repetir delante del docente.

**Resultado: dos defectos graves, los dos corregidos, y tres observaciones que se documentan.**

| # | Hallazgo | Gravedad | Estado |
|---|---|---|---|
| 1 | El menú se cae con un entero grande | Grave | **Corregido** |
| 2 | Solo una de las cuatro áreas de permisos se comprobaba | Grave | **Corregido** |
| 3 | `isdigit()` acepta caracteres que `int()` rechaza | Leve | **Corregido** |
| 4 | Asociaciones mutables accesibles desde fuera de la clase | Observación | Se documenta |
| 5 | Datos de contacto en el resumen exportable | Observación | Se documenta |
| — | Inyección SQL | — | **Sin hallazgos** |
| — | Path traversal en la exportación del informe | — | **Sin hallazgos** |

---

## 1. Inyección SQL — sin hallazgos

Los catorce `execute()` de `ecotech.py` pasan los valores como parámetros `?`. Se probaron cargas
reales, no ejemplos de manual:

| Carga inyectada | Por dónde entró | Resultado |
|---|---|---|
| `Legal'); DROP TABLE empleado; --` | nombre de departamento | Guardado como texto. La tabla `empleado` intacta |
| `x'; DELETE FROM empleado WHERE '1'='1` | `Departamento.renombrar` | Guardado como texto. Los empleados intactos |
| `1 OR 1=1` | `Empleado.buscar(id)` | Devuelve `None`. Ninguna fila coincide |

Reproducción:

```python
import ecotech as E
d = E.Departamento("Legal'); DROP TABLE empleado; --")
d.guardar(admin)
d.renombrar("x'; DELETE FROM empleado WHERE '1'='1", admin)
print(len(E.Empleado.listar()))          # los empleados siguen ahí
print(E.Departamento.buscar(1).obtener_nombre())   # el veneno es un nombre, no una orden
```

**Por qué funciona.** El valor viaja por un canal distinto al de la consulta, así que el motor nunca
lo analiza como SQL. Hay dos refuerzos más:

- `Connection.execute` ejecuta **una sola** sentencia. Un `;` inyectado no encadenaría nada aunque
  llegara a interpretarse.
- La única interpolación en una sentencia es `f"SELECT {cls.COLUMNAS} FROM empleado ..."`.
  `COLUMNAS` es una constante de clase escrita por nosotros, jamás una entrada del usuario. Es el
  único lugar del archivo donde aparece una f-string dentro de SQL, y está así porque la lista de
  columnas no puede ir como parámetro: `?` sustituye valores, no identificadores.

## 2. Exportación del informe — sin hallazgos

`Informe.exportar` resuelve la ruta y recién entonces comprueba que siga dentro de la carpeta de
trabajo. Probado:

| Ruta pedida | Resultado |
|---|---|
| `../../fuga.csv` | Bloqueado |
| `/tmp/fuga.csv` | Bloqueado |
| `salida.csv` | Permitido |

El orden importa: comprobar antes de resolver no sirve, porque resolver es justamente lo que
colapsa los `..`.

---

## 3. Defecto 1 — El menú se caía con un entero grande · corregido

### Qué pasaba

Un entero de 25 dígitos pasaba `isdigit()`, pasaba las validaciones de dominio y reventaba al llegar
a SQLite con `OverflowError`, que **no estaba en la cadena de `except`**. El programa moría con
traceback en pantalla.

```
OverflowError: Python int too large to convert to SQLite INTEGER
```

Reproducción original, seis caminos distintos del menú:

| Opción | Campo | Llegaba a |
|---|---|---|
| 3, 4 | Id del departamento | `Departamento.buscar` |
| 7, 8, 9 | Id del empleado | `Empleado.buscar` |
| 5 | Salario | `Empleado.guardar` |

```bash
printf 's\n8\n9999999999999999999999999\n0\n' | python3 main.py     # antes: traceback
```

Esto rompía el indicador 2.1.4.G.7 en el punto exacto que evalúa: «evitar que el sistema se
interrumpa ante errores de ejecución».

### Cómo se corrigió

Las seis rutas cruzaban por un solo punto, así que la corrección va ahí y no en seis lugares.
Quedaron **tres capas**, cada una en su sitio:

| Capa | Dónde | Qué rechaza |
|---|---|---|
| Formato | `main.py`, `pedir_entero()` | Lo no decimal y todo lo que pase de `MAXIMO_ENTERO`, mil millones. Vuelve a preguntar |
| Regla de negocio | `ecotech.py`, `Empleado.__init__` | Salario fuera de `1 … SALARIO_MAXIMO`, cien millones. Lanza `ValueError` |
| Base de datos | `ESQUEMA`, tabla `empleado` | `CHECK (salario > 0 AND salario <= 100000000)` |

La segunda capa existe porque `pedir_entero` se puede saltar llamando a la clase desde otro
programa. La tercera, porque el objeto se puede saltar abriendo la base con otra herramienta.

Y como último recurso, `main.py` cerró la cadena con un `except Exception` que **nombra el tipo del
error y continúa**. No es `except: pass`: no silencia nada, imprime qué falló y devuelve el menú.
Con eso la promesa de no interrumpirse pasa a ser absoluta y no «para los errores que previmos».

### Evidencia después

```
Salario: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
Salario: 500000000
   ! Salario fuera de rango (1 a 100000000): 500000000
Salario: 1720000
   Empleado contratado con id 4.
```

Y saltándose la clase por completo:

```python
con.execute("INSERT INTO empleado (...) VALUES (...)", (..., 999_000_000))
# sqlite3.IntegrityError — el CHECK de la tabla lo rechaza
```

---

## 4. Defecto 2 — La autorización tenía un solo control real · corregido

### Qué pasaba

`Usuario._PERMISOS` declara cuatro módulos: `empleados`, `departamentos`, `proyectos` e `informes`.
Pero `tiene_permiso()` se invocaba en **dos** lugares de todo el sistema: al leer el salario y al
generar un informe. Los otros dos módulos estaban declarados y no se comprobaban nunca.

Medido con un usuario de rol `EMPLEADO`, que en la tabla solo tiene `proyectos`:

| Operación | Antes | Después |
|---|---|---|
| Leer el salario | bloqueado | bloqueado |
| Crear un departamento | **permitido** | bloqueado |
| Renombrar un departamento | **permitido** | bloqueado |
| Borrar un departamento | **permitido** | bloqueado |
| Borrar un empleado | **permitido** | bloqueado |

Dicho de la forma que más duele: **el sistema protegía un sueldo y regalaba el borrado.** Es el
hueco más visible frente al criterio 2.1.2, porque encapsular un atributo no sirve de nada si
cualquiera puede eliminar el registro entero.

### Cómo se corrigió

La comprobación estaba escrita dos veces con distinto mensaje. Antes de multiplicarla por cinco se
extrajo a una función de módulo:

```python
def autorizar(solicitante: "Usuario", modulo: str) -> None:
    if not solicitante.tiene_permiso(modulo):
        raise PermissionError(f"No autorizado para operar sobre {modulo}")
```

Los dos controles que ya existían se reescribieron con ella, y las cinco escrituras que estaban
abiertas ahora reciben un `solicitante`:

| Método | Módulo que exige |
|---|---|
| `Departamento.guardar` | `departamentos` |
| `Departamento.renombrar` | `departamentos` |
| `Departamento.eliminar` | `departamentos` |
| `Empleado.eliminar` | `empleados` |
| `Empleado.asignar_departamento` | `empleados` |
| `Empleado.obtener_salario` | `empleados` |
| `Informe.generar` | `informes` |

Los cuatro módulos de la tabla de permisos pasaron a usarse de verdad, y los roles empezaron a
significar algo distinto entre sí: un `GERENTE` administra departamentos pero no borra empleados; un
`EMPLEADO` no puede escribir nada.

> **Actualización, 12-sep-2026.** `Empleado.asignar_departamento` ya no existe: la tercera pasada
> (`AUDITORIA2.md`, sección 10) lo reemplazó por los métodos del UML. Hoy son nueve las operaciones
> protegidas: se suman `Departamento.agregar_empleado` y `quitar_empleado` (`empleados`) y
> `Departamento.asignar_gerente` (`departamentos`).

Esto **no rompe la correspondencia con el diagrama**, porque los métodos del CRUD ya estaban fuera
del UML por decisión declarada. La firma que sí está en el diagrama, `obtener_salario(solicitante)`,
no se tocó.

### La excepción deliberada: `actualizar_contacto`

`Empleado.actualizar_contacto` **no** recibe `solicitante`, y no es un olvido. Sobrescribe a
`Persona.actualizar_contacto`, que el diagrama fija en dos parámetros. Un tercer parámetro rompería
dos cosas a la vez: la sustituibilidad de la subclase, porque dejaría de poder usarse donde se
espera una `Persona`, y la correspondencia exacta que evalúa el criterio 2.1.1.

Es una decisión con costo: cambiar el correo de un empleado no pide permiso hoy. El dato es menos
sensible que el salario y menos destructivo que un borrado, así que se asume y se declara aquí en
vez de disimularlo. Si hubiera que cerrarlo, el lugar correcto sería el diagrama, no el código.

### Evidencia después

```
  leer salario             bloqueado
  renombrar departamento   bloqueado
  BORRAR departamento      bloqueado
  BORRAR empleado          bloqueado
  crear departamento       bloqueado
  empleado y departamento siguen en la base: True
```

La última línea importa: la excepción se lanza **antes** de tocar la base, así que un intento
rechazado no deja nada a medio escribir.

---

## 5. Observación 3 — `isdigit()` no era el predicado correcto · corregido

`"²".isdigit()` devuelve `True` y `int("²")` lanza `ValueError`. El bucle lo atrapaba, así que no
había caída, pero el usuario recibía `invalid literal for int()` en vez de un mensaje redactado.
`isdecimal()` es el predicado que corresponde: acepta exactamente los caracteres que `int()` sabe
convertir.

## 6. Observación 4 — Asociaciones mutables expuestas · se documenta

`Empleado._proyectos` y `Empleado._departamento` llevan un guion bajo y los escriben `Departamento`
y `Proyecto`. Se puede saltar la regla:

```python
empleado._proyectos.append(proyecto)   # Proyecto nunca se entera: sigue diciendo 0 empleados
```

**No se corrige, y el argumento es el que sigue.** Al unificar el código en un archivo, el guion
bajo simple pasó a significar exactamente lo que la convención de Python dice: interno al módulo.
Antes el acceso cruzaba módulos y era discutible; ahora no sale del archivo, que es el ámbito para
el que la convención existe.

Hacerlos privados obligaría a inventar métodos de acceso que el diagrama no tiene, y eso cuesta en
el criterio 2.1.1. Es un intercambio consciente entre dos indicadores, resuelto a favor del que pesa
más.

El contraste está en la misma clase: `Departamento.listar_empleados()` devuelve `list(...)`, una
copia, precisamente para que nadie modifique la lista interna desde fuera. Donde se pudo cerrar sin
inventar métodos, se cerró.

> **Actualización, 12-sep-2026.** La mitad de esta observación quedó cerrada por otra vía.
> `Empleado._departamento` y la lista interna de `Departamento` se borraron: la relación vive solo
> en la base, y `listar_empleados()` arma objetos nuevos desde las filas, así que no hay lista que
> manipular. Sigue vigente para `Empleado._proyectos`, porque `Proyecto` todavía vive en memoria.
> Detalle en `AUDITORIA2.md`, sección 10.

## 7. Observación 5 — Datos de contacto en el resumen · se documenta

`obtener_resumen()` emite nombre, correo y teléfono. Como `Informe` se construye llamando a ese
método, un informe de empleados exportado a CSV lleva los datos de contacto de toda la dotación.

Es el comportamiento que define el diagrama y la mitigación importante ya está puesta: **el salario
queda fuera del resumen**, por eso tiene su propio método con control de acceso. La regla implícita
del modelo es que el resumen es información de directorio interno, no información reservada.

---

## 8. Lo que esta auditoría dejó explícitamente fuera

- **Inicio de sesión y persistencia de `Usuario`.** La tabla `usuario` existe en el esquema, con su
  `UNIQUE` y su `CHECK` de rol, y ningún código la escribe. El solicitante del menú se construye
  fijo en `main.py`. Es Unidad 3 y se declara en vez de disimularse. Consecuencia honesta: hoy los
  permisos protegen contra el uso incorrecto, no contra un atacante, porque no hay quién verifique
  la identidad de quien dice ser el administrador.
- **Cifrado de los datos en reposo.** SQLite no lo trae y agregarlo excede la evaluación.
- **Concurrencia.** Un solo proceso escribe. Con varios, la conexión por operación deja ventanas
  entre el `buscar` y el `eliminar` del menú.

## 9. Cómo repetir esta auditoría

```bash
cd ecotech_new
rm -f ecotech.db
python3 ecotech.py     # la autoverificación incluye los cinco casos de permisos
python3 main.py        # teclear 25 dígitos en cualquier campo numérico
```

La autoverificación de `ecotech.py` quedó ampliada con los casos que esta auditoría destapó: el
salario desbordado y los cinco intentos de escritura sin permiso. Si alguien afloja una guarda, un
`assert` se cae.
