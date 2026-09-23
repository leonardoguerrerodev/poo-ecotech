# Salida de terminal — EcoTech Solutions

Evidencia de ejecución del indicador **2.1.3.G.5**, que exige las cuatro operaciones CRUD
verificadas, y del **2.1.4.G.7**, que exige validar las entradas y que el sistema no se interrumpa
ante errores. Las secciones 1 a 3 son de la Unidad 2 y muestran el menú de esa entrega, sin inicio
de sesión; **las secciones 4 a 6 son la Unidad 3** (3.1.1, 3.1.2 y 3.1.3). La 5 y la 6 son la
versión final: proyectos persistidos, y el clima y el pago calculados **por proyecto**.

Las dos corridas son reales y reproducibles desde cero:

```bash
cd ecotech_new
rm -f ecotech.db
python3 ecotech.py     # autoverificación
python3 main.py        # menú
```

---

## 1. Autoverificación

Corre sobre una base temporal que se borra al terminar. Comprueba trece rechazos de validación del
dominio (tres agregados el 15-sep-2026: un correo de más de 254 caracteres, un nombre con marca
invisible de dirección y un teléfono con dígitos no ASCII), cuatro reglas de credencial, **siete intentos de escritura sin permiso**, el ciclo CRUD completo
sobre `Empleado` y `Departamento`, y **que la relación entre los dos vive en la base**: un
departamento leído de nuevo con `buscar()` reporta el mismo gerente y la misma cantidad de
empleados que escribió otra instancia, el cargo de gerente queda vacante cuando la persona se
cambia de departamento o se borra, un gerente ajeno se rechaza, y ni un objeto sin guardar ni un
segundo `guardar()` llegan a la base.

```
$ python3 ecotech.py
OK · dominio · seguridad · CRUD sobre Empleado y Departamento
```

Los casos de permisos no se pueden mostrar desde el menú, porque el menú siempre opera como
`ADMIN_RRHH`. Salieron de la auditoría: los de departamentos y empleados, de la sección 2.2 de
`AUDITORIA.md`, y los tres de la relación, de la sección 2.8.

---

## 2. Sesión del menú

Recorrido completo, con entradas inválidas provocadas a propósito y tres acciones canceladas con
`x` a mitad de camino. El menú agrupa las opciones por operación: 1-3 crean, 4-5 leen, 6-8
actualizan y 9-10 eliminan.

Después de cada acción el menú pide **Enter** y recién entonces limpia la pantalla y redibuja el
menú. Para que la sesión se lea de corrido, cada una de esas limpiezas quedó condensada en una
sola línea `[pantalla limpia · menú]`: el menú completo se muestra solo la primera vez.

