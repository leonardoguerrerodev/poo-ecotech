# Matriz de rúbrica — EcoTech Solutions, Evaluación Sumativa 2 (U2 + U3)

> **Estado final al 23-sep-2026**, tras ejecutar el plan
> `docs/planes/2026-09-23_auditoria-rubrica-por-etapas.md`. El punto de partida era
> **12 ✅ · 10 ⚠️** en los indicadores y **57 ✅ · 5 ⚠️ · 4 ❌** en el diagrama (commit `9f2410a`, tag
> `u3-pre-auditoria`); el detalle de cada brecha y cómo se cerró está en `AUDITORIA.md` §2.12.
>
> Fuentes: `00_Ramo/Diapositivas/Rubrica_Unidad2.pdf` (22 indicadores, 60 puntos) y
> `00_Ramo/Diapositivas/Guia_CRUD_TI3V21_U2_U3_ES02_GUÍA.pdf` (acciones de cada paso).

## Cómo leer la matriz

- **`.G.`** = se gana con el **código** (13 indicadores, 30,0 puntos).
  **`.I.`** = se gana **explicando** (9 indicadores, 30,0 puntos). En la U2 eso fue la defensa oral
  del 21-sep-2026. Para la U3 no hay defensa oral agendada, aunque la guía la describe: sus `.I.` se
  respaldan en la documentación del repositorio.
- Las referencias `archivo:línea` apuntan al código final. La Tabla 2 **la genera un script** que
  lee el diagrama y el código y compara nombre, visibilidad y parámetros de cada miembro; no se
  escribió a mano.

## Tabla 1 — Los 22 indicadores

