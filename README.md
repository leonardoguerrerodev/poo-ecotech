# EcoTech Solutions — gestión de empleados

Sistema de gestión de personal en Python, implementado sobre el modelo de clases UML
de la asignatura *Programación Orientada a Objeto Seguro*. Persistencia en SQLite con
la librería estándar: **sin dependencias externas**.

## Uso

```bash
python3 ecotech.py   # autoverificación sobre una base temporal
python3 main.py      # menú de la aplicación (crea ./ecotech.db en modo 0600)
```

Requiere Python 3.10 o superior (usa `int | None`).

## Estructura

| Ruta | Contenido |
|---|---|
| `ecotech.py` | Dominio completo: validaciones, esquema SQL, las 8 clases del UML y su CRUD |
| `main.py` | Interfaz de terminal. No contiene una sola sentencia SQL |
| `comentado/` | Espejo de ambos archivos con comentarios que justifican cada decisión |
| `diagramas/` | Modelo de clases en formato drawio |
| `docs/` | Análisis del código generado con IA, las dos auditorías de seguridad, el guion de defensa y la sesión de terminal |

El espejo de `comentado/` es el mismo código con la justificación encima. Que siga siendo el mismo
se comprueba así:

```bash
diff <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' ecotech.py) \
     <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' comentado/ecotech.py)
```

### `ecotech.py`

Cuatro secciones en orden:

1. **Validaciones y autorización.** Expresiones regulares de correo, usuario y teléfono;
   `texto()` normaliza y acota cadenas y rechaza caracteres de control; `canonico()` reduce un
   teléfono a sus 9 dígitos; `sin_formula()` neutraliza las celdas que una planilla evaluaría;
   `autorizar()` lanza `PermissionError` si el rol no cubre el módulo.
2. **Base de datos.** `ESQUEMA` define las seis tablas. `conectar()` es un context manager
   que abre la conexión, activa `PRAGMA foreign_keys` y confirma o revierte la transacción.
   `crear_tablas()` es idempotente y deja el archivo en modo `0600`. La base vive junto a
   `ecotech.py`, lo lance quien lo lance y desde donde sea; `usar_base()` redirige la ruta, que es
   lo que permite testear contra una base temporal.
3. **Clases del modelo.** Las ocho del diagrama más el enum `Rol`, declaradas en orden de
   dependencia y con su CRUD adentro. Detalle en la tabla de abajo.
4. **Autoverificación.** `_autoverificar()` recorre con `assert` el dominio, los permisos, el
   ciclo CRUD entero, los permisos del archivo de la base y la exportación a CSV. Es la red que
   protege cualquier refactor.

### Clases

| Clase | Tabla | Rol |
|---|---|---|
| `EntidadReportable` | — | Abstracta. Aporta el id y obliga a implementar `obtener_resumen()` |
| `Persona` | — | Abstracta. Nombre, dirección y contacto validado |
| `Empleado` | `empleado` | Contrato y salario. CRUD completo |
| `Departamento` | `departamento` | Agrupa empleados y designa gerente. CRUD completo, y la relación persistida |
| `Proyecto` | `proyecto` | Asignación de empleados y horas consumidas. En memoria en esta unidad |
| `RegistroTiempo` | `registro_tiempo` | Horas imputadas a un proyecto en una fecha. En memoria en esta unidad |
| `Usuario` | `usuario` | Credencial y rol. No es entidad reportable. Se persiste en la Unidad 3 |
| `Informe` | — | Se genera al vuelo a partir de cualquier lista de `EntidadReportable` |

El CRUD vive como métodos de cada clase: `guardar()` inserta, `listar()` y `buscar()` leen
como métodos de clase, los métodos de actualización escriben solo tras validar, y `eliminar()`
borra. Todas las consultas van parametrizadas con `?`.

### Relaciones

**La base es la única fuente de verdad de la relación entre `Departamento` y `Empleado`.** Los
métodos del diagrama, `agregar_empleado`, `quitar_empleado`, `asignar_gerente` y
`listar_empleados`, escriben y leen las claves foráneas directamente; no hay listas en memoria que
se puedan desfasar, y `obtener_resumen()` cuenta con el mismo `COUNT(*)` que muestra el menú.
Relacionar un objeto sin guardar lanza `ValueError`.

- `empleado.departamento_id` → agregación, `ON DELETE SET NULL`: borrar un departamento no
  borra a su gente.
- `departamento.gerente_id` → «gerente» 0..1, `ON DELETE SET NULL`: borrar a la gerente deja el
  cargo vacante. Solo se asigna a alguien del departamento, y cambiarla de departamento libera el
  cargo en la misma transacción.
- `registro_tiempo.empleado_id` → composición, `ON DELETE CASCADE`: los registros no
  sobreviven al empleado.
- `empleado_proyecto` → tabla intermedia de la relación muchos a muchos.

## Seguridad

- **Inyección SQL:** consultas parametrizadas, nunca concatenación de cadenas.
- **Claves:** `hashlib.scrypt` con sal aleatoria de 16 bytes por usuario y factor de trabajo
  `n=2**16`, comparación con `secrets.compare_digest`. El hash guarda sus propios parámetros,
  `scrypt$n$r$p$sal$hash`, para que subir el costo mañana no invalide los hashes de hoy. La clave
  en claro nunca se guarda en el objeto, y no hay ninguna credencial escrita en el código.
- **Autorización:** tres roles en `Rol`, con su mapa de módulos en `Usuario._PERMISOS`.
  Las nueve operaciones protegidas exigen el parámetro `solicitante` y pasan por `autorizar()`.