```

==================================================================
   EcoTech Solutions — Gestión de empleados
==================================================================
   C — CREAR                     U — ACTUALIZAR
    1. Datos de ejemplo           6. Renombrar departamento
    2. Departamento               7. Contacto del empleado
    3. Empleado (contratar)       8. Asignar a departamento

   R — LEER                      D — ELIMINAR
    4. Departamentos              9. Departamento
    5. Empleados                 10. Empleado

   Escriba "x" para cancelar la acción en curso   ·   0. salir
==================================================================

   Opción: 1
   Creados 2 departamentos y 3 empleados.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 4
   [1] Desarrollo Sostenible · 2 empleados
   [2] Investigación y Desarrollo · 1 empleado

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [1] Juanita Bravo Sepúlveda | jbravo@ecotech.cl | 987654321 | contrato: 2023-04-17

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 6
   (escriba x para cancelar)
   Id del departamento: abc
   ! Escriba un número entero, sin puntos ni letras.
   Id del departamento: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
   Id del departamento: 1
   Nuevo nombre: Innovación Sostenible
   Ahora se llama Innovación Sostenible.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 4
   [1] Innovación Sostenible · 2 empleados
   [2] Investigación y Desarrollo · 1 empleado

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 7
   (escriba x para cancelar)
   Id del empleado: 1
   Nuevo teléfono: 22 987 6543
   Nuevo correo: x
   Acción cancelada. No se guardó nada.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 7
   (escriba x para cancelar)
   Id del empleado: 1
   Nuevo teléfono: 22 987 6543
   Nuevo correo: juanita.bravo@ecotech.cl
   Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [1] Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 3
   (escriba x para cancelar)
   Nombre completo: Rodrigo Peña Alarcón
   Dirección: Manuel Montt 300, Ñuñoa
   Teléfono: +56 9 3344 5566
   Correo: X
   Acción cancelada. No se guardó nada.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 3
   (escriba x para cancelar)
   Nombre completo: Rodrigo Peña Alarcón
   Dirección: Manuel Montt 300, Ñuñoa
   Teléfono: +56 9 3344 5566
   Correo: rpena@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-03-10
   Salario: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
   Salario: 500000000
   ! Salario fuera de rango (1 a 100000000): 500000000

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 3
   (escriba x para cancelar)
   Nombre completo: Rodrigo Peña Alarcón
   Dirección: Manuel Montt 300, Ñuñoa
   Teléfono: +56 9 3344 5566
   Correo: rpena@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-03-10
   Salario: 1720000
   Empleado contratado con id 4.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [1] Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17
   [4] Rodrigo Peña Alarcón | rpena@ecotech.cl | 933445566 | contrato: 2025-03-10

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 9
   (escriba x para cancelar)
   Id del departamento: 1
   Departamento eliminado. Sus empleados siguen vigentes, sin departamento: la agregación es ON DELETE SET NULL.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 4
   [2] Investigación y Desarrollo · 1 empleado

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [1] Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17
   [4] Rodrigo Peña Alarcón | rpena@ecotech.cl | 933445566 | contrato: 2025-03-10

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 8
   (escriba x para cancelar)
   Id del empleado: 1
   Id del departamento: x
   Acción cancelada. No se guardó nada.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 8
   (escriba x para cancelar)
   Id del empleado: 1
   Id del departamento: 2
   Juanita Bravo Sepúlveda quedó en Investigación y Desarrollo.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 8
   (escriba x para cancelar)
   Id del empleado: 1
   Id del departamento: 2
   ! Juanita Bravo Sepúlveda ya pertenecía a Investigación y Desarrollo.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 4
   [2] Investigación y Desarrollo · 2 empleados

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 10
   (escriba x para cancelar)
   Id del empleado: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
   Id del empleado: 1
   Empleado eliminado, junto con sus registros de tiempo.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [4] Rodrigo Peña Alarcón | rpena@ecotech.cl | 933445566 | contrato: 2025-03-10

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 1
   ! Ya hay datos cargados: los ejemplos solo se crean sobre una base vacía.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 3
   (escriba x para cancelar)
   Nombre completo: Carla Reyes Ortiz
   Dirección: Pedro de Valdivia 55, Providencia
   Teléfono: +56 9 7412 8537
   Correo: creyes@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-06-02
   Salario: 1100000
   ! Ese correo ya está registrado. Use otro.

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 4
   [2] Investigación y Desarrollo · 1 empleado

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [4] Rodrigo Peña Alarcón | rpena@ecotech.cl | 933445566 | contrato: 2025-03-10

   Presione Enter para continuar...

   [pantalla limpia · menú]

   Opción: 0
   Hasta luego.
```

---

## 3. Qué demuestra cada tramo

| Línea de la sesión | Operación | Lo que prueba |
|---|---|---|
| `1` | **C** | Tres INSERT de empleados y dos de departamentos, con datos plausibles |
| `4` y `5` | **R** | SELECT con columnas nombradas, ordenado por nombre. El conteo por departamento sale de un `COUNT(*)`, no de una lista en memoria |
| `6` con `abc` | — | La entrada no numérica se rechaza y se vuelve a pedir |
| `6` con 25 dígitos | — | **La guarda de rango.** Sin ella, ese número llega a SQLite y mata el programa con `OverflowError` |
| `6` con `1` | **U** | UPDATE del nombre, previa validación con la misma función que usa el constructor |
| `7` con `x` en el correo | — | **Cancelación.** El teléfono ya estaba tecleado, pero la acción se corta antes del UPDATE y vuelve al menú |
| `7` completo | **U** | El teléfono entra como `22 987 6543` y queda guardado como `229876543`. La normalización sobrevive al viaje a la base |
| `3` con `X` en el correo | — | La cancelación no distingue mayúsculas, y ocurre antes de construir el `Empleado` |
| `3` con salario de 25 dígitos | — | **Primera capa**, en el menú: rechaza el formato y vuelve a preguntar sin perder lo ya tecleado |
| `3` con salario `500000000` | — | **Segunda capa**, en la clase: pasa el formato pero rompe la regla de negocio. La operación se aborta y el menú sigue vivo |
| `3` con salario válido | **C** | El mismo flujo, ahora exitoso, con id 4 asignado por SQLite. El listado confirma que ninguno de los dos intentos anteriores dejó un registro a medias |
| `9` | **D** | Se borra el departamento y **los cuatro empleados siguen ahí**. Es la agregación del diagrama: `ON DELETE SET NULL` |
| `8` con `x` en el departamento | — | Cancelación en el segundo dato de la acción, con el primero ya validado |
| `8` completo | **U** | `Departamento.agregar_empleado()`, el método del UML, escribe la clave foránea. El departamento pasa de uno a dos empleados |
| `8` repetido | — | Asignar a alguien donde ya estaba afecta cero filas: el método devuelve `False` y el menú lo dice, en vez de anunciar un cambio que no ocurrió |
| `10` con 25 dígitos | — | La misma guarda, ahora sobre un identificador |
| `10` con `1` | **D** | DELETE del empleado |
| `1` repetido | — | El candado de base vacía: no escribe nada, así que no quedan departamentos duplicados |
| `3` con el correo de Camila | — | `sqlite3.IntegrityError` por el `UNIQUE` del correo. El menú imprime el motivo y sigue vivo, y los listados siguientes confirman que no quedó nada a medias |
| `0` | — | Salida limpia |