| # | Indicador (resumen de la rúbrica) | Exc. | Evidencia | Estado | Observación |
|---|---|---|---|---|---|
| 2.1.1.G.1 | Clases del UML con atributos, constructores y métodos; relaciones representadas en el código | 1,2 | Los 68 miembros del diagrama existen con su nombre, visibilidad y parámetros (Tabla 2, 0 diferencias). Herencia `ecotech.py:194, 235`; las cinco asociaciones viven en la base (Tabla 3) | ✅ | Antes: «participa en», «registra», «imputa a» e «identifica a» sin código |
| 2.1.1.I.2 | Explica la correspondencia UML ↔ código y la traducción de las relaciones | 1,8 | `DEFENSA_ORAL.md` (expuesta); Tablas 2 y 3 | ✅ | — |
| 2.1.2.G.3 | Encapsulamiento, herencia/abstracción, consistencia, reutilización | 1,8 | Atributos `__privados`; `EntidadReportable` y `Persona` abstractas (`ecotech.py:180, 194`); puertas protegidas `_datos_contacto` 221 y `RegistroTiempo._datos` 653; `texto()`, `autorizar()`, `exigir_guardado()` compartidos 43-71 | ✅ | Ya no hay listas internas escribibles desde fuera (`AUDITORIA.md` §3.2, resuelta) |
| 2.1.2.I.4 | Justifica el encapsulamiento y las decisiones contra la duplicación | 2,4 | `DEFENSA_ORAL.md` §3.2 | ✅ | — |
| 2.1.3.G.5 | Conexión con librería oficial; registro, consulta, actualización y eliminación verificados | 2,4 | `sqlite3`; `conectar()` 144 con claves foráneas; CRUD de `Empleado` 292-347, `Departamento` 429-481 y `Proyecto` 561-608; horas 258-284 y 643-651; `SALIDA_TERMINAL.md` §5 | ✅ | Las seis tablas del esquema se usan |
| 2.1.3.I.6 | Configuración de la conexión y lógica del CRUD | 3,0 | `DEFENSA_ORAL.md` | ✅ | — |
| 2.1.4.G.7 | `try/except` en ejecución y conexión; validación de entradas; sin interrupciones | 2,4 | `atender()` (`main.py:483-516`), login protegido (`main.py:552-557`), `pedir_horas` 128, `conectar()` con `finally`; `SALIDA_TERMINAL.md` §5.4 | ✅ | Antes: un hash corrupto cerraba el login con traceback |
| 2.1.4.I.8 | Explica los `try/except` y cómo las validaciones protegen el sistema | 3,6 | `DEFENSA_ORAL.md`; notas de las láminas 4 y 6 | ✅ | — |
| 2.1.5.G.9 | Prueba el código de IA, encuentra errores, modifica/adapta/descarta | 3,0 | `ANALISIS_IA.md` §1-3 (filas 1-25) | ✅ | — |
| 2.1.5.I.10 | Transparencia y criterios seguridad/eficiencia/coherencia | 4,2 | `ANALISIS_IA.md` §2 | ✅ | — |
| 3.1.1.G.11 | Solicitudes HTTP con librería oficial; procesa JSON | 1,8 | `requests` con `timeout` (`servicios.py:108-142`); Open-Meteo y mindicador.cl | ✅ | — |
| 3.1.1.G.12 | Extrae los datos requeridos y los **integra** en el flujo del sistema | 1,8 | El clima se pide para la ciudad **del proyecto** (`main.py:313`) y la planilla del equipo sale en la moneda **del proyecto** (`main.py:326`), con una consulta por planilla; `SALIDA_TERMINAL.md` §5.1 | ✅ | Antes: una ciudad y un sueldo sueltos, sin relación con los proyectos que pide la guía |
| 3.1.1.I.13 | Explica las solicitudes HTTP, el JSON y la integración | 3,0 | `README.md`; `AUDITORIA.md` §2.11; `ANALISIS_IA.md` §4-5 | ✅ | Sin defensa oral de la U3: si el docente la pide, hace falta un guion |
| 3.1.2.G.14 | Autenticación con credenciales cifradas; valida y sanea entradas de las consultas API | 2,4 | scrypt, señuelo y bloqueo (`ecotech.py:698-810`); login robusto; ciudad y moneda validadas en `Proyecto` y otra vez en `servicios.py`; demora medida (`AUDITORIA.md` §2.12) | ✅ | — |
| 3.1.2.G.15 | Protege la información sensible; restringe el consumo de APIs con flujo y sesión | 2,4 | Permisos `proyectos` y `tiempo` separados (`ecotech.py:660-664`); el `EMPLEADO` no consulta APIs y solo registra **sus** horas (262-266); permiso antes de pedir datos (`main.py:58-63, 462`); sesión con caducidad | ✅ | — |
| 3.1.2.I.16 | Explica autenticación, saneamiento, información sensible y control de flujo y sesión | 3,6 | `AUDITORIA.md` §2.11 y §2.12 (tabla de roles vigente); `README.md` § Seguridad | ✅ | Igual que I.13 |
| 3.1.3.G.17 | Excepciones de conectividad, red y tiempos de espera | 2,4 | `servicios.py:114-124`; `SALIDA_TERMINAL.md` §4.2 y §5.3 | ✅ | — |
| 3.1.3.G.18 | Valida códigos HTTP; continuidad y comunicación segura de errores | 2,4 | `servicios.py:126-133`; mensajes fijos también en `crear_tablas()` y `Informe.exportar()` | ✅ | Antes: dos mensajes con la ruta del archivo |
| 3.1.3.I.19 | Explica excepciones, conectividad, tiempos de espera y códigos HTTP | 4,2 | `AUDITORIA.md` §2.11; `SALIDA_TERMINAL.md` §4.3 y §5.4 | ✅ | Igual que I.13 |
| 3.1.4.G.20 | Evidencia y documenta el uso de IA; analiza el código sugerido | 3,0 | `ANALISIS_IA.md` §4 y §6 (filas 26-54); `FLUJO_DE_TRABAJO.md`; `docs/planes/` | ✅ | — |
| 3.1.4.G.21 | Identifica errores, redundancias o vulnerabilidades en el código de IA; refactoriza | 3,0 | `ANALISIS_IA.md` §4-6; `AUDITORIA.md` §2.10-2.12; pruebas de mutación | ✅ | — |
| 3.1.4.I.22 | Explica el uso de IA, el análisis, los errores y la refactorización | 4,2 | `ANALISIS_IA.md` §5-6 | ✅ | Igual que I.13 |

**Estado final: 22 ✅.** Lo único abierto no es de código: las cuatro `.I.` de la U3 dependen de que
el docente lea la documentación, o de un guion si pide defensa oral.

Puntos: U2 = 25,8 (G 10,8 + I 15,0) · U3 = 34,2 (G 19,2 + I 15,0) · total 60,0.

## Tabla 2 — Diagrama (`diagramas/modelo_u3.drawio`) ↔ código, miembro por miembro

Convención del diagrama: atributos y métodos de dominio; **no** el CRUD (`guardar`, `listar`,
`buscar`, `eliminar`, `_desde_fila`, `contar_empleados`, `buscar_por_nombre`, `_datos`) ni las
constantes de clase. El literal de `Rol` (`ADMIN_RRHH`, `GERENTE`, `EMPLEADO`) está en
`ecotech.py:174-177`.

Generada con el comparador de la auditoría: por cada fila del diagrama busca el atributo o el
método en su clase (camelCase → snake_case; `-` → `__`, `#` → `_`) y compara la lista de parámetros.
**68 miembros, 0 diferencias.** La primera corrida encontró una: `autenticar(nombre, clave)` en el
diagrama y `nombre_usuario` en el código, que se corrigió en el código.

