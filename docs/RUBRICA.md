# Matriz de rúbrica — EcoTech Solutions, Evaluación Sumativa 2 (U2 + U3)

> Estado al **23-sep-2026, antes de la auditoría** (tag `u3-pre-auditoria`, commit `9f2410a`).
> Etapa 2 del plan `docs/planes/2026-09-23_auditoria-rubrica-por-etapas.md`. Los estados ❌ y ⚠️
> son el punto de partida; la etapa 8 los actualiza.
>
> Fuentes: `00_Ramo/Diapositivas/Rubrica_Unidad2.pdf` (22 indicadores, 60 puntos) y
> `00_Ramo/Diapositivas/Guia_CRUD_TI3V21_U2_U3_ES02_GUÍA.pdf` (acciones de cada paso).
> Las referencias `archivo:línea` apuntan al código de ese commit.

## Cómo leer la matriz

- **`.G.`** = se gana con el **código** (13 indicadores, 30,0 puntos).
  **`.I.`** = se gana **explicando** (9 indicadores, 30,0 puntos). En la U2 eso fue la defensa oral
  del 21-sep-2026 (`docs/DEFENSA_ORAL.md`). La U3 no tiene defensa oral agendada según Leo, aunque la
  guía la describe («posterior a la entrega cada estudiante realiza una defensa argumentativa
  individual»). Por eso las `.I.` de la U3 se respaldan en `docs/`.
- ✅ cubierto con evidencia · ⚠️ cubierto con una brecha concreta · ❌ falta.

## Tabla 1 — Los 22 indicadores

