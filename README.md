# EcoTech Solutions — gestión de empleados

Programa de terminal en Python para gestionar empleados y departamentos de la empresa EcoTech.
Lleva a código el diagrama de clases UML de la asignatura *Programación Orientada a Objeto Seguro*,
guarda los datos en una base SQLite, pide inicio de sesión y consulta dos servicios externos: el
**clima** de la ciudad de una faena y el **tipo de cambio** del día para pagar en moneda extranjera.

## Cómo ejecutarlo

Requiere **Python 3.11 o superior** y conexión a internet para las opciones 11 y 12.

```bash
pip install -r requirements.txt   # una sola dependencia: requests
python3 main.py                   # la primera vez pide crear la cuenta de administrador
python3 ecotech.py                # autoverificación del sistema, sobre una base temporal
python3 servicios.py              # autoverificación de las APIs, sin conectarse a internet
```

**La primera vez** el programa pide crear la cuenta de administrador (RRHH); después pide usuario y
clave. En el menú, la opción **1** carga datos de ejemplo y la **14** crea cuentas de gerente o de
empleado para probar los permisos. Escribir **`x`** en cualquier dato cancela la acción sin guardar.

Las APIs son públicas y **no piden llave**: [Open-Meteo](https://open-meteo.com) para el clima y
[mindicador.cl](https://mindicador.cl) para el dólar, el euro y la UF.

## Qué hay en el repositorio

| Archivo o carpeta | Qué es |
|---|---|
| `ecotech.py` | El sistema: validaciones, tablas de la base, las 8 clases del UML, sus operaciones CRUD y el inicio de sesión |
| `servicios.py` | Los servicios externos: la única parte del programa que habla con internet |
| `main.py` | El menú de terminal. No tiene ni una línea de SQL ni de HTTP: solo llama a las clases |
| `requirements.txt` | La única dependencia externa, `requests` |
| `diagramas/` | El diagrama vigente, `modelo_u3.drawio`; el de la Unidad 2 (`modelo_u2.drawio`, con sus imágenes) y el de la Unidad 1 (`modelo_final.drawio`) |
| `docs/AUDITORIA.md` | La auditoría de seguridad del código, en seis pasadas: lo que encontramos y cómo lo corregimos |
| `docs/ANALISIS_IA.md` | Qué propuso la IA, qué errores y vulnerabilidades le encontramos y qué hicimos con cada fragmento |

### Por qué tres archivos

- **Cada archivo tiene una sola responsabilidad.** `ecotech.py` es el sistema: las clases, la base de
  datos y las reglas. `servicios.py` es la frontera con internet. `main.py` es solo la pantalla: pide
  datos, llama a las clases y muestra el resultado. Si una API cambia, se toca solo `servicios.py`; si
  a futuro la interfaz fuera web, `ecotech.py` no cambia.
- **No es un archivo por clase**, que es lo que el docente indicó evitar: es un archivo por razón de
  cambio. `servicios.py` no importa nada de `ecotech.py`, así que no hay importaciones circulares.
- **`ecotech.py` se prueba solo**, sin abrir el menú: `python3 ecotech.py`.
- **Juntar las clases en un archivo resolvió problemas reales:** se acabaron las importaciones
  circulares entre clases y un acceso a datos privados desde fuera de su clase.

## Cómo está construido

### Del diagrama al código

Cada caja del UML es una clase en `ecotech.py`, con los mismos atributos y en el mismo orden. La
visibilidad se tradujo literal: privado (`-`) es `__atributo`, protegido (`#`) es `_atributo`.

Al arrancar se crean las seis tablas del modelo. **El CRUD completo es de `Empleado` y
`Departamento`**, las dos clases relacionadas que pide la evaluación (ver [El CRUD](#el-crud)), y
`Usuario` se guarda y se lee para el inicio de sesión. Las tablas de proyectos y registros de tiempo
quedan creadas, sin uso todavía.

| Clase | Qué representa | En la base, en esta unidad |
|---|---|---|
| `EntidadReportable` | Abstracta. Todo lo que puede aparecer en un informe | sin tabla propia: aporta el id a sus hijas |
| `Persona` | Abstracta. Nombre, dirección y contacto validados | sin tabla propia: sus datos van en la tabla `empleado` |
| `Empleado` | Hereda de `Persona`. Contrato y salario | ✅ **con CRUD** · tabla `empleado` |
| `Departamento` | Agrupa empleados y tiene gerente | ✅ **con CRUD** · tabla `departamento` |
| `Proyecto` | Empleados asignados y horas consumidas | tabla creada, sin CRUD todavía: vive en memoria |
| `RegistroTiempo` | Horas trabajadas en un proyecto | tabla creada, sin CRUD todavía: vive en memoria |
| `Usuario` | Credencial, rol e intentos fallidos | ✅ tabla `usuario`: alta de cuentas e inicio de sesión |
| `Informe` | Resumen generado a partir de cualquier entidad | sin tabla: se calcula al vuelo y se exporta a CSV |
| `ServicioExterno` | «boundary»: consulta el clima y el tipo de cambio | sin tabla: los datos se piden en el momento |

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
- **Inicio de sesión:** nada funciona sin usuario y clave. La clave se escribe sin eco (`getpass`).
  **Cinco intentos fallidos bloquean la cuenta cinco minutos**, y el bloqueo queda en la base, así
  que reiniciar el programa no lo levanta. El mensaje de error es el mismo, y tarda lo mismo, si
  el usuario no existe, si la clave es incorrecta o si la cuenta está bloqueada: así no se puede
  averiguar qué cuentas existen. **Diez minutos sin actividad cierran la sesión.**
- **Contraseñas:** se convierten en hash `scrypt` con sal aleatoria, nunca quedan en texto plano, y se
  comparan en tiempo constante (`secrets.compare_digest`). El hash guarda su costo, así que se
  puede subir más adelante sin romper las claves existentes.
- **Permisos por rol:** tres roles (`ADMIN_RRHH`, `GERENTE`, `EMPLEADO`). El menú revisa el permiso
  **antes de pedir el primer dato**, y las clases lo vuelven a revisar al escribir. Un gerente ve el
  informe de dotación pero no los sueldos ni los pagos; un empleado solo consulta.
- **Servicios externos:** toda solicitud lleva **tiempo de espera** (3 s para conectar, 10 para
  leer), se revisa el **código HTTP** antes de leer la respuesta, y el JSON se valida campo por campo
  antes de usarlo. La ciudad y la moneda se validan antes de salir a internet (la moneda, contra una
  lista cerrada). Lo que llega de la red se trata con la misma desconfianza que lo que se teclea.
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
  no disponible, falta de permiso, servicio externo caído, sin red o lento) y muestra un mensaje
  claro. **Ningún error cierra el programa**, y ningún mensaje muestra rutas, consultas ni trazas
  internas.
- **Exportación a CSV:** las celdas que una planilla podría ejecutar como fórmula (`=`, `+`, `-`,
  `@`) se neutralizan, y las rutas que intentan salir de la carpeta (`../`) se rechazan.

### Cómo lo comprobamos

- **Autoverificación** (`python3 ecotech.py`): prueba con `assert` las reglas del dominio, los
  permisos, el CRUD completo, las relaciones leídas desde la base, la exportación, el inicio de
  sesión y el bloqueo por intentos fallidos. Termina en `OK` o se detiene en la regla que falló.
- **Autoverificación de las APIs** (`python3 servicios.py`): simula respuestas `200`, `404`, `429`,
  `500`, tiempo agotado, falta de red, JSON inválido y datos con otro formato, sin conectarse.
- **Auditoría de seguridad en seis pasadas** (`docs/AUDITORIA.md`). Encontró, entre
  otras cosas, que un número de 25 dígitos cerraba el programa y que borrar un empleado no pedía
  permiso. Las dos cosas se corrigieron y hoy tienen su prueba.

## Uso de inteligencia artificial

Usamos Claude (Anthropic) con Claude Code, y revisamos sugerencias de GitHub Copilot. No copiamos y
pegamos: cada propuesta se planificó, se leyó, se probó y se decidió. De 25 fragmentos revisados,
**2 se adoptaron, 13 se modificaron y 10 se descartaron**, siempre por seguridad, eficiencia o
coherencia con el diagrama. Algunos ejemplos:

- se descartaron métodos que la IA sugería y que el UML no tiene;
- se corrigió una conexión que quedaba abierta y un `SELECT *` que arrastraba el salario;
- se recortó un menú de 14 opciones con login a 10 opciones, porque el login era de la Unidad 3.

En la Unidad 3 revisamos 18 fragmentos más: **2 se adoptaron, 13 se modificaron y 3 se
descartaron**. Algunos ejemplos:

- se suponía que una ciudad inexistente daría un error `404`; consultada la API real, responde `200`
  sin resultados, y el código se escribió sobre lo que la API hace de verdad;
- el tipo de cambio aceptaba `Infinity`, que el lector de JSON de Python admite, y el pago quedaba en
  cero;
- el nombre de la ciudad que devuelve la API se imprimía sin revisar: podía traer códigos que
  alteran la terminal;
- el permiso se revisaba después de pedir todos los datos, y un gerente podía dejar una carga a
  medias.

El detalle, fila por fila, está en `docs/ANALISIS_IA.md`.

## Qué quedó fuera

| Qué | Por qué |
|---|---|
| Guardar `Proyecto` y `RegistroTiempo` en la base | Sus tablas existen, pero el CRUD pedía dos clases relacionadas. El clima se consulta por ciudad, no por proyecto guardado |
| Cambiar la clave desde el menú | `cambiar_clave` existe en la clase, pero no se guarda en la base todavía |
| Llave de API | Ninguna de las dos APIs la pide. Si una la pidiera, iría en una variable de entorno o en `.env` (ya excluido del repositorio), nunca en el código |

### Límites conocidos

- No hay servidor web, así que XSS y cabeceras HTTP no aplican: los contextos que interpretan datos
  aquí son la terminal y la planilla, y los dos están cubiertos.
- La base no está cifrada y está pensada para un solo usuario a la vez.
- mindicador.cl publica el dólar y el euro observados en Chile, así que los pagos se calculan en
  USD, EUR o UF. Otra moneda exigiría otra API.
- La limpieza de pantalla usa códigos ANSI: la consola antigua de Windows (`cmd` sin modo VT) los
  muestra como texto. Windows Terminal, Linux y macOS funcionan bien.

## El menú

Catorce opciones agrupadas por operación: **C** crear (1-3), **R** leer (4-5), **U** actualizar
(6-8), **D** eliminar (9-10), **S** servicios externos (11-12) y **A** administración (13-14).
Después de cada acción el menú pide Enter, limpia la pantalla y vuelve a aparecer.

```
==================================================================
   EcoTech Solutions — Gestión de empleados
   Sesión: rrhh.admin
==================================================================
   C — CREAR                     U — ACTUALIZAR
    1. Datos de ejemplo           6. Renombrar departamento
    2. Departamento               7. Contacto del empleado
    3. Empleado (contratar)       8. Asignar a departamento

   R — LEER                      D — ELIMINAR
    4. Departamentos              9. Departamento
    5. Empleados                 10. Empleado

   S — SERVICIOS EXTERNOS        A — ADMINISTRACIÓN
   11. Clima para faena          13. Informe de dotación
   12. Pago en moneda extranjera 14. Crear usuario

   Escriba "x" para cancelar la acción en curso   ·   0. salir
==================================================================

   Opción: 11
   Ciudad de la faena: Valparaíso
   Valparaíso, Chile: despejado, 18.6 °C, humedad 55 %, viento 24.7 km/h.
   Condiciones aptas para trabajo en terreno.

   Opción: 12
   Id del empleado: 1
   Moneda (USD, EUR, UF): usd
   Juanita Bravo Sepúlveda: 1,450,000 CLP = 1,512.91 USD  (1 USD = 958.42 CLP hoy)
```

<details>
<summary><b>Sesión de ejemplo de la Unidad 2</b> (extracto real de <code>python3 main.py</code> de esa entrega, sin las pausas ni el inicio de sesión)</summary>

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