**Las tres capas de validación, visibles en una sola sesión.** El formato lo juzga el menú y se puede
reintentar en el sitio. La regla de negocio la juzga la clase y aborta la operación. La restricción
la juzga la base y devuelve un `IntegrityError`. Ninguna de las tres interrumpe el programa.

---

## 4. Unidad 3 — inicio de sesión, APIs y errores de red

> Registro del 21-sep-2026. Desde el 23-sep-2026 las opciones 11 y 12 ya no piden una ciudad o una
> moneda sueltas: trabajan sobre un **proyecto** guardado, con su ciudad y su moneda. La sesión
> vigente es la de la **sección 5**; esta se conserva como evidencia del login, el bloqueo y la red.

Corridas del 21-sep-2026 sobre una base temporal nueva, **con red real** contra Open-Meteo y
mindicador.cl. Las entradas se escribieron con un guion que reemplaza `input` y `getpass`: las
claves aparecen como `••••••••••` porque en la terminal real no tienen eco. La inactividad se
simuló adelantando el reloj 700 segundos, más que los 10 minutos del límite.

```bash
python3 ecotech.py     # OK · dominio · seguridad · CRUD sobre Empleado y Departamento · inicio de sesión y bloqueo
python3 servicios.py   # OK · APIs · códigos HTTP · errores de red · entradas y respuestas validadas
```

### 4.1 Sesión completa con red

```

   Configuración inicial: cree la cuenta de administrador (ADMIN_RRHH).
   Usuario (3 a 20: minúsculas, números, . _ -): rrhh.admin
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   ! La clave no cumple la política de seguridad
   Usuario (3 a 20: minúsculas, números, . _ -): rrhh.admin
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   Cuenta creada. Ahora inicie sesión.

   Inicio de sesión — EcoTech Solutions
   Usuario: rrhh.admin
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: rrhh.admin
   Clave: ••••••••••

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 1
   Creados 2 departamentos y 3 empleados.

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 11
   (escriba x para cancelar)
   Ciudad de la faena: Valparaíso
   Valparaíso, Chile: despejado, 18.6 °C, humedad 55 %, viento 24.7 km/h.
   Condiciones aptas para trabajo en terreno.

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 11
   (escriba x para cancelar)
   Ciudad de la faena: Xyzzyqwerty
   ! No se encontró la ciudad 'Xyzzyqwerty'

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 11
   (escriba x para cancelar)
   Ciudad de la faena: Santiago; DROP TABLE empleado
   ! Ciudad inválida: de 2 a 80 letras, con espacios, guion, punto o apóstrofo

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 12
   (escriba x para cancelar)
   Id del empleado: 1
   Moneda (USD, EUR, UF): usd
   Juanita Bravo Sepúlveda: 1,450,000 CLP = 1,512.91 USD  (1 USD = 958.42 CLP hoy)

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 12
   (escriba x para cancelar)
   Id del empleado: 1
   Moneda (USD, EUR, UF): JPY
   ! Moneda no soportada. Use: USD, EUR, UF

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 14
   (escriba x para cancelar)
   Usuario (3 a 20: minúsculas, números, . _ -): c.rojas
   Rol (1 ADMIN_RRHH · 2 GERENTE · 3 EMPLEADO): 2
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   Usuario creado con id 2.

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 14
   (escriba x para cancelar)
   Usuario (3 a 20: minúsculas, números, . _ -): c.rojas
   Rol (1 ADMIN_RRHH · 2 GERENTE · 3 EMPLEADO): 3
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   ! Ese nombre de usuario ya existe. Use otro.

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 13
   (escriba x para cancelar)
   Dotación EcoTech (2026-09-21)
   Departamento: Desarrollo Sostenible | Gerente: sin gerente | Empleados: 2
   Departamento: Investigación y Desarrollo | Gerente: sin gerente | Empleados: 1
   Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   Juanita Bravo Sepúlveda | jbravo@ecotech.cl | 987654321 | contrato: 2023-04-17
   ¿Exportar a informe_dotacion.csv? (s/n): n

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 5
   ! Sesión cerrada por inactividad. Inicie sesión de nuevo.

   Inicio de sesión — EcoTech Solutions
   Usuario: c.rojas
   Clave: ••••••••••

[pantalla limpia · menú · sesión: c.rojas]

   Opción: 13
   (escriba x para cancelar)
   Dotación EcoTech (2026-09-21)
   Departamento: Desarrollo Sostenible | Gerente: sin gerente | Empleados: 2
   Departamento: Investigación y Desarrollo | Gerente: sin gerente | Empleados: 1
   Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   Juanita Bravo Sepúlveda | jbravo@ecotech.cl | 987654321 | contrato: 2023-04-17
   ¿Exportar a informe_dotacion.csv? (s/n): n

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: c.rojas]

   Opción: 12
   ! No autorizado para operar sobre empleados

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: c.rojas]

   Opción: 3
   ! No autorizado para operar sobre empleados

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: c.rojas]

   Opción: 11
   (escriba x para cancelar)
   Ciudad de la faena: Punta Arenas
   Punta Arenas, Chile: nublado, 5.0 °C, humedad 55 %, viento 8.9 km/h.
   Condiciones aptas para trabajo en terreno.

   Presione Enter para continuar...

[pantalla limpia · menú · sesión: c.rojas]

   Opción: 4
   ! Sesión cerrada por inactividad. Inicie sesión de nuevo.

   Inicio de sesión — EcoTech Solutions
   Usuario: c.rojas
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: c.rojas
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: c.rojas
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: c.rojas
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: c.rojas
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: c.rojas
   Clave: ••••••••••
   ! Credenciales inválidas o cuenta bloqueada temporalmente.
   Usuario: rrhh.admin
   Clave: ••••••••••

[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 0
   Hasta luego.
```