| # | Indicador (resumen de la rúbrica) | Exc. | Evidencia | Estado | Brecha |
|---|---|---|---|---|---|
| 2.1.1.G.1 | Clases del UML con atributos, constructores y métodos; relaciones (asociación, herencia) representadas en el código | 1,2 | 9 clases de `modelo_u3` en `ecotech.py:171-720` y `servicios.py:43`; herencia `Persona(EntidadReportable)` 191, `Empleado(Persona)` 232; agregación por FK `empleado.departamento_id` 94-95 | ⚠️ | Asociación «identifica a» (Usuario→Empleado) solo en el esquema (`ecotech.py:129-130`), sin código. `Proyecto` y `RegistroTiempo` sin persistir: la asociación «participa en» vive en listas en memoria (477-478, 251). → E5 |
| 2.1.1.I.2 | Explica la correspondencia UML ↔ código y cómo se tradujeron las relaciones | 1,8 | `DEFENSA_ORAL.md` (expuesto el 21-sep); Tabla 2 de este archivo | ✅ | — (U2 ya expuesta) |
| 2.1.2.G.3 | Encapsulamiento, herencia/abstracción, consistencia diseño-código, reutilización | 1,8 | atributos `__privados` en todas las clases; `EntidadReportable` y `Persona` con `ABC` 177-188, 191-229; `_datos_contacto()` 218; `texto()`, `autorizar()`, `exigir_guardado()` compartidos 42-71 | ⚠️ | `Empleado._proyectos` y `Proyecto._registros` escribibles desde fuera (`AUDITORIA.md` §3.2). Inconsistencias UML↔código de la Tabla 2. → E4, E5c |
| 2.1.2.I.4 | Justifica el encapsulamiento y las decisiones para no duplicar código | 2,4 | `DEFENSA_ORAL.md` §3.2 y marco teórico | ✅ | — |
| 2.1.3.G.5 | Conexión con librería oficial; registro, consulta, actualización y eliminación verificados | 2,4 | `sqlite3` (`ecotech.py:22`); `conectar()` 140-149 con `PRAGMA foreign_keys`; CRUD completo de `Empleado` 276-331 y `Departamento` 411-465; `SALIDA_TERMINAL.md` §2 | ⚠️ | CRUD solo en 2 de las 5 entidades con tabla: `proyecto`, `empleado_proyecto` y `registro_tiempo` existen en el esquema (98-119) y ningún código las lee ni escribe. → E5b-E5d |
| 2.1.3.I.6 | Configuración y parámetros de la conexión; lógica del CRUD | 3,0 | `DEFENSA_ORAL.md` (guion de persistencia) | ✅ | — |
| 2.1.4.G.7 | `try/except` en la ejecución y en la conexión; validación de entradas; sin interrupciones | 2,4 | `conectar()` con `finally` 145-149; `crear_tablas()` atrapa `OSError` 155-158; `atender()` con 9 `except` en orden, `Exception` al final (`main.py:338-370`); `pedir_*` con techo y reintento (`main.py:91-115`) | ⚠️ | **El login no está protegido**: `iniciar_sesion()` (`main.py:396-408`) corre fuera de `atender()`, y `main()` (`main.py:430-441`) solo atrapa `sqlite3.Error`, `Cancelado`, `KeyboardInterrupt` y `EOFError`. Un `hash_clave` corrupto hace que `verificar_clave` lance `ValueError` (`ecotech.py:578-579`) y el programa muere con traceback. Lo mismo con una clave con surrogates (`UnicodeEncodeError` en `clave.encode()`, 572). → E3 |
| 2.1.4.I.8 | Explica los `try/except` y cómo las validaciones protegen el sistema | 3,6 | `DEFENSA_ORAL.md`; notas de las láminas 4 y 6 del mazo ES2 | ✅ | — |
| 2.1.5.G.9 | Prueba el código de IA, encuentra errores, modifica/adapta/descarta con justificación | 3,0 | `ANALISIS_IA.md` §1-3 (filas 1-25: 2 adoptadas, 13 modificadas, 10 descartadas) | ✅ | — |
| 2.1.5.I.10 | Transparencia sobre qué fragmentos vienen de IA; criterios seguridad/eficiencia/coherencia | 4,2 | `ANALISIS_IA.md` §2; `DEFENSA_ORAL.md` (tabla de criterios) | ✅ | — |
| 3.1.1.G.11 | Solicitudes HTTP con librería oficial; procesa JSON | 1,8 | `requests` (`servicios.py:15`); `__consultar()` 108-142 con `timeout`, `status_code` y `.json()`; dos APIs: Open-Meteo 24-25 y mindicador.cl 26 | ✅ | — |
| 3.1.1.G.12 | Extrae los datos requeridos e **integra** los datos de la API en el flujo del sistema | 1,8 | `obtener_clima()` 49-90 extrae temperatura, humedad, viento y estado; `obtener_tipo_cambio()` 92-106; opciones 11 y 12 (`main.py:262-281`) | ⚠️ | La integración es débil: la opción 11 pide una ciudad suelta, sin relación con ningún proyecto, y la 12 convierte el sueldo de **un** empleado a una moneda elegida al vuelo. La guía pide «apoyar la toma de decisiones en la ejecución de proyectos» y «calcular pagos ajustados al país donde se ejecuta el proyecto». → E5b (ciudad y moneda en `Proyecto`) y E6d |
| 3.1.1.I.13 | Explica solicitudes HTTP, JSON e integración, con decisiones técnicas | 3,0 | `README.md`; `AUDITORIA.md` §2.11 «La red»; `ANALISIS_IA.md` §4-5 | ⚠️ | Sin defensa oral: la explicación depende de que el docente lea `docs/`. La integración por proyecto (G.12) debe quedar explicada en el README. → E8 |
| 3.1.2.G.14 | Autenticación con credenciales cifradas y validación de acceso; valida y sanea entradas de las consultas API | 2,4 | scrypt con sal y costo guardado (`ecotech.py:567-582`); `autenticar()` con señuelo y bloqueo 645-675; `getpass` (`main.py:403`); `_validar_ciudad()` (`servicios.py:144-146`) y lista cerrada de monedas 47, 94-97 | ⚠️ | Hueco del login (ver G.7). Demora del login sin medir: el diseño promete la misma demora para cuenta inexistente, clave mala y cuenta bloqueada, y nunca se midió. → E3, E7 |
| 3.1.2.G.15 | Protege la información sensible; restringe el consumo de APIs con controles de flujo y sesión | 2,4 | `PERMISO` revisado antes de pedir datos (`main.py:51-54`, `ejecutar()` 317-328); sesión que caduca a los 10 min (`main.py:56`, 411-427); sueldo solo con permiso `empleados` (`ecotech.py:253-255`); base `0600` 156 | ⚠️ | El EMPLEADO consulta el clima con el permiso `proyectos` (`ecotech.py:541`), que también es el de administrar proyectos: los permisos no separan «consultar» de «administrar». → E5a (permisos `proyectos` / `tiempo`) |
| 3.1.2.I.16 | Explica autenticación, saneamiento, protección de información sensible y control de flujo y sesión | 3,6 | `AUDITORIA.md` §2.11 (login, control de acceso, información sensible); `README.md` tabla de seguridad | ⚠️ | Igual que I.13: sin defensa oral. Falta documentar el vínculo Usuario→Empleado y la tabla de roles nueva. → E8 |
| 3.1.3.G.17 | Excepciones de conectividad, red y tiempos de espera | 2,4 | `requests.Timeout`, `ConnectionError`, `RequestException` (`servicios.py:114-124`); `TIEMPO_ESPERA = (3.05, 10)` 46; `ServicioNoDisponible` atrapada en `atender()` (`main.py:358`); `SALIDA_TERMINAL.md` §4.2 (red cortada) | ✅ | — |
| 3.1.3.G.18 | Valida los códigos HTTP; continuidad operativa y **comunicación segura de errores** | 2,4 | `status_code != 200` con 5xx, 400, 404, 429 y resto (`servicios.py:126-133`); `raise … from None`; `atender()` sigue el bucle | ⚠️ | **Hallazgo nuevo, fuera del plan:** dos mensajes todavía imprimen el texto crudo de un `OSError`, que trae la ruta absoluta del archivo: `crear_tablas()` (`ecotech.py:158`) e `Informe.exportar()` (`ecotech.py:714`). Contradice `AUDITORIA.md` §2.11 «Mensajes de error que no filtran nada». Pendiente de decisión de Leo |
| 3.1.3.I.19 | Explica excepciones, conectividad, tiempos de espera y códigos HTTP | 4,2 | `AUDITORIA.md` §2.11 «La red»; `SALIDA_TERMINAL.md` §4.3 | ✅ | — (sin defensa oral: la explicación ya está completa en docs) |
| 3.1.4.G.20 | Evidencia y documenta el uso de IA; analiza el código sugerido | 3,0 | `ANALISIS_IA.md` §4 (filas 26-43), `FLUJO_DE_TRABAJO.md`, `docs/planes/` | ✅ | Se amplía con lo que ocurra en esta auditoría. → E8 (filas desde la 44) |
| 3.1.4.G.21 | Identifica errores, redundancias o vulnerabilidades en código de IA; refactoriza y justifica | 3,0 | `ANALISIS_IA.md` §4-5; `AUDITORIA.md` §2.10 (SonarCloud) y §2.11 | ✅ | — |
| 3.1.4.I.22 | Explica el uso de IA, el análisis, los errores encontrados y la refactorización | 4,2 | `ANALISIS_IA.md` §5 «Lo que cambió respecto de la Unidad 2» | ✅ | — |