### EntidadReportable

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `# id: int [0..1]` | `_id` | `ecotech.py:184` | ✅ |
| `+ obtenerId(): int [0..1]` | `obtener_id` | `ecotech.py:186` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:190` | ✅ |

### Persona

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- nombre: str` | `__nombre` | `ecotech.py:200` | ✅ |
| `- direccion: str` | `__direccion` | `ecotech.py:201` | ✅ |
| `- telefono: str` | `__telefono` | `ecotech.py:218` | ✅ |
| `- correo: str {unique}` | `__correo` | `ecotech.py:219` | ✅ |
| `+ obtenerNombre(): str` | `obtener_nombre` | `ecotech.py:206` | ✅ |
| `+ actualizarContacto(telefono: str, correo: str): void` | `actualizar_contacto` | `ecotech.py:209` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:225` | ✅ |
| `# validarCorreo(correo: str): bool` | `_validar_correo` | `ecotech.py:228` | ✅ |
| `# validarTelefono(telefono: str): bool` | `_validar_telefono` | `ecotech.py:231` | ✅ |
| `- fijarContacto(telefono: str, correo: str): void` | `__fijar_contacto` | `ecotech.py:212` | ✅ |
| `# datosContacto(): tuple` | `_datos_contacto` | `ecotech.py:221` | ✅ |

### Empleado

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- fechaInicioContrato: date` | `__fecha_inicio_contrato` | `ecotech.py:251` | ✅ |
| `- salario: int` | `__salario` | `ecotech.py:252` | ✅ |
| `+ obtenerSalario(solicitante: Usuario): int` | `obtener_salario` | `ecotech.py:254` | ✅ |
| `+ registrarTiempo(proyecto: Proyecto, fecha: date, horas: float, descripcion: str, solicitante: Usuario): RegistroTiempo` | `registrar_tiempo` | `ecotech.py:258` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:286` | ✅ |

### Departamento

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- nombre: str` | `__nombre` | `ecotech.py:355` | ✅ |
| `+ obtenerNombre(): str` | `obtener_nombre` | `ecotech.py:357` | ✅ |
| `+ agregarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `agregar_empleado` | `ecotech.py:360` | ✅ |
| `+ quitarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `quitar_empleado` | `ecotech.py:377` | ✅ |
| `+ asignarGerente(empleado: Empleado, solicitante: Usuario): void` | `asignar_gerente` | `ecotech.py:394` | ✅ |
| `+ listarEmpleados(): list` | `listar_empleados` | `ecotech.py:408` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:417` | ✅ |

### Proyecto

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- nombre: str` | `__nombre` | `ecotech.py:496` | ✅ |
| `- descripcion: str` | `__descripcion` | `ecotech.py:497` | ✅ |
| `# fechaInicio: date` | `_fecha_inicio` | `ecotech.py:498` | ✅ |
| `- ciudad: str` | `__ciudad` | `ecotech.py:499` | ✅ |
| `- moneda: str` | `__moneda` | `ecotech.py:500` | ✅ |
| `+ asignarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `asignar_empleado` | `ecotech.py:502` | ✅ |
| `+ desasignarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `desasignar_empleado` | `ecotech.py:514` | ✅ |
| `+ listarEmpleados(): list` | `listar_empleados` | `ecotech.py:527` | ✅ |
| `+ horasConsumidas(): float` | `horas_consumidas` | `ecotech.py:536` | ✅ |
| `+ obtenerCiudad(): str` | `obtener_ciudad` | `ecotech.py:545` | ✅ |
| `+ obtenerMoneda(): str` | `obtener_moneda` | `ecotech.py:548` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:551` | ✅ |

### RegistroTiempo

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- fecha: date` | `__fecha` | `ecotech.py:620` | ✅ |
| `- horas: float` | `__horas` | `ecotech.py:621` | ✅ |
| `- descripcion: str` | `__descripcion` | `ecotech.py:622` | ✅ |
| `+ obtenerHoras(): float` | `obtener_horas` | `ecotech.py:624` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:627` | ✅ |
| `# validarHoras(horas: float): bool` | `_validar_horas` | `ecotech.py:632` | ✅ |
| `# validarFecha(fecha: date): bool` | `_validar_fecha` | `ecotech.py:635` | ✅ |

