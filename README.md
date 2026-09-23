# EcoTech Solutions — gestión de empleados

**INACAP · TI3V21 Programación Orientada a Objeto Seguro · Evaluación Sumativa 2 (Unidades 2 y 3)**
**Docente:** Rubén Schnettler Lucero
**Integrantes:** Claudio Medina · Lucas Espinoza · Leonardo Guerrero
**Repositorio:** https://github.com/leonardoguerrerodev/poo-ecotech

Programa de terminal en Python que gestiona empleados, departamentos y proyectos. Lleva a código el
diagrama de clases de la asignatura, guarda los datos en SQLite, pide inicio de sesión y consulta dos
servicios externos para cada proyecto: el **clima** de su ciudad (Open-Meteo) y el **tipo de cambio**
de su moneda (mindicador.cl). Lo que llega de esos servicios se valida, se guarda y, si la red falla,
se usa el último valor conocido avisando que es referencial.

## 1. Para evaluar

**Versión entregada:** el último commit de `main` hasta el **23-09-2026 a las 23:59, hora de Chile**.
El comando `git checkout` de abajo deja el repositorio exactamente en esa versión.

Requiere **Python 3.11 o superior** e internet para las opciones que consultan servicios (11, 12 y 21).

```bash
git clone https://github.com/leonardoguerrerodev/poo-ecotech.git
cd poo-ecotech
git checkout $(git rev-list -n 1 --before="2026-09-23 23:59:59 -0300" main)

python3 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

python3 ecotech.py                 # autoverificación del sistema (base temporal): termina en OK
python3 servicios.py               # autoverificación de las APIs, sin conectarse: termina en OK
python3 main.py                    # el programa
```

En Windows, si `python3` no existe, se usa `python` o `py`.

**Primer uso:**
- **No hay usuarios ni claves en el código.** La primera vez, el programa pide crear la cuenta de
  administrador: usuario de 3 a 20 caracteres y clave de 12 o más, con tres de estos cuatro tipos:
  minúscula, mayúscula, número y símbolo. Después pide iniciar sesión con esa cuenta.
- La **opción 1** carga datos de ejemplo: dos departamentos, tres empleados y dos proyectos, uno en
  Valparaíso pagado en pesos y otro en Madrid pagado en euros.
- La **opción 14** crea cuentas de gerente o de empleado para probar los permisos.
- **`x`** en cualquier dato cancela la acción sin guardar; **`0`** sale.
- Las APIs no piden llave. La configuración es opcional: `cp .env.example .env`.

El mismo contenido está en [`ENTREGA.md`](ENTREGA.md).

## 2. Qué hay en el repositorio

| Archivo | Qué es |
|---|---|
| `ecotech.py` | Las 10 clases del diagrama (más el enumerado `Rol`), la base de datos, el CRUD y el inicio de sesión |
| `servicios.py` | El cliente de los servicios externos: la única parte que habla con internet |
| `main.py` | El menú de terminal: no contiene SQL ni HTTP |
| `diagramas/EcoTech_UML_VIGENTE.drawio` | **El diagrama vigente**, igual al código miembro por miembro, con su imagen clara y oscura. Los de unidades anteriores están en `diagramas/historico/` |
| `requirements.txt` · `.env.example` | Dependencias con versión exacta · variables de configuración, sin valores secretos |
| `docs/SALIDA_TERMINAL.md` | Sesiones reales del programa, incluidos los fallos provocados (sin red, red que se cae y configuración insegura) |
| `docs/AUDITORIA.md` | Las auditorías de seguridad: cada hallazgo, su corrección y su prueba |
| `docs/ANALISIS_IA.md` | El uso de IA: qué se adoptó, modificó o descartó, y por qué |

Tres archivos y no uno por clase, porque el docente pidió no modularizar por clase: es **un archivo
por razón de cambio**. Si cambia una API, solo se toca `servicios.py`, que no importa nada de
`ecotech.py`.

## 3. Cómo está construido

| Clase | Qué representa | En la base |
|---|---|---|
| `EntidadReportable` · `Persona` | Abstractas: id y resumen · nombre y contacto validados | sin tabla propia |
| `Empleado` | Hereda de `Persona`: contrato y salario | `empleado` · CRUD |
| `Departamento` | Agrupa empleados y tiene gerente | `departamento` · CRUD |
| `Proyecto` | Ciudad, moneda de pago, equipo y horas | `proyecto`, `empleado_proyecto` · CRUD |
| `RegistroTiempo` | Horas de un empleado en un proyecto | `registro_tiempo` |
| `RegistroClima` · `TipoCambio` | Lo que devolvieron las APIs, guardado (sin edición: es evidencia) | `registro_clima`, `tipo_cambio` |
| `Usuario` · `Rol` | Cuenta, rol, intentos fallidos y, si es empleado, su ficha | `usuario` |
| `Informe` | Resumen de cualquier entidad, exportable a CSV | sin tabla |
| `ServicioExterno` | «boundary»: clima y tipo de cambio | sin tabla |