### 4.2 La misma sesión con la red cortada

`HTTPS_PROXY=http://127.0.0.1:9` hace que toda solicitud falle al conectar. Extracto de las líneas
con opciones y mensajes:

```
   Opción: 11
   Ciudad de la faena: Valparaíso
   ! No hay conexión con el servicio externo. Revise la red.
   Opción: 1
   Opción: 12
   Moneda (USD, EUR, UF): EUR
   ! No hay conexión con el servicio externo. Revise la red.
   Opción: 0
```

Y el tiempo de espera, contra una dirección que no responde (`10.255.255.1`):

```
ServicioNoDisponible: El servicio externo no respondió a tiempo. Intente más tarde.
real    0m3,286s
```

### 4.3 Qué demuestra cada tramo

| Tramo | Indicador | Qué se ve |
|---|---|---|
| Configuración inicial con clave corta | 3.1.2.G.14 | la política de claves rechaza la primera y el programa vuelve a preguntar |
| Primer login con clave equivocada | 3.1.2.G.14 | mensaje único, sin decir si falló el usuario o la clave |
| Opción 11, Valparaíso y Punta Arenas | 3.1.1.G.11 y G.12 | solicitud HTTP real, JSON procesado, datos elegidos (estado, temperatura, humedad, viento) y convertidos en una decisión: apto o no para trabajo en terreno |
| Opción 11 con `Xyzzyqwerty` | 3.1.3.G.18 | la API responde `200` sin resultados y el sistema lo informa sin caerse |
| Opción 11 con `Santiago; DROP TABLE empleado` | 3.1.2.G.14 | la entrada se rechaza antes de salir a la red |
| Opción 12, pago en USD | 3.1.1.G.12 | el tipo de cambio del día se integra con un dato de la base, el sueldo, leído con permiso |
| Opción 12 con `JPY` | 3.1.2.G.14 | lista blanca de monedas |
| Opción 14 dos veces con `c.rojas` | 3.1.2.G.14 | crear cuentas es de RRHH; el nombre repetido lo frena el `UNIQUE` con su propio mensaje |
| Inactividad y nuevo login como gerente | 3.1.2.G.15 | la sesión caduca; el gerente genera el informe (sin sueldos) pero **no** llega a pagos ni a contratar, y se le niega antes de pedirle un dato |
| Cinco claves malas y luego la correcta | 3.1.2.G.14 | la cuenta queda bloqueada: ni la clave correcta entra |
| Sección 4.2 | 3.1.3.G.17 | sin red y con tiempo agotado, mensaje claro y el menú sigue |

---

## 5. Unidad 3 final — proyectos, horas y servicios por proyecto

Corridas del 23-sep-2026 sobre una base temporal nueva, **con red real**. Mismo método que la
sección 4: un guion reemplaza `input` y `getpass`, y cada redibujo del menú se condensa en una línea.
Los números de clima y tipo de cambio son los de ese día.

```bash
python3 ecotech.py     # OK · dominio · seguridad · CRUD sobre Empleado y Departamento · proyectos y horas · inicio de sesión y bloqueo
python3 servicios.py   # OK · APIs · códigos HTTP · errores de red · entradas y respuestas validadas
```

El menú de esta versión:

