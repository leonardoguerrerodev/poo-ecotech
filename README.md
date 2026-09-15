# EcoTech Solutions — gestión de empleados

Programa de terminal en Python para gestionar empleados y departamentos de la empresa EcoTech.
Lleva a código el diagrama de clases UML de la asignatura *Programación Orientada a Objeto Seguro*
y guarda los datos en una base SQLite.

**Todo es biblioteca estándar de Python: no hay nada que instalar.**

## Cómo ejecutarlo

Requiere **Python 3.11 o superior**.

```bash
python3 main.py      # abre el menú (crea ecotech.db la primera vez)
python3 ecotech.py   # corre la autoverificación: prueba todo sobre una base temporal
```

En el menú, la opción **1** carga datos de ejemplo para probar sin tener que teclear datos. Escribir **`x`**
en cualquier dato cancela la acción sin guardar.

## Qué hay en el repositorio

| Archivo o carpeta | Qué es |
|---|---|
| `ecotech.py` | El sistema: validaciones, tablas de la base, las 8 clases del UML y sus operaciones CRUD |
| `main.py` | El menú de terminal. No tiene ni una línea de SQL: solo llama a los métodos de las clases |
| `comentado/` | El mismo código explicado. `*_corto.py` trae un comentario breve por pieza; `Comments_Explicacion_Larga/` trae la justificación completa de cada decisión |
| `diagramas/` | El diagrama de clases vigente (`modelo_u2.drawio` y sus imágenes clara y oscura) y el de la Unidad 1 (`modelo_final.drawio`) |
| `docs/AUDITORIA.md` | La auditoría de seguridad del código, en cuatro pasadas: lo que encontramos y cómo lo corregimos |

## Cómo está construido

### Del diagrama al código

Cada caja del UML es una clase en `ecotech.py`, con los mismos atributos y en el mismo orden. La
visibilidad se tradujo literal: privado (`-`) es `__atributo`, protegido (`#`) es `_atributo`.

| Clase | Qué representa | Se guarda en la base |
|---|---|---|
| `EntidadReportable` | Abstracta. Todo lo que puede aparecer en un informe | — |
| `Persona` | Abstracta. Nombre, dirección y contacto validados | — |
| `Empleado` | Hereda de `Persona`. Contrato y salario | ✅ tabla `empleado` |
| `Departamento` | Agrupa empleados y tiene gerente | ✅ tabla `departamento` |
| `Proyecto` | Empleados asignados y horas consumidas | en memoria (tabla lista) |
| `RegistroTiempo` | Horas trabajadas en un proyecto | en memoria (tabla lista) |
| `Usuario` | Credencial y rol | Unidad 3 (tabla lista) |
| `Informe` | Resumen generado a partir de cualquier entidad | — (se calcula al vuelo) |

### Las relaciones

| En el UML | En el código | En la base |
|---|---|---|
| Herencia `Empleado` → `Persona` | `class Empleado(Persona)` | los datos de persona van en la tabla `empleado` |
| Agregación ◇ `Departamento`–`Empleado` | `agregar_empleado()`, `quitar_empleado()` | `ON DELETE SET NULL`: **borrar un departamento no borra a sus empleados** |
| Composición ◆ `Empleado`–`RegistroTiempo` | `registrar_tiempo()` | `ON DELETE CASCADE`: los registros se van con el empleado |
| Asociación «gerente» | `asignar_gerente()` | `gerente_id` (solo alguien del mismo departamento) |
| Muchos a muchos `Proyecto`–`Empleado` | `asignar_empleado()` actualiza los dos lados | tabla intermedia `empleado_proyecto` |

La relación entre departamentos y empleados **vive solo en la base**: no hay copias en memoria que
se puedan desincronizar.

### El CRUD

Se hace sobre **`Empleado` y `Departamento`**, las dos clases relacionadas que pide la evaluación.
Las operaciones son métodos de cada clase:

| Operación | Método | Detalle |
|---|---|---|
| **C** · crear | `guardar()` | el id lo asigna la base; guardar dos veces se rechaza |
| **R** · leer | `listar()`, `buscar()` | columnas con nombre, nunca `SELECT *`; buscar algo que no existe devuelve `None` |
| **U** · actualizar | `renombrar()`, `actualizar_contacto()`, `agregar_empleado()` | valida primero y recién después escribe |
| **D** · eliminar | `eliminar()` | pide permiso y confirma que de verdad borró algo |

La conexión se abre y se cierra en cada operación (`conectar()`), con las claves foráneas activadas
y la transacción confirmada o deshecha automáticamente.

## Seguridad

Es el foco de la asignatura, así que la resumimos punto por punto:

- **Inyección SQL:** todas las consultas usan parámetros `?`. El dato nunca se pega dentro del SQL.
- **Contraseñas:** se convierten en hash `scrypt` con sal aleatoria, nunca quedan en texto plano, y se
  comparan en tiempo constante (`secrets.compare_digest`). El hash guarda su costo, así que se
  puede subir más adelante sin romper las claves existentes. La tabla `usuario` se escribe en la
  Unidad 3, junto con el inicio de sesión.
- **Permisos por rol:** tres roles (`ADMIN_RRHH`, `GERENTE`, `EMPLEADO`). Las nueve operaciones que
  escriben o muestran datos sensibles, como ver un salario, piden quién lo solicita y pasan por
  `autorizar()`.
- **Datos privados:** el salario es un atributo privado y solo sale con permiso. Los listados y los
  informes nunca lo muestran.
- **Archivo de la base:** queda con permisos `0600`, legible solo por su dueño, porque adentro hay
  sueldos.