- **Las relaciones del diagrama viven solo en la base**, con claves foráneas:
  - borrar un departamento no borra a sus empleados (`ON DELETE SET NULL`);
  - borrar un empleado se lleva sus horas y su cuenta;
  - un proyecto con horas registradas no se puede borrar.
- La conexión se abre y se cierra en cada operación, con las claves foráneas activadas y la
  transacción confirmada o deshecha automáticamente. Todas las consultas usan parámetros `?`.

## 4. Seguridad

- **Inicio de sesión:**
  - claves con hash `scrypt` y sal, comparadas en tiempo constante;
  - **5 intentos fallidos bloquean la cuenta 5 minutos**, y el bloqueo queda en la base;
  - el mismo mensaje y la misma demora (medida: 255 ms) si el usuario no existe, si la clave es
    incorrecta o si la cuenta está bloqueada;
  - **10 minutos sin actividad cierran la sesión**, también si quedó detenida en «Presione Enter».
- **Permisos por rol:** `ADMIN_RRHH`, `GERENTE` y `EMPLEADO`.
  - El menú revisa el permiso **antes de pedir datos**, y las clases lo vuelven a revisar al escribir.
  - El gerente no ve sueldos ni la planilla.
  - El empleado solo registra **sus propias horas**.
  - En el listado de empleados, el correo y el teléfono solo los ve RRHH; el informe de dotación
    los incluye para quien tiene permiso de informes.
- **Servicios externos:**
  - tiempo de espera en toda solicitud, solo `https` (aunque la dirección venga de la
    configuración) y el código HTTP se revisa antes de leer la respuesta;
  - la respuesta se valida en tipo, **rango** y fecha antes de usarse y otra vez antes de guardarse;
  - si el servicio falla, el sistema **no se detiene**: usa el último dato de la sesión o el último
    guardado en la base, **avisando que es referencial**.
- **Entradas en tres capas:**
  - el menú revisa el formato: números con techo, fechas reales;
  - las clases revisan las reglas del negocio, incluidos textos sin códigos que alteren la terminal;
  - la base las repite con `CHECK`, `NOT NULL` y `UNIQUE`.
- **Errores:** cada tipo se atrapa por separado con un mensaje claro. **Ningún error cierra el
  programa**, y ningún mensaje muestra rutas, consultas ni trazas.
- **Datos:**
  - la base y el CSV exportado quedan en `0600`;
  - el salario nunca sale en listados ni informes;
  - el CSV neutraliza las fórmulas y rechaza las rutas que salen de la carpeta (`../`).

**Cómo se comprobó:** dos autoverificaciones con `assert`, que terminan en `OK`. Además, **ocho
pasadas de auditoría** (`docs/AUDITORIA.md`), la última con un revisor independiente y la matriz real
de permisos: 3 roles × 25 opciones. Cada regla nueva se probó **rompiéndola a propósito** para
comprobar que la prueba falla.

## 5. Uso de inteligencia artificial

Usamos Claude (Anthropic) y revisamos sugerencias de GitHub Copilot. Cada propuesta se leyó, se probó
y se decidió por seguridad, eficiencia o coherencia con el diagrama. **68 decisiones registradas:
5 adoptadas, 47 modificadas y 16 descartadas.** Algunos ejemplos:
- se descartaron métodos que el diagrama no tiene;
- se corrigió un tipo de cambio que aceptaba `Infinity`;
- se detectaron pruebas que pasaban por el motivo equivocado;
- se quitaron versiones de dependencias con avisos de seguridad conocidos.

El detalle fila por fila, con la revisión del cliente en los cinco aspectos que pide el docente
(credenciales, protocolo, tiempo de espera, manejo de errores y uso de la respuesta), está en
`docs/ANALISIS_IA.md`.

## 6. Qué quedó fuera

- **No se editan** un registro de horas ni un dato guardado de las APIs: son traza.
- **Cambiar la clave** existe en la clase, pero no se guarda en la base.
- La base no está cifrada y está pensada para un solo usuario a la vez.
- La limpieza de pantalla usa códigos ANSI: la consola antigua de Windows los muestra como texto;
  Windows Terminal, Linux y macOS funcionan bien.

## 7. El menú

Después de cada acción pide Enter, limpia la pantalla y vuelve a aparecer.

```
   C — CREAR                     U — ACTUALIZAR
    1. Datos de ejemplo           6. Renombrar departamento
    2. Departamento               7. Contacto del empleado
    3. Empleado (contratar)       8. Asignar a departamento

   R — LEER                      D — ELIMINAR
    4. Departamentos              9. Departamento
    5. Empleados                 10. Empleado

   S — SERVICIOS EXTERNOS        A — ADMINISTRACIÓN
   11. Clima del proyecto        13. Informe de dotación
   12. Planilla en su moneda     14. Crear usuario

   P — PROYECTOS
   15. Crear proyecto            18. Quitar empleado
   16. Proyectos                 19. Registrar horas
   17. Asignar empleado          20. Eliminar proyecto

   H — HISTORIAL DE LAS APIS
   21. Guardar cambio del día    24. Borrar registro de clima
   22. Historial de clima        25. Borrar tipo de cambio
   23. Historial tipo de cambio
```