```
   S — SERVICIOS EXTERNOS        A — ADMINISTRACIÓN
   11. Clima del proyecto        13. Informe de dotación
   12. Planilla en su moneda     14. Crear usuario

   P — PROYECTOS
   15. Crear proyecto            18. Quitar empleado
   16. Proyectos                 19. Registrar horas
   17. Asignar empleado          20. Eliminar proyecto
```

### 5.1 Sesión de RRHH (`ADMIN_RRHH`)

```
   Configuración inicial: cree la cuenta de administrador (ADMIN_RRHH).
   Usuario (3 a 20: minúsculas, números, . _ -): rrhh.admin
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   Cuenta creada. Ahora inicie sesión.

   Inicio de sesión — EcoTech Solutions
   Usuario: rrhh.admin
   Clave: ••••••••••
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 1
   Creados 2 departamentos, 3 empleados y 2 proyectos.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 16
   [1] Proyecto: Parque Eólico Costero | Descripción: Montaje de aerogeneradores en el litoral | Ciudad: Valparaíso | Moneda: CLP | Inicio: 2024-02-05 | Empleados: 2 | Horas consumidas: 0.00
   [2] Proyecto: Planta Solar Castilla | Descripción: Asesoría en eficiencia energética | Ciudad: Madrid | Moneda: EUR | Inicio: 2024-05-06 | Empleados: 2 | Horas consumidas: 0.00

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 15
   (escriba x para cancelar)
   Nombre: Relleno Sanitario Sur
   Descripción: Monitoreo de gases
   Inicio (AAAA-MM-DD): 2025-03-01
   Ciudad donde se ejecuta: Temuco
   Moneda de pago (CLP, USD, EUR): usd
   Proyecto creado con id 3.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 17
   (escriba x para cancelar)
   Id del empleado: 3
   Id del proyecto: 1
   Camila Reyes Ortiz ahora participa en el proyecto 1.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 17
   (escriba x para cancelar)
   Id del empleado: 3
   Id del proyecto: 1
   ! Camila Reyes Ortiz ya estaba en ese proyecto.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 18
   (escriba x para cancelar)
   Id del empleado: 3
   Id del proyecto: 1
   Camila Reyes Ortiz salió del proyecto; sus horas ya registradas se conservan.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 19
   (escriba x para cancelar)
   Id del empleado: 1
   Id del proyecto: 1
   Fecha (AAAA-MM-DD): 2025-06-02
   Horas: 7,5
   Descripción: Montaje de torres
   Registradas 7.5 h. El proyecto suma 7.50 h.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 19
   (escriba x para cancelar)
   Id del empleado: 1
   Id del proyecto: 1
   Fecha (AAAA-MM-DD): 2025-06-03
   Horas: abc
   ! Escriba las horas como número, por ejemplo 7.5.
   Horas: 25
   Descripción: Turno doble
   ! Horas inválidas: 25.0

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 20
   (escriba x para cancelar)
   Id del proyecto: 1
   ! El proyecto tiene horas registradas: no se puede eliminar

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 20
   (escriba x para cancelar)
   Id del proyecto: 3
   Proyecto eliminado, junto con sus asignaciones.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 11
   (escriba x para cancelar)
   Id del proyecto: 1
   Valparaíso, Chile: nublado, 18.4 °C, humedad 54 %, viento 13.2 km/h.
   Condiciones aptas para trabajo en terreno.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 11
   (escriba x para cancelar)
   Id del proyecto: 2
   Madrid, España: nublado, 27.1 °C, humedad 20 %, viento 0.8 km/h.
   Condiciones aptas para trabajo en terreno.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 12
   (escriba x para cancelar)
   Id del proyecto: 1
   Planilla en CLP: el proyecto se paga en pesos, sin conversión.
   Ignacio Fuentes Cárdenas: 1,980,000 CLP
   Juanita Bravo Sepúlveda: 1,450,000 CLP

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 12
   (escriba x para cancelar)
   Id del proyecto: 2
   Planilla en EUR  (1 EUR = 1,081.49 CLP hoy)
   Camila Reyes Ortiz: 1,260,000 CLP = 1,165.06 EUR
   Ignacio Fuentes Cárdenas: 1,980,000 CLP = 1,830.81 EUR

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 13
   (escriba x para cancelar)
   Dotación EcoTech (2026-09-23)
   Departamento: Desarrollo Sostenible | Gerente: sin gerente | Empleados: 2
   Departamento: Investigación y Desarrollo | Gerente: sin gerente | Empleados: 1
   Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   Juanita Bravo Sepúlveda | jbravo@ecotech.cl | 987654321 | contrato: 2023-04-17
   Proyecto: Parque Eólico Costero | Descripción: Montaje de aerogeneradores en el litoral | Ciudad: Valparaíso | Moneda: CLP | Inicio: 2024-02-05 | Empleados: 2 | Horas consumidas: 7.50
   Proyecto: Planta Solar Castilla | Descripción: Asesoría en eficiencia energética | Ciudad: Madrid | Moneda: EUR | Inicio: 2024-05-06 | Empleados: 2 | Horas consumidas: 0.00
   ¿Exportar a informe_dotacion.csv? (s/n): n

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 14
   (escriba x para cancelar)
   Usuario (3 a 20: minúsculas, números, . _ -): j.bravo
   Rol (1 ADMIN_RRHH · 2 GERENTE · 3 EMPLEADO): 3
   Id del empleado: 1
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   Usuario creado con id 2.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 14
   (escriba x para cancelar)
   Usuario (3 a 20: minúsculas, números, . _ -): j.bravo.dos
   Rol (1 ADMIN_RRHH · 2 GERENTE · 3 EMPLEADO): 3
   Id del empleado: 1
   Clave (12 o más, con 3 de: minúscula, mayúscula, número, símbolo): ••••••••••
   Repita la clave: ••••••••••
   ! Ese empleado ya tiene una cuenta.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 16
   [1] Proyecto: Parque Eólico Costero | Descripción: Montaje de aerogeneradores en el litoral | Ciudad: Valparaíso | Moneda: CLP | Inicio: 2024-02-05 | Empleados: 2 | Horas consumidas: 7.50
   [2] Proyecto: Planta Solar Castilla | Descripción: Asesoría en eficiencia energética | Ciudad: Madrid | Moneda: EUR | Inicio: 2024-05-06 | Empleados: 2 | Horas consumidas: 0.00

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: rrhh.admin]

   Opción: 0
   Hasta luego.
```