### Usuario

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `# id: int [0..1]` | `_id` | `ecotech.py:682` | ✅ |
| `- nombreUsuario: str` | `__nombre_usuario` | `ecotech.py:684` | ✅ |
| `- hashClave: str` | `__hash_clave` | `ecotech.py:689` | ✅ |
| `- rol: Rol` | `__rol` | `ecotech.py:685` | ✅ |
| `- intentosFallidos: int` | `__intentos_fallidos` | `ecotech.py:686` | ✅ |
| `- bloqueadoHasta: datetime [0..1]` | `__bloqueado_hasta` | `ecotech.py:687` | ✅ |
| `+ verificarClave(clave: str): bool` | `verificar_clave` | `ecotech.py:704` | ✅ |
| `+ cambiarClave(actual: str, nueva: str): bool` | `cambiar_clave` | `ecotech.py:712` | ✅ |
| `+ tienePermiso(modulo: str): bool` | `tiene_permiso` | `ecotech.py:729` | ✅ |
| `+ obtenerEmpleado(): Empleado [0..1]` | `obtener_empleado` | `ecotech.py:732` | ✅ |
| `+ autenticar(nombre: str, clave: str): Usuario [0..1]` | `autenticar` | `ecotech.py:781` | ✅ |
| `# hashear(clave: str, sal: bytes, costo: tuple): str` | `_hashear` | `ecotech.py:698` | ✅ |
| `# validarClave(clave: str): bool` | `_validar_clave` | `ecotech.py:720` | ✅ |

### Informe

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- titulo: str` | `__titulo` | `ecotech.py:816` | ✅ |
| `- fechaGeneracion: date` | `__fecha_generacion` | `ecotech.py:817` | ✅ |
| `- contenido: list` | `__contenido` | `ecotech.py:818` | ✅ |
| `+ generar(titulo: str, entidades: list, solicitante: Usuario): Informe` | `generar` | `ecotech.py:821` | ✅ |
| `+ exportar(ruta: str, formato: str): bool` | `exportar` | `ecotech.py:826` | ✅ |
| `+ obtenerTexto(): str` | `obtener_texto` | `ecotech.py:852` | ✅ |

### ServicioExterno

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `+ obtenerClima(ciudad: str): dict` | `obtener_clima` | `servicios.py:49` | ✅ |
| `+ obtenerTipoCambio(moneda: str): float` | `obtener_tipo_cambio` | `servicios.py:92` | ✅ |
| `- consultar(url: str, params: dict): dict` | `__consultar` | `servicios.py:108` | ✅ |
| `# validarCiudad(ciudad: str): bool` | `_validar_ciudad` | `servicios.py:144` | ✅ |

## Tabla 3 — Relaciones

| Relación del diagrama | Multiplicidad | En el código | En la base |
|---|---|---|---|
| Empleado ▷ Persona (herencia) | — | `class Empleado(Persona)` `ecotech.py:235` | columnas de persona en `empleado` |
| Persona, Departamento, Proyecto, RegistroTiempo ▷ EntidadReportable | — | `ecotech.py:194, 350, 484, 610` | sin tabla propia |
| Departamento ◇— Empleado «contiene» | 0..1 — 0..* | `agregar_empleado`, `quitar_empleado`, `listar_empleados` | `empleado.departamento_id` `ON DELETE SET NULL` (97) |
| Departamento — Empleado «gerente» | 0..1 — 0..1 | `asignar_gerente` | `departamento.gerente_id` `ON DELETE SET NULL` (85) |
| Proyecto — Empleado «participa en» | 0..* — 0..* | `asignar_empleado`, `desasignar_empleado`, `listar_empleados` (502-534) | `empleado_proyecto`, cascada por los dos lados (107-113) |
| Empleado ◆— RegistroTiempo «registra» | 1 — 0..* | `registrar_tiempo` (258): el registro solo nace desde su empleado | `registro_tiempo.empleado_id` `ON DELETE CASCADE` (121) |
| Proyecto — RegistroTiempo «imputa a» | 1 — 0..* | `horas_consumidas` (536), `RegistroTiempo.listar(proyecto)` (643) | `registro_tiempo.proyecto_id` sin cascada (122): un proyecto con horas no se borra |
| Usuario — Empleado «identifica a» | 0..1 — 0..1 | `obtener_empleado` (732); obligatorio para `EMPLEADO` | `usuario.empleado_id UNIQUE` `ON DELETE CASCADE` (132-133) |
| Usuario — Rol «tiene» | 0..* — 1 | `self.__rol: Rol` | `CHECK (rol IN …)` |
| Informe ⇢ EntidadReportable «consulta» | — | `Informe.generar(…, entidades: list[EntidadReportable], …)` (821) | sin tabla |

Ninguna relación tiene una copia en memoria: todas se leen y se escriben en la base.