**Resumen de partida:** 12 ✅ · 10 ⚠️ · 0 ❌. Los ⚠️ que cierra el plan son G.1, G.3, G.5, G.7, G.12,
G.14 y G.15, e I.13 e I.16 por documentación. **G.18 queda abierto**: su brecha no está en el plan.

Puntos: U2 = 25,8 (G 10,8 + I 15,0) · U3 = 34,2 (G 19,2 + I 15,0) · total 60,0.

## Tabla 2 — UML (`diagramas/modelo_u3.drawio`) ↔ código

Convención del diagrama (decisión de Leo, plan del 21-sep): se muestran atributos y métodos de
dominio; **no** se muestran el CRUD (`guardar`, `listar`, `buscar`, `eliminar`, `_desde_fila`,
`contar_empleados`) ni las constantes de clase. Las filas que hoy rompen esa convención van ❌.
El diagrama tiene **66 miembros** (celdas cuyo texto empieza con `+`, `#` o `-`; mismo número con
`grep -o 'value="[+#-] ' diagramas/modelo_u3.drawio | wc -l`). Los literales de `Rol` no cuentan.

Código: `ecotech.py` salvo que diga `servicios.py`. `ok` = mismo nombre (camelCase → snake_case),
visibilidad y firma.

### «abstracta» EntidadReportable

| Miembro UML | Código | Estado |
|---|---|---|
| `# id: int [0..1]` | `self._id` 181 | ✅ |
| `+ obtenerId(): int [0..1]` | `obtener_id` 183 | ✅ |
| `+ obtenerResumen(): str` *(abstracto)* | `@abstractmethod obtener_resumen` 186-188 | ✅ |

### «abstracta» Persona

| Miembro UML | Código | Estado |
|---|---|---|
| `- nombre: str` | `self.__nombre` 197 | ✅ |
| `- direccion: str` | `self.__direccion` 198 | ✅ |
| `- telefono: str` | `self.__telefono` 215 | ✅ |
| `- correo: str {unique}` | `self.__correo` 216; `UNIQUE` en la tabla 91 | ✅ |
| `+ obtenerNombre(): str` | 203 | ✅ |
| `+ actualizarContacto(telefono, correo): void` | 206 | ✅ |
| `+ obtenerResumen(): str` | 221-223 (abstracto con cuerpo) | ✅ |
| `# validarCorreo(correo): bool` | `_validar_correo` 225 | ✅ |
| `# validarTelefono(telefono): bool` | `_validar_telefono` 228 | ✅ |
| `- fijarContacto(telefono, correo): void` | `__fijar_contacto` 209 | ✅ |
| `# datosContacto(): tuple` | `_datos_contacto` 218 | ✅ |