### 5.2 Sesión de la cuenta `EMPLEADO` creada en la 5.1

La cuenta `j.bravo` quedó vinculada al empleado 1, Juanita Bravo, que participa en el proyecto 1 y no
en el 2.

```
   Inicio de sesión — EcoTech Solutions
   Usuario: j.bravo
   Clave: ••••••••••
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 19
   (escriba x para cancelar)
   Registro a nombre de Juanita Bravo Sepúlveda.
   Id del proyecto: 1
   Fecha (AAAA-MM-DD): 2025-06-04
   Horas: 2
   Descripción: Informe de avance
   Registradas 2 h. El proyecto suma 9.50 h.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 19
   (escriba x para cancelar)
   Registro a nombre de Juanita Bravo Sepúlveda.
   Id del proyecto: 2
   Fecha (AAAA-MM-DD): 2025-06-04
   Horas: 1
   Descripción: Visita a terreno
   ! El empleado no está asignado a ese proyecto

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 15
   ! No autorizado para operar sobre proyectos

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 11
   ! No autorizado para operar sobre proyectos

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 12
   ! No autorizado para operar sobre empleados

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 19
   (escriba x para cancelar)
   Registro a nombre de Juanita Bravo Sepúlveda.
   Id del proyecto: x
   Acción cancelada. No se guardó nada.

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 16
   [1] Proyecto: Parque Eólico Costero | Descripción: Montaje de aerogeneradores en el litoral | Ciudad: Valparaíso | Moneda: CLP | Inicio: 2024-02-05 | Empleados: 2 | Horas consumidas: 9.50
   [2] Proyecto: Planta Solar Castilla | Descripción: Asesoría en eficiencia energética | Ciudad: Madrid | Moneda: EUR | Inicio: 2024-05-06 | Empleados: 2 | Horas consumidas: 0.00

   Presione Enter para continuar...
[pantalla limpia · menú · sesión: j.bravo]

   Opción: 0
   Hasta luego.
```

### 5.3 Las opciones por proyecto con la red caída

`requests.get` reemplazado para que lance `ConnectionError` (opciones 11 y 12 en EUR) y `Timeout`
(opción 11). Líneas de mensaje, sin tracebacks y sin la URL ni el texto interno de la excepción:

```
   ! No hay conexión con el servicio externo. Revise la red.
   ! No hay conexión con el servicio externo. Revise la red.
   ! El servicio externo no respondió a tiempo. Intente más tarde.
```

### 5.4 Qué demuestra cada tramo