- **Permisos del archivo:** la base queda en `0600`. SQLite la crea en `0644` y adentro hay
  sueldos, así que el encapsulamiento no sirve de nada si cualquier usuario del equipo puede abrir
  el archivo con otra herramienta.
- **Path traversal:** `Informe.exportar()` resuelve la ruta destino y la rechaza si sale del
  directorio de trabajo.
- **Inyección de fórmulas:** las celdas del CSV exportado que empiezan con `=`, `+`, `-` o `@`
  salen con un apóstrofo delante, para que la planilla las lea como texto y no las ejecute.
  `csv.writer` escapa lo que rompe el formato del archivo, no lo que la planilla interpreta
  después.
- **Validación de entrada:** el dominio rechaza salarios fuera de rango, contratos con fecha
  futura, jornadas de más de 24 horas, contacto mal formado y caracteres de control, que en un
  programa de terminal permiten falsear la pantalla. La interfaz acota además todo
  entero tecleado, porque SQLite desborda más allá de 64 bits.
- **Errores:** el bucle de `main.py` atrapa cada familia de `sqlite3.Error` por separado y
  cierra con un `except` general, de modo que ningún fallo tumba la sesión.

### Lo que este sistema no cubre

- **Cuatro de las seis tablas no tienen código que las escriba, a propósito.** El esquema es el
  contrato completo del diagrama, pero el CRUD de esta unidad es sobre las dos clases relacionadas
  que pide la evaluación. `Proyecto` y `RegistroTiempo` viven en memoria, con sus reglas probadas en
  la autoverificación; `proyecto`, `empleado_proyecto` y `registro_tiempo` quedan listas para
  persistirlas, y `usuario` llega con la autenticación.

- **No hay autenticación.** La tabla `usuario` existe y ningún código la escribe: el menú
  construye su solicitante al arrancar. Los roles protegen del uso incorrecto, no de un atacante,
  porque nadie verifica la identidad de quien dice ser el administrador. El inicio de sesión es
  materia de la unidad siguiente y agregarlo le pondría a `Usuario` métodos que el diagrama no
  tiene.
- **XSS y cabeceras HTTP no aplican.** No hay servidor ni salida HTML: la interfaz es una
  terminal. Los dos contextos que aquí interpretan el dato, la planilla y la terminal, están
  cubiertos arriba.
- **Sin cifrado en reposo ni concurrencia.** La base es un archivo en claro y escribe un solo
  proceso.

El detalle de cada punto, con su reproducción, está en `docs/AUDITORIA.md` y `docs/AUDITORIA2.md`.

## Menú

Diez opciones sobre las dos clases relacionadas, agrupadas por operación: **C** crear datos de
ejemplo, un departamento o un empleado (1-3); **R** listar departamentos y empleados (4-5);
**U** renombrar departamento, actualizar contacto y asignar departamento (6-8); **D** eliminar
departamento o empleado (9-10). Escribir `x` en cualquier dato que se pida cancela la acción sin
guardar nada, y `m` reimprime el menú.

<details>
<summary><b>Sesión de ejemplo</b> (extracto real de <code>python3 main.py</code>)</summary>

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

   m. menú   ·   x. cancela el dato que se pide   ·   0. salir
==================================================================

   Opción (m = menú): 1
   Creados 2 departamentos y 3 empleados.

   Opción (m = menú): 4
   [1] Desarrollo Sostenible · 2 empleados
   [2] Investigación y Desarrollo · 1 empleado

   Opción (m = menú): 6
   (escriba x para cancelar)
   Id del departamento: abc
   ! Escriba un número entero, sin puntos ni letras.
   Id del departamento: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
   Id del departamento: 1
   Nuevo nombre: Innovación Sostenible
   Ahora se llama Innovación Sostenible.

   Opción (m = menú): 7
   (escriba x para cancelar)
   Id del empleado: 1
   Nuevo teléfono: 22 987 6543
   Nuevo correo: x
   Acción cancelada. No se guardó nada.

   Opción (m = menú): 7
   (escriba x para cancelar)
   Id del empleado: 1
   Nuevo teléfono: 22 987 6543
   Nuevo correo: juanita.bravo@ecotech.cl
   Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17

   Opción (m = menú): 3
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

   Opción (m = menú): 3
   (escriba x para cancelar)
   Nombre completo: Rodrigo Peña Alarcón
   Dirección: Manuel Montt 300, Ñuñoa
   Teléfono: +56 9 3344 5566
   Correo: rpena@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-03-10
   Salario: 1720000
   Empleado contratado con id 4.

   Opción (m = menú): 9
   (escriba x para cancelar)
   Id del departamento: 1
   Departamento eliminado. Sus empleados siguen vigentes, sin departamento: la agregación es ON DELETE SET NULL.

   Opción (m = menú): 5
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [1] Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17
   [4] Rodrigo Peña Alarcón | rpena@ecotech.cl | 933445566 | contrato: 2025-03-10

   Opción (m = menú): 1
   ! Ya hay datos cargados: los ejemplos solo se crean sobre una base vacía.

   Opción (m = menú): 3
   (escriba x para cancelar)
   Nombre completo: Carla Reyes Ortiz
   Dirección: Pedro de Valdivia 55, Providencia
   Teléfono: +56 9 7412 8537
   Correo: creyes@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-06-02
   Salario: 1100000
   ! Ese correo ya está registrado. Use otro.

   Opción (m = menú): 0
   Hasta luego.
```

Tres capas de validación en una sola sesión: el formato lo juzga el menú y se reintenta en el
sitio, la regla de negocio la juzga la clase y aborta la operación, la restricción la juzga
SQLite y devuelve un `IntegrityError`. Ninguna interrumpe el programa.

</details>
