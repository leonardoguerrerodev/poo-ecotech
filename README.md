# EcoTech Solutions — gestión de empleados

Sistema de gestión de personal en Python, implementado sobre el modelo de clases UML
de la asignatura *Programación Orientada a Objeto Seguro*. Persistencia en SQLite con
la librería estándar: **sin dependencias externas**.

## Uso

```bash
python3 ecotech.py   # autoverificación sobre una base temporal
python3 main.py      # menú de la aplicación (crea ./ecotech.db)
```

Requiere Python 3.10 o superior (usa `int | None`).

## Estructura

| Ruta | Contenido |
|---|---|
| `ecotech.py` | Dominio completo: validaciones, esquema SQL, las 8 clases del UML y su CRUD |
| `main.py` | Interfaz de terminal. No contiene una sola sentencia SQL |
| `comentado/` | Espejo de ambos archivos con comentarios que justifican cada decisión |
| `diagramas/` | Modelo de clases en formato drawio |

### `ecotech.py`

Cuatro secciones en orden:

1. **Validaciones y autorización.** Expresiones regulares de correo, usuario y teléfono;
   `texto()` normaliza y acota cadenas; `canonico()` reduce un teléfono a sus 9 dígitos;
   `autorizar()` lanza `PermissionError` si el rol no cubre el módulo.
2. **Base de datos.** `ESQUEMA` define las seis tablas. `conectar()` es un context manager
   que abre la conexión, activa `PRAGMA foreign_keys` y confirma o revierte la transacción.
   `usar_base()` redirige la ruta, que es lo que permite testear contra una base temporal.
3. **Clases del modelo.**
4. **Autoverificación.** `_autoverificar()` recorre con `assert` el dominio, los permisos y
   el ciclo CRUD entero. Es la red que protege cualquier refactor.

### Clases

| Clase | Tabla | Rol |
|---|---|---|
| `EntidadReportable` | — | Abstracta. Aporta el id y obliga a implementar `obtener_resumen()` |
| `Persona` | — | Abstracta. Nombre, dirección y contacto validado |
| `Empleado` | `empleado` | Contrato y salario. CRUD completo |
| `Departamento` | `departamento` | Agrupa empleados y designa gerente. CRUD completo |
| `Proyecto` | `proyecto` | Asignación de empleados y horas consumidas |
| `RegistroTiempo` | `registro_tiempo` | Horas imputadas a un proyecto en una fecha |
| `Usuario` | `usuario` | Credencial y rol. No es entidad reportable |
| `Informe` | — | Se genera al vuelo a partir de cualquier lista de `EntidadReportable` |

El CRUD vive como métodos de cada clase: `guardar()` inserta, `listar()` y `buscar()` leen
como métodos de clase, los métodos de actualización escriben solo tras validar, y `eliminar()`
borra. Todas las consultas van parametrizadas con `?`.

### Relaciones

- `empleado.departamento_id` → agregación, `ON DELETE SET NULL`: borrar un departamento no
  borra a su gente.
- `registro_tiempo.empleado_id` → composición, `ON DELETE CASCADE`: los registros no
  sobreviven al empleado.
- `empleado_proyecto` → tabla intermedia de la relación muchos a muchos.

## Seguridad

- **Inyección SQL:** consultas parametrizadas, nunca concatenación de cadenas.
- **Claves:** `hashlib.scrypt` con sal aleatoria de 16 bytes por usuario, comparación con
  `secrets.compare_digest`. La clave en claro nunca se guarda en el objeto.
- **Autorización:** tres roles en `Rol`, con su mapa de módulos en `Usuario._PERMISOS`.
  Las siete operaciones de escritura exigen el parámetro `solicitante` y pasan por `autorizar()`.
- **Path traversal:** `Informe.exportar()` resuelve la ruta destino y la rechaza si sale del
  directorio de trabajo.
- **Validación de entrada:** el dominio rechaza salarios fuera de rango, contratos con fecha
  futura, jornadas de más de 24 horas y contacto mal formado. La interfaz acota además todo
  entero tecleado, porque SQLite desborda más allá de 64 bits.
- **Errores:** el bucle de `main.py` atrapa cada familia de `sqlite3.Error` por separado y
  cierra con un `except` general, de modo que ningún fallo tumba la sesión.

## Menú

Diez opciones sobre las dos clases relacionadas: crear, listar, renombrar y eliminar
departamentos; contratar, listar, actualizar contacto, eliminar y asignar departamento a
empleados. La opción `s` siembra datos de ejemplo y `m` reimprime el menú.

<details>
<summary><b>Sesión de ejemplo</b> (extracto real de <code>python3 main.py</code>)</summary>

```
==================================================================
   EcoTech Solutions — Gestión de empleados
==================================================================
   DEPARTAMENTOS                EMPLEADOS
    1. Crear                     5. Contratar
    2. Listar                    6. Listar
    3. Renombrar                 7. Actualizar contacto
    4. Eliminar                  8. Eliminar
                                 9. Asignar a departamento
    s. Cargar datos de ejemplo   0. Salir
==================================================================

   Opción (m = menú): s
   Cargados 2 departamentos y 3 empleados.

   Opción (m = menú): 2
   [1] Desarrollo Sostenible · 2 empleados
   [2] Investigación y Desarrollo · 1 empleado

   Opción (m = menú): 3
   Id del departamento: abc
   ! Escriba un número entero, sin puntos ni letras.
   Id del departamento: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
   Id del departamento: 1
   Nuevo nombre: Innovación Sostenible
   Ahora se llama Innovación Sostenible.

   Opción (m = menú): 7
   Id del empleado: 1
   Nuevo teléfono: 22 987 6543
   Nuevo correo: juanita.bravo@ecotech.cl
   Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17

   Opción (m = menú): 5
   Nombre completo: Rodrigo Peña Alarcón
   Dirección: Manuel Montt 300, Ñuñoa
   Teléfono: +56 9 3344 5566
   Correo: rpena@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-03-10
   Salario: 500000000
   ! Salario fuera de rango (1 a 100000000): 500000000

   Opción (m = menú): 4
   Id del departamento: 1
   Departamento eliminado. Sus empleados siguen vigentes, sin departamento: la agregación es ON DELETE SET NULL.

   Opción (m = menú): 6
   [3] Camila Reyes Ortiz | creyes@ecotech.cl | 974128536 | contrato: 2024-01-08
   [2] Ignacio Fuentes Cárdenas | ifuentes@ecotech.cl | 965432109 | contrato: 2022-11-02
   [1] Juanita Bravo Sepúlveda | juanita.bravo@ecotech.cl | 229876543 | contrato: 2023-04-17

   Opción (m = menú): s
   ! Ese correo ya está registrado. Use otro.

   Opción (m = menú): 0
   Hasta luego.
```

Tres capas de validación en una sola sesión: el formato lo juzga el menú y se reintenta en el
sitio, la regla de negocio la juzga la clase y aborta la operación, la restricción la juzga
SQLite y devuelve un `IntegrityError`. Ninguna interrumpe el programa.

</details>