| Tramo | Indicador | Qué se ve |
|---|---|---|
| Opción 1 y opción 16 | 2.1.3.G.5 | la siembra crea dos proyectos con ciudad y moneda, y el listado los lee **de la base** con sus empleados y horas |
| Opción 15 con `usd` | 2.1.3.G.5 · 2.1.4.G.7 | C de `Proyecto`; la moneda se normaliza y se valida contra la lista `CLP, USD, EUR` |
| Opción 17 dos veces y opción 18 | 2.1.1.G.1 | la asociación «participa en» vive en `empleado_proyecto`: asignar dos veces se informa, quitar conserva las horas |
| Opción 19 con `7,5`, con `abc` y con `25` | 2.1.4.G.7 | coma decimal aceptada; texto y 25 h rechazados sin cerrar el menú |
| Opción 20 sobre el proyecto 1 y el 3 | 2.1.3.G.5 | D de `Proyecto`: con horas imputadas se rechaza (la historia no se borra); sin horas se elimina |
| Opción 11 sobre los proyectos 1 y 2 | 3.1.1.G.11 · G.12 | el clima se pide para **la ciudad del proyecto** guardada en la base, no para un texto suelto |
| Opción 12 en CLP y en EUR | 3.1.1.G.12 | la planilla del equipo en **la moneda del país del proyecto**: CLP sin consultar la API, EUR con una sola consulta de tipo de cambio para todo el equipo |
| Opción 13 | 3.1.2.G.15 | el informe incluye los proyectos y sigue sin sueldos |
| Opción 14 dos veces sobre el empleado 1 | 3.1.2.G.14 | una cuenta `EMPLEADO` exige un empleado; el segundo intento lo frena el `UNIQUE` con su propio mensaje |
| 5.2, opción 19 | 3.1.2.G.15 | el `EMPLEADO` registra **sus** horas sin elegir a quién: el sistema toma el empleado de su cuenta |
| 5.2, opción 19 en el proyecto 2 | 2.1.4.G.7 | no puede imputar horas a un proyecto donde no participa |
| 5.2, opciones 15, 11 y 12 | 3.1.2.G.15 | denegadas **antes de pedir un dato**: el `EMPLEADO` ya no consulta la API de clima ni ve sueldos |
| 5.2, `x` en la opción 19 | 2.1.4.G.7 | cancelar sigue funcionando |
| Sección 5.3 | 3.1.3.G.17 | sin red y con tiempo agotado, mensaje fijo y el menú sigue |

---

## 6. Unidad 3, cierre — historial de las APIs y fallos provocados

Corridas del 23-sep-2026, regeneradas tras la corrección de la pasada 8, con el mismo guion de entradas (`docs/herramientas/driver.py`), sobre bases
temporales. Son los **fallos provocados** que pide la lámina 35 del docente: la red se corta o se
configura mal a propósito, y se muestra qué hace el sistema. Solo las líneas de cada acción.

### 6.1 El dato de la API se valida y se guarda (C, R y D, sin U)

Las respuestas de las APIs son fijas y tienen el formato real de Open-Meteo y mindicador.cl, para que
la corrida sea reproducible (la API fija informa el sábado 19-09-2026: el historial guarda
esa fecha, no la de hoy); la sesión con red real es la de la sección 5.

```
   Opción: 1
   Creados 2 departamentos, 3 empleados y 2 proyectos.

   Opción: 11
   Id del proyecto: 1
   Valparaíso, Chile: nublado, 17.0 °C, humedad 61 %, viento 12.5 km/h.
   Condiciones aptas para trabajo en terreno.
   Guardado en el historial del proyecto (registro 1).

   Opción: 12
   Id del proyecto: 2
   Tipo de cambio del 19-09-2026 guardado en el historial.
   Planilla en EUR  (1 EUR = 1,081.49 CLP)
   Camila Reyes Ortiz: 1,260,000 CLP = 1,165.06 EUR
   Ignacio Fuentes Cárdenas: 1,980,000 CLP = 1,830.81 EUR

   Opción: 21
   Guardados: 1 · ya registrados: 1 · descartados: 0

   Opción: 22
   Id del proyecto: 1
   [1] Clima 2026-09-23 20:13 | Valparaíso, Chile | nublado, 17.0 °C, humedad 61 %, viento 12.5 km/h | apto para terreno

   Opción: 23
   [1] Tipo de cambio 2026-09-19 | 1 EUR = 1,081.49 CLP
   [2] Tipo de cambio 2026-09-19 | 1 USD = 945.87 CLP

   Opción: 24
   Id del registro de clima: 1
   Registro de clima eliminado.

   Opción: 22
   Id del proyecto: 1
   (el proyecto no tiene consultas de clima guardadas)

   Opción: 25
   Id del tipo de cambio: 2
   Tipo de cambio eliminado.

   Opción: 23
   [1] Tipo de cambio 2026-09-19 | 1 EUR = 1,081.49 CLP

   Opción: 11
   Id del proyecto: 1
   Valparaíso, Chile: nublado, 17.0 °C, humedad 61 %, viento 12.5 km/h.
   Condiciones aptas para trabajo en terreno.
   Guardado en el historial del proyecto (registro 1).

   Opción: 0
   Hasta luego.
```

### 6.2 Sesión nueva sin red: el respaldo sale de la base

El programa se cerró y se volvió a abrir, así que la memoria de la sesión está vacía, y
`requests.get` lanza `ConnectionError`.