### Empleado

| Miembro UML | Código | Estado |
|---|---|---|
| `- fechaInicioContrato: date` | `self.__fecha_inicio_contrato` 248 | ✅ |
| `- salario: int` | `self.__salario` 249 | ✅ |
| `+ obtenerSalario(solicitante: Usuario): int` | 253 | ✅ |
| `+ registrarTiempo(proyecto, fecha, horas, descripcion): RegistroTiempo` | 257-268 | ⚠️ escribe solo en memoria (listas 250-251) y no pide `solicitante`. → E4 y E5d |
| `+ obtenerResumen(): str` | 270 | ✅ |
| *(fuera del UML)* `__registros`, `_proyectos` | 250-251 | ❌ copias en memoria de relaciones que el esquema ya persiste; rompen la regla 13 de la memoria. → E5c, E5d |

### Departamento

| Miembro UML | Código | Estado |
|---|---|---|
| `- nombre: str` | `self.__nombre` 339 | ✅ |
| `+ obtenerNombre(): str` | 341 | ✅ |
| `+ agregarEmpleado(empleado, solicitante): bool` | 344 | ✅ |
| `+ quitarEmpleado(empleado, solicitante): bool` | 361 | ✅ |
| `+ asignarGerente(empleado, solicitante): void` | 378 | ✅ |
| `+ listarEmpleados(): list` | 392 | ✅ |
| `+ obtenerResumen(): str` | 401 | ✅ |

### Proyecto

| Miembro UML | Código | Estado |
|---|---|---|
| `- nombre: str` | `self.__nombre` 474 | ✅ |
| `- descripcion: str` | `self.__descripcion` 475 | ✅ |
| `# fechaInicio: date` | `self._fecha_inicio` 476 | ✅ |
| `+ asignarEmpleado(empleado): bool` | 480 | ⚠️ solo en memoria; sin `solicitante`. → E4, E5c |
| `+ desasignarEmpleado(empleado): bool` | 487 | ⚠️ ídem |
| `+ horasConsumidas(): float` | 494 | ⚠️ suma una lista en memoria. → E5c |
| `+ obtenerResumen(): str` | 497 | ⚠️ cuenta la lista en memoria. → E5c |
| *(falta en ambos)* `ciudad`, `moneda`, `listarEmpleados`, `obtenerCiudad`, `obtenerMoneda` | — | ❌ decisión de Leo del 21-sep. → E4, E5b |

### RegistroTiempo

| Miembro UML | Código | Estado |
|---|---|---|
| `- fecha: date` | `self.__fecha` 515 | ✅ |
| `- horas: float` | `self.__horas` 516 | ✅ |
| `- descripcion: str` | `self.__descripcion` 517 | ✅ |
| `+ obtenerHoras(): float` | 519 | ✅ |
| `+ obtenerResumen(): str` | 522 | ✅ |
| `# validarHoras(horas): bool` | `_validar_horas` 527 | ✅ |
| `# validarFecha(fecha): bool` | `_validar_fecha` 530 | ✅ |
| *(persistencia)* | tabla `registro_tiempo` 111-119 sin uso | ❌ → E5d |

### Usuario

| Miembro UML | Código | Estado |
|---|---|---|
| `# id: int [0..1]` | `self._id` 555 | ✅ |
| `- nombreUsuario: str` | `self.__nombre_usuario` 556 | ✅ |
| `- hashClave: str` | `self.__hash_clave` 561/565 | ✅ |
| `- rol: Rol` | `self.__rol` 557 | ✅ |
| `- intentosFallidos: int` | `self.__intentos_fallidos` 558 | ✅ |
| `- bloqueadoHasta: datetime [0..1]` | `self.__bloqueado_hasta` 559 | ✅ |
| `+ verificarClave(clave): bool` | 576 | ✅ |
| `+ cambiarClave(actual, nueva): bool` | 584 | ✅ (no persiste: declarado en `AUDITORIA.md` §3.5) |
| `+ tienePermiso(modulo): bool` | 601 | ✅ |
| `+ guardar(solicitante: Usuario [0..1]): int` | 606 | ❌ el método existe, pero es CRUD y el diagrama no debe mostrarlo. → E4 (sale del UML) |
| `+ buscarPorNombre(nombre): Usuario [0..1]` | 628 | ❌ ídem. → E4 |
| `+ autenticar(nombre, clave): Usuario [0..1]` *(estático)* | `@classmethod` 645 | ✅ |
| `# hashear(clave, sal, costo): str` | `@classmethod _hashear` 569 | ✅ |
| `# validarClave(clave): bool` | `_validar_clave` 592 | ✅ |
| *(falta en ambos)* `obtenerEmpleado(): Empleado [0..1]` | — | ❌ → E4, E5a |
| *(fuera del UML, constantes)* `_PERMISOS`, `COLUMNAS`, `MAX_INTENTOS`, `BLOQUEO`, `COSTO` | 537-567 | ✅ conforme a la convención (no se muestran) |