- **Validación de entradas, en tres capas:**
  1. **el menú** revisa el formato (números con techo, fechas reales) y vuelve a preguntar;
  2. **las clases** revisan las reglas del negocio: salario en rango, contrato no futuro, correo
     válido de hasta 254 caracteres, teléfono chileno, textos sin caracteres invisibles ni códigos
     que alteren la terminal;
  3. **la base** repite las reglas con `CHECK`, `NOT NULL` y `UNIQUE` como última red.
- **Errores:** el menú atrapa cada tipo de error por separado (dato inválido, correo repetido, base
  no disponible, falta de permiso) y muestra un mensaje claro. **Ningún error cierra el programa.**
- **Exportación a CSV:** las celdas que una planilla podría ejecutar como fórmula (`=`, `+`, `-`,
  `@`) se neutralizan, y las rutas que intentan salir de la carpeta (`../`) se rechazan.

### Cómo lo comprobamos

- **Autoverificación** (`python3 ecotech.py`): prueba con `assert` las reglas del dominio, los
  permisos, el CRUD completo, las relaciones leídas desde la base y la exportación. Termina en
  `OK` o se detiene en la regla que falló.
- **Auditoría de seguridad en cuatro pasadas** (`docs/AUDITORIA.md`). Encontró, entre
  otras cosas, que un número de 25 dígitos cerraba el programa y que borrar un empleado no pedía
  permiso. Las dos cosas se corrigieron y hoy tienen su prueba.

## Uso de inteligencia artificial

Usamos Claude (Anthropic) con Claude Code, y revisamos sugerencias de GitHub Copilot. No copiamos y
pegamos: cada propuesta se planificó, se leyó, se probó y se decidió. De 25 fragmentos revisados,
**2 se adoptaron, 13 se modificaron y 10 se descartaron**, siempre por seguridad, eficiencia o
coherencia con el diagrama. Algunos ejemplos:

- se descartaron métodos que la IA sugería y que el UML no tiene;
- se corrigió una conexión que quedaba abierta y un `SELECT *` que arrastraba el salario;
- se recortó un menú de 14 opciones con login a 10 opciones, porque el login es de la Unidad 3.

El análisis completo lo presentamos en la defensa oral.

## Pendiente para la Unidad 3

| Qué falta | Por qué no está hoy |
|---|---|
| **Inicio de sesión** con la tabla `usuario` | Es contenido de la Unidad 3. Hoy el menú opera siempre como `ADMIN_RRHH` |
| **Protección contra fuerza bruta**: bloqueo temporal tras varios intentos fallidos y la misma demora exista o no el usuario | Sin login no hay credencial que atacar. El diseño está en `docs/AUDITORIA.md`, sección 3.4 |
| **Menú de informes** con permisos reales por rol | Solo tiene sentido con usuarios autenticados: un gerente ve el informe sin sueldos, un empleado no puede generarlo |
| **Consumo de APIs externas** (HTTP y JSON), con manejo de errores de red, tiempos de espera y códigos de respuesta | Es el otro eje de la Unidad 3 |
| Guardar `Proyecto` y `RegistroTiempo` en la base | Sus tablas ya existen; el CRUD de esta unidad pedía dos clases relacionadas |

Agregar el login le suma métodos a `Usuario`, así que primero se actualiza el diagrama y después el
código, para no romper la correspondencia entre los dos.

### Límites conocidos

- No hay servidor web, así que XSS y cabeceras HTTP no aplican: los contextos que interpretan datos
  aquí son la terminal y la planilla, y los dos están cubiertos.
- La base no está cifrada y está pensada para un solo usuario a la vez.
- La limpieza de pantalla usa códigos ANSI: la consola antigua de Windows (`cmd` sin modo VT) los
  muestra como texto. Windows Terminal, Linux y macOS funcionan bien.
- Los archivos de `comentado/` son para leer. Se ejecuta la raíz.

## El menú

Diez opciones agrupadas por operación: **C** crear (1-3), **R** leer (4-5), **U** actualizar (6-8) y
**D** eliminar (9-10). Después de cada acción el menú pide Enter, limpia la pantalla y vuelve a
aparecer.

<details>
<summary><b>Sesión de ejemplo</b> (extracto real de <code>python3 main.py</code>, sin las pausas)</summary>

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

   Opción: 4
   [1] Desarrollo Sostenible · 2 empleados
   [2] Investigación y Desarrollo · 1 empleado

   Opción: 6
   (escriba x para cancelar)
   Id del departamento: abc
   ! Escriba un número entero, sin puntos ni letras.
   Id del departamento: 9999999999999999999999999
   ! Demasiado grande. El máximo es 1000000000.
   Id del departamento: 1
   Nuevo nombre: Innovación Sostenible
   Ahora se llama Innovación Sostenible.

   Opción: 7
   (escriba x para cancelar)
   Id del empleado: 1
   Nuevo teléfono: 22 987 6543
   Nuevo correo: x
   Acción cancelada. No se guardó nada.

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

   Opción: 9
   (escriba x para cancelar)
   Id del departamento: 1
   Departamento eliminado. Sus empleados siguen vigentes, sin departamento: la agregación es ON DELETE SET NULL.

   Opción: 3
   (escriba x para cancelar)
   Nombre completo: Carla Reyes Ortiz
   Dirección: Pedro de Valdivia 55, Providencia
   Teléfono: +56 9 7412 8537
   Correo: creyes@ecotech.cl
   Inicio de contrato (AAAA-MM-DD): 2025-06-02
   Salario: 1100000
   ! Ese correo ya está registrado. Use otro.

   Opción: 0
   Hasta luego.
```

En una sola sesión se ven las tres capas: el menú rechaza el formato y vuelve a preguntar, la clase
rechaza el salario fuera de rango y la base rechaza el correo repetido. El programa nunca se cierra.

</details>