```
   Opción: 11
   Id del proyecto: 1
   ! Valor referencial: el servicio no respondió y se muestra el último dato guardado en la base.
   Clima 2026-09-23 20:13 | Valparaíso, Chile | nublado, 17.0 °C, humedad 61 %, viento 12.5 km/h | apto para terreno

   Opción: 12
   Id del proyecto: 2
   ! Valor referencial: el servicio no respondió y se muestra el último dato guardado en la base.
   Tipo de cambio 2026-09-19 | 1 EUR = 1,081.49 CLP
   Planilla en EUR  (1 EUR = 1,081.49 CLP)
   Camila Reyes Ortiz: 1,260,000 CLP = 1,165.06 EUR
   Ignacio Fuentes Cárdenas: 1,980,000 CLP = 1,830.81 EUR

   Opción: 21
   ! USD: No hay conexión con el servicio externo. Revise la red.
   ! EUR: No hay conexión con el servicio externo. Revise la red.
   Guardados: 0 · ya registrados: 0 · descartados: 2

   Opción: 11
   Id del proyecto: 2
   ! No hay conexión con el servicio externo. Revise la red.

   Opción: 0
   Hasta luego.
```

### 6.3 La red se cae a mitad de la sesión: el respaldo sale de la memoria

Las tres primeras solicitudes responden y desde la cuarta la red está caída.

```
   Opción: 1
   Creados 2 departamentos, 3 empleados y 2 proyectos.

   Opción: 11
   Id del proyecto: 1
   Valparaíso, Chile: nublado, 17.0 °C, humedad 61 %, viento 12.5 km/h.
   Condiciones aptas para trabajo en terreno.
   Guardado en el historial del proyecto (registro 1).

   Opción: 12
   Id del proyecto: 2
   Tipo de cambio del 19-09-2026 guardado en el historial.
   Planilla en EUR  (1 EUR = 1,081.49 CLP)
   Camila Reyes Ortiz: 1,260,000 CLP = 1,165.06 EUR
   Ignacio Fuentes Cárdenas: 1,980,000 CLP = 1,830.81 EUR

   Opción: 11
   Id del proyecto: 1
   ! Valor referencial: el servicio no respondió y se muestra el último dato obtenido en esta sesión.
   Valparaíso, Chile: nublado, 17.0 °C, humedad 61 %, viento 12.5 km/h.
   Condiciones aptas para trabajo en terreno.

   Opción: 12
   Id del proyecto: 2
   ! Valor referencial: el servicio no respondió y se muestra el último dato obtenido en esta sesión.
   Planilla en EUR  (1 EUR = 1,081.49 CLP)
   Camila Reyes Ortiz: 1,260,000 CLP = 1,165.06 EUR
   Ignacio Fuentes Cárdenas: 1,980,000 CLP = 1,830.81 EUR

   Opción: 11
   Id del proyecto: 2
   ! No hay conexión con el servicio externo. Revise la red.

   Opción: 0
   Hasta luego.
```

### 6.4 Configuración insegura: `ECOTECH_URL_INDICADORES=http://…`

```
   Opción: 1
   Creados 2 departamentos, 3 empleados y 2 proyectos.

   Opción: 21
   ! USD: La configuración del servicio externo no es válida: se exige https y un tiempo de espera de 0 a 60 segundos. Revise el .env.
   ! EUR: La configuración del servicio externo no es válida: se exige https y un tiempo de espera de 0 a 60 segundos. Revise el .env.
   Guardados: 0 · ya registrados: 0 · descartados: 2

   Opción: 12
   Id del proyecto: 2
   ! La configuración del servicio externo no es válida: se exige https y un tiempo de espera de 0 a 60 segundos. Revise el .env.

   Opción: 0
   Hasta luego.
```

### 6.5 Qué demuestra cada tramo

| Tramo | Indicador | Qué se ve |
|---|---|---|
| 6.1, opciones 11 y 12 | 3.1.1.G.12 | el dato de la API se valida otra vez y se **guarda**: pedir, validar, guardar e informar (láminas 29-30) |
| 6.1, opción 21 | 3.1.1.G.12 | «Guardados · ya registrados · descartados»: nada se descarta en silencio (lámina 30) |
| 6.1, opciones 12 y 23 | 3.1.1.G.12 | el tipo de cambio se guarda con la **fecha que informa la API** (19-09), no con la de hoy |
| 6.1, opciones 22 a 25 | 2.1.3.G.5 | R y D del historial; no hay U, porque un dato de la API es evidencia |
| 6.2 | 3.1.3.G.17 | sin red y sin memoria, el último valor **guardado en la base**, avisado como referencial, y con error claro cuando no hay nada guardado (lámina 16) |
| 6.3 | 3.1.3.G.17 | degradar antes que interrumpir: el último dato de la sesión, marcado |
| 6.4 | 3.1.2.G.14 · 3.1.3.G.18 | una dirección `http` se rechaza **antes** de salir a la red; el mensaje no repite la dirección y el menú sigue |