### «enumeration» Rol

| Miembro UML | Código | Estado |
|---|---|---|
| `ADMIN_RRHH`, `GERENTE`, `EMPLEADO` | `class Rol(Enum)` 171-174 | ✅ |

### «control» Informe

| Miembro UML | Código | Estado |
|---|---|---|
| `- titulo: str` | `self.__titulo` 681 | ✅ |
| `- fechaGeneracion: date` | `self.__fecha_generacion` 682 | ✅ |
| `- contenido: list` | `self.__contenido` 683 | ✅ |
| `+ generar(titulo, entidades, solicitante): Informe` | `@staticmethod` 685-689 | ✅ |
| `+ exportar(ruta, formato): bool` | 691 | ✅ (ver G.18: mensaje del `OSError`) |
| `+ obtenerTexto(): str` | 717 | ✅ |

### «boundary» ServicioExterno (`servicios.py`)

| Miembro UML | Código | Estado |
|---|---|---|
| `+ TIEMPO_ESPERA: tuple` | 46 | ❌ constante de clase en el diagrama; la convención dice que no va. → E4 |
| `+ MONEDAS: dict` | 47 | ❌ ídem. → E4 |
| `+ obtenerClima(ciudad): dict` | 49 | ✅ |
| `+ obtenerTipoCambio(moneda): float` | 92 | ✅ |
| `- consultar(url, params): dict` | `__consultar` 108 | ✅ |
| `# validarCiudad(ciudad): bool` | `_validar_ciudad` 144 | ✅ |

### Relaciones

| Relación UML | Multiplicidad | Código | Estado |
|---|---|---|---|
| Empleado ▷ Persona (herencia) | — | `class Empleado(Persona)` 232 | ✅ |
| Persona, Departamento, Proyecto, RegistroTiempo ▷ EntidadReportable | — | 191, 334, 468, 505 | ✅ |
| Departamento ◇— Empleado «contiene» | 0..1 — 0..* | FK `empleado.departamento_id … ON DELETE SET NULL` 94-95; métodos 344-399 | ✅ |
| Departamento — Empleado «gerente» | 0..1 — 0..1 | FK `departamento.gerente_id` 82-83; `asignar_gerente` 378 | ✅ |
| Proyecto — Empleado «participa en» | 0..* — 0..* | tabla `empleado_proyecto` 104-110 **sin uso**; listas en memoria 477-478, 251 | ❌ → E5c |
| Empleado ◆— RegistroTiempo «registra» | 1 — 0..* | FK `registro_tiempo.empleado_id … ON DELETE CASCADE` 116-118 **sin uso**; lista 250 | ❌ → E5d |
| Proyecto — RegistroTiempo «imputa a» | 1 — 0..* | FK `registro_tiempo.proyecto_id` 117-119 **sin uso**; lista 477 | ❌ → E5d |
| Usuario — Empleado «identifica a» | 0..1 — 0..1 | columna `usuario.empleado_id UNIQUE … ON DELETE CASCADE` 129-130; **ningún método la lee ni la escribe** | ❌ → E5a |
| Usuario — Rol «tiene» | 0..* — 1 | `self.__rol: Rol`; `CHECK (rol IN …)` 124-125 | ✅ |
| Informe ⇢ EntidadReportable «consulta» | — | `generar(…, entidades: list[EntidadReportable], …)` 686 | ✅ |

**Resumen Tabla 2:** 66 miembros del diagrama. **57 ✅, 5 ⚠️ y 4 ❌**: los ❌ son `Usuario.guardar`,
`Usuario.buscarPorNombre`, `TIEMPO_ESPERA` y `MONEDAS`; los ⚠️ son `registrarTiempo` y los cuatro
métodos de `Proyecto` que trabajan en memoria. A eso se suman los que faltan en el
diagrama y en el código (`ciudad`, `moneda`, `listarEmpleados`, `obtenerCiudad`, `obtenerMoneda`,
`obtenerEmpleado`), y las 4 relaciones ❌, todas del lado de la persistencia.
