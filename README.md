# EcoTech Solutions — gestión de empleados

> **Para evaluar:** integrantes, versión entregada y comandos para clonar y ejecutar en [`ENTREGA.md`](ENTREGA.md).

Programa de terminal en Python para gestionar empleados, departamentos y proyectos de la empresa
EcoTech. Lleva a código el diagrama de clases UML de la asignatura *Programación Orientada a Objeto
Seguro*, guarda los datos en una base SQLite, pide inicio de sesión y consulta dos servicios
externos para cada proyecto: el **clima** de la ciudad donde se ejecuta y el **tipo de cambio** del
día, para pagar al equipo en la moneda de ese país. Lo que llega de esos servicios se valida, **se
guarda en la base** y, si la red falla, se usa el último valor conocido avisando que es referencial.

## Cómo ejecutarlo

Requiere **Python 3.11 o superior** y conexión a internet para las opciones 11, 12 y 21.

```bash
pip install -r requirements.txt   # requests y sus dependencias, con versión exacta
python3 main.py                   # la primera vez pide crear la cuenta de administrador
python3 ecotech.py                # autoverificación del sistema, sobre una base temporal
python3 servicios.py              # autoverificación de las APIs, sin conectarse a internet
```

**La primera vez** el programa pide crear la cuenta de administrador (RRHH); después pide usuario y
clave. En el menú, la opción **1** carga datos de ejemplo (dos departamentos, tres empleados y dos
proyectos: uno en Valparaíso pagado en pesos y otro en Madrid pagado en euros) y la **14** crea
cuentas de gerente o de empleado para probar los permisos; una cuenta de empleado queda vinculada a
su ficha. Escribir **`x`** en cualquier dato cancela la acción sin guardar.

Las APIs son públicas y **no piden llave**: [Open-Meteo](https://open-meteo.com) para el clima y
[mindicador.cl](https://mindicador.cl) para el dólar y el euro.

### Configuración (opcional)

Las direcciones de las APIs y el tiempo de espera se pueden cambiar sin tocar el código, con
variables de entorno o con un archivo `.env` junto a `servicios.py`. `.env.example` trae los nombres y
los valores por defecto: se copia como `.env`, que **no** se sube al repositorio. Una dirección que no
sea `https` o un tiempo fuera de 0 a 60 segundos se rechazan antes de salir a internet, y el programa
sigue funcionando. Del `.env` solo se leen las variables `ECOTECH_*`, y si el archivo no se puede
leer se usan los valores por defecto.

```bash
cp .env.example .env              # y editar lo que haga falta
```

## Qué hay en el repositorio

| Archivo o carpeta | Qué es |
|---|---|
| `ecotech.py` | El sistema: validaciones, tablas de la base, las 10 clases del UML con el enumerado `Rol`, sus operaciones CRUD y el inicio de sesión |
| `servicios.py` | Los servicios externos: la única parte del programa que habla con internet |
| `main.py` | El menú de terminal. No tiene ni una línea de SQL ni de HTTP: solo llama a las clases |
| `requirements.txt` | `requests` y sus dependencias, con versión exacta |
| `.env.example` | Las variables de configuración, sin valores secretos (el `.env` real no se sube) |
| `diagramas/` | El diagrama vigente, `modelo_u3.drawio`; el de la Unidad 2 (`modelo_u2.drawio`, con sus imágenes) y el de la Unidad 1 (`modelo_final.drawio`) |
| `docs/AUDITORIA.md` | La auditoría de seguridad del código, por pasadas: lo que encontramos y cómo lo corregimos |
| `docs/ANALISIS_IA.md` | Qué propuso la IA, qué errores y vulnerabilidades le encontramos y qué hicimos con cada fragmento |
| `docs/RUBRICA.md` | Los 22 indicadores de la rúbrica, cada uno con dónde está su evidencia, y el diagrama comparado con el código miembro por miembro |
| `docs/SALIDA_TERMINAL.md` | Sesiones reales del menú, incluidos los fallos provocados: sin red, red que se cae a mitad y configuración insegura |

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

Al arrancar se crean las ocho tablas del modelo, y **todas se usan**: `Empleado`, `Departamento` y
`Proyecto` tienen CRUD (ver [El CRUD](#el-crud)), los registros de horas se crean y se leen desde
su empleado y su proyecto, lo que devuelven las APIs se guarda en `RegistroClima` y `TipoCambio`,
y `Usuario` se guarda y se lee para el inicio de sesión.

| Clase | Qué representa | En la base, en esta unidad |
|---|---|---|
| `EntidadReportable` | Abstracta. Todo lo que puede aparecer en un informe | sin tabla propia: aporta el id a sus hijas |
| `Persona` | Abstracta. Nombre, dirección y contacto validados | sin tabla propia: sus datos van en la tabla `empleado` |
| `Empleado` | Hereda de `Persona`. Contrato y salario | ✅ **con CRUD** · tabla `empleado` |
| `Departamento` | Agrupa empleados y tiene gerente | ✅ **con CRUD** · tabla `departamento` |
| `Proyecto` | Ciudad, moneda de pago, empleados asignados y horas consumidas | ✅ **con CRUD** · tablas `proyecto` y `empleado_proyecto` |
| `RegistroTiempo` | Horas trabajadas en un proyecto | ✅ tabla `registro_tiempo`: se crea desde el empleado y se lee por proyecto |
| `Usuario` | Credencial, rol, intentos fallidos y, si es empleado, su ficha | ✅ tabla `usuario`: alta de cuentas e inicio de sesión |
| `Informe` | Resumen generado a partir de cualquier entidad | sin tabla: se calcula al vuelo y se exporta a CSV |
| `ServicioExterno` | «boundary»: consulta el clima y el tipo de cambio; recuerda el último dato bueno de la sesión | sin tabla: lo que trae se guarda con las dos clases de abajo |
| `RegistroClima` | El clima que devolvió la API para un proyecto | ✅ tabla `registro_clima`: se guarda al consultar, se lee y se borra |
| `TipoCambio` | El valor del día de una moneda | ✅ tabla `tipo_cambio`, uno por moneda y día: se guarda, se lee y se borra |

### Las relaciones

| En el UML | En el código | En la base |
|---|---|---|
| Herencia `Empleado` → `Persona` | `class Empleado(Persona)` | los datos de persona van en la tabla `empleado` |
| Agregación ◇ `Departamento`–`Empleado` | `agregar_empleado()`, `quitar_empleado()` | `ON DELETE SET NULL`: **borrar un departamento no borra a sus empleados** |
| Composición ◆ `Empleado`–`RegistroTiempo` | `registrar_tiempo()`: un registro de horas solo nace desde su empleado | `ON DELETE CASCADE`: los registros se van con el empleado |
| Asociación «imputa a» `Proyecto`–`RegistroTiempo` | `horas_consumidas()`, `RegistroTiempo.listar(proyecto)` | `proyecto_id` sin cascada: **un proyecto con horas no se puede borrar** |
| Asociación «gerente» | `asignar_gerente()` | `gerente_id` (solo alguien del mismo departamento) |
| Muchos a muchos `Proyecto`–`Empleado` | `asignar_empleado()`, `desasignar_empleado()`, `listar_empleados()` | tabla intermedia `empleado_proyecto` |
| Asociación «identifica a» `Usuario`–`Empleado` | `obtener_empleado()`: la cuenta de un empleado sabe quién es | `usuario.empleado_id`, único; borrar al empleado borra su cuenta |
| Composición ◆ `Proyecto`–`RegistroClima` | `RegistroClima.guardar(proyecto, …)`, `listar(proyecto)` | `ON DELETE CASCADE`: el historial de clima se va con el proyecto |

**Todas las relaciones viven solo en la base**: no hay copias en memoria que se puedan
desincronizar.

### El CRUD

Se hace sobre **`Empleado` y `Departamento`**, las dos clases relacionadas que pide la evaluación,
y desde la versión final también sobre **`Proyecto`**. Las operaciones son métodos de cada clase:

| Operación | Método | Detalle |
|---|---|---|
| **C** · crear | `guardar()` | el id lo asigna la base; guardar dos veces se rechaza |
| **R** · leer | `listar()`, `buscar()` | columnas con nombre, nunca `SELECT *`; buscar algo que no existe devuelve `None` |
| **U** · actualizar | `renombrar()`, `actualizar_contacto()`, `agregar_empleado()`, `asignar_empleado()` | valida primero y recién después escribe |
| **D** · eliminar | `eliminar()` | pide permiso y confirma que de verdad borró algo; un proyecto con horas registradas se rechaza |

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
  **antes de pedir el primer dato**, y las clases lo vuelven a revisar al escribir. Un gerente
  administra proyectos y ve el informe de dotación, pero no los sueldos ni la planilla; un empleado
  consulta y registra **solo sus propias horas**, en proyectos donde participa. El correo y el
  teléfono de los empleados solo los ve quien tiene el permiso de RRHH; los demás ven id y nombre.
- **Servicios externos:** toda solicitud lleva **tiempo de espera** (3 s para conectar, 10 para
  leer), se revisa el **código HTTP** antes de leer la respuesta, y el JSON se valida campo por campo
  antes de usarlo, incluido el **rango** (un dólar a un millón de pesos, o una humedad de 150 %, es
  un dato roto) y la fecha que informa el servicio. La ciudad y
  la moneda se validan antes de salir a internet (la moneda, contra una lista cerrada), y solo se
  acepta `https`, aunque la dirección venga de la configuración. Lo que llega de la red se trata con
  la misma desconfianza que lo que se teclea, y se vuelve a validar antes de guardarse.
- **Si el servicio falla, el sistema no se detiene:** usa el último dato bueno de la sesión o, si no
  hay, el último guardado en la base, y **avisa que es referencial**. Nunca lo usa en silencio.
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
- **Auditoría de seguridad en siete pasadas** (`docs/AUDITORIA.md`). Encontró, entre
  otras cosas, que un número de 25 dígitos cerraba el programa, que borrar un empleado no pedía
  permiso y que un hash alterado en la base cerraba la pantalla de login. Todo se corrigió y hoy
  tiene su prueba.
- **Las pruebas se probaron**: se rompieron cinco reglas a propósito, una por vez, y la
  autoverificación falló las cinco veces.
- **El login tarda lo mismo** con una cuenta que no existe, con una clave mala y con una cuenta
  bloqueada: medido, 255 ms en los tres casos.

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

En la auditoría final contra la rúbrica revisamos 12 decisiones más: **11 se modificaron y 1 se
descartó**. Varias fueron errores de la propia IA sobre su trabajo anterior —un plan que no
coincidía con el código, una cifra sumada de memoria— y los atrapó un control automático, no una
relectura.

En el cierre de la Unidad 3 revisamos el código cliente con los cinco aspectos que pide el docente
(credenciales, protocolo, tiempo de espera, manejo de errores y uso de la respuesta) y registramos 13
decisiones más: **10 se modificaron, 2 se descartaron y 1 se adoptó**; entre ellas, una prueba que habría pasado por
el motivo equivocado y un comentario de supresión que el propio analizador rechazaba.

El detalle, fila por fila, está en `docs/ANALISIS_IA.md`.

## Qué quedó fuera

| Qué | Por qué |
|---|---|
| Editar o borrar un registro de horas | Un registro de horas es traza: se crea y se lee, y se va solo cuando se va su empleado |
| Editar un dato guardado de las APIs | Es evidencia de lo que respondió el servicio: se guarda, se lee y se borra, pero no se modifica |
| Cambiar la clave desde el menú | `cambiar_clave` existe en la clase, pero no se guarda en la base todavía |
| Llave de API | Ninguna de las dos APIs la pide. Si una la pidiera, iría en una variable de entorno o en `.env` (ya excluido del repositorio), nunca en el código |

### Límites conocidos

- No hay servidor web, así que XSS y cabeceras HTTP no aplican: los contextos que interpretan datos
  aquí son la terminal y la planilla, y los dos están cubiertos.
- La base no está cifrada y está pensada para un solo usuario a la vez.
- mindicador.cl publica el dólar y el euro observados en Chile, así que un proyecto se paga en
  CLP, USD o EUR. Otra moneda exigiría otra API.
- La limpieza de pantalla usa códigos ANSI: la consola antigua de Windows (`cmd` sin modo VT) los
  muestra como texto. Windows Terminal, Linux y macOS funcionan bien.

## El menú

Veinticinco opciones agrupadas por operación: **C** crear (1-3), **R** leer (4-5), **U**
actualizar (6-8), **D** eliminar (9-10), **S** servicios externos (11-12), **A** administración
(13-14), **P** proyectos (15-20) y **H** historial de las APIs (21-25).
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

   Escriba "x" para cancelar la acción en curso   ·   0. salir
==================================================================

   Opción: 11
   Id del proyecto: 2
   Madrid, España: nublado, 27.1 °C, humedad 20 %, viento 0.8 km/h.
   Condiciones aptas para trabajo en terreno.
   Guardado en el historial del proyecto (registro 1).

   Opción: 12
   Id del proyecto: 2
   Tipo de cambio del 23-09-2026 guardado en el historial.
   Planilla en EUR  (1 EUR = 1,081.49 CLP)
   Camila Reyes Ortiz: 1,260,000 CLP = 1,165.06 EUR
   Ignacio Fuentes Cárdenas: 1,980,000 CLP = 1,830.81 EUR
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
