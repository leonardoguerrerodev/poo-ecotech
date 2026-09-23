# Matriz de rúbrica — EcoTech Solutions, Evaluación Sumativa 2 (U2 + U3)

> **Estado al 23-sep-2026, después de la pasada 8 y su corrección** (`AUDITORIA.md` §2.13). Generado por `docs/herramientas/e10_rubrica.py`: las referencias `archivo:línea` se
> calculan desde el código y la Tabla 2 la produce un comparador, no se escriben a mano.
> Punto de partida de la pasada 7: 12 ✅ · 10 ⚠️ (commit `cf608ef`).
>
> Fuentes: `00_Ramo/Diapositivas/Rubrica_Unidad2.pdf` (22 indicadores, 60 puntos),
> `Guia_CRUD_TI3V21_U2_U3_ES02_GUÍA.pdf` y el bloque 5 del docente, `5_poo_servicios_rubensch.pdf`
> (láminas 34-35: dónde se demuestra cada criterio de la U3).

## Cómo leer la matriz

- **`.G.`** se gana con el código (13 indicadores); **`.I.`** se gana explicando (9). La U3 es una
  evaluación individual, sin defensa oral en este entregable (lámina 34): sus `.I.` se respaldan en la
  documentación del repositorio.
- ✅ cubierto con evidencia · ⚠️ cubierto, con una brecha concreta y abierta.

## Tabla 1 — Los 22 indicadores

| # | Indicador (resumen) | Exc. | Evidencia | Estado | Observación |
|---|---|---|---|---|---|
| 2.1.1.G.1 | Clases del UML con atributos, constructores y métodos; relaciones en el código | 1,2 | 89 miembros del diagrama iguales al código (Tabla 2); las relaciones viven en la base (Tabla 3) | ✅ | — |
| 2.1.1.I.2 | Explica la correspondencia UML ↔ código | 1,8 | `DEFENSA_ORAL.md` (expuesta); Tablas 2 y 3 | ✅ | — |
| 2.1.2.G.3 | Encapsulamiento, herencia/abstracción, reutilización | 1,8 | Atributos `__privados`; `EntidadReportable` y `Persona` abstractas; seis clases heredan de `EntidadReportable`; `texto()` `ecotech.py:45-53` y `exigir_guardado()` `ecotech.py:69-73` compartidos | ✅ | — |
| 2.1.2.I.4 | Justifica el encapsulamiento | 2,4 | `DEFENSA_ORAL.md` §3.2 | ✅ | — |
| 2.1.3.G.5 | Conexión con librería oficial y CRUD verificado | 2,4 | `sqlite3`; `conectar()` `ecotech.py:165-173`; CRUD de `Empleado` `ecotech.py:256-368`, `Departamento` `ecotech.py:371-502`, `Proyecto` `ecotech.py:505-628`, `RegistroClima` `ecotech.py:678-764` y `TipoCambio` `ecotech.py:767-849`; `SALIDA_TERMINAL.md` §5-6 | ✅ | Las ocho tablas se usan |
| 2.1.3.I.6 | Configuración de la conexión y lógica del CRUD | 3,0 | `DEFENSA_ORAL.md` | ✅ | — |
| 2.1.4.G.7 | `try/except`, validación de entradas, sin interrupciones | 2,4 | `atender()` `main.py:591-624`; login protegido `main.py:651-669`; 13 entradas hostiles rechazadas sin traza (`AUDITORIA.md` §2.13) | ✅ | A8-05 corregido: un `.env` ilegible se ignora con aviso |
| 2.1.4.I.8 | Explica los `try/except` | 3,6 | `DEFENSA_ORAL.md` | ✅ | — |
| 2.1.5.G.9 | Prueba y ajusta el código de IA | 3,0 | `ANALISIS_IA.md` §1-3 | ✅ | — |
| 2.1.5.I.10 | Transparencia y criterios | 4,2 | `ANALISIS_IA.md` §2 | ✅ | — |
| 3.1.1.G.11 | Solicitudes HTTP con librería oficial; JSON | 1,8 | `requests` en `__consultar` `servicios.py:193-230`; `requirements.txt` con versión exacta | ✅ | A8-04 corregido: versiones sin avisos en OSV (23-sep-2026) |
| 3.1.1.G.12 | Extrae, **integra y verifica** los datos de la API | 1,8 | Clima y planilla por proyecto; el dato se valida y se **guarda** (`clima_del_proyecto` `main.py:328-354`, `tipo_cambio_del_dia` `main.py:357-372`, opción 21 `main.py:496-515`) | ✅ | El clima y el tipo de cambio se validan por rango antes de usarse (`_en_rango` `servicios.py:60-63`, `__extraer_valor` `servicios.py:178-191`); A8-02 y A8-07 corregidos |
| 3.1.1.I.13 | Explica HTTP, JSON e integración | 3,0 | `README.md`; `AUDITORIA.md` §2.11; `ANALISIS_IA.md` §4-7 | ✅ | — |
| 3.1.2.G.14 | Autenticación con credenciales cifradas; valida y sanea entradas de las APIs | 2,4 | scrypt, señuelo y bloqueo (`autenticar` `ecotech.py:976-1004`); primera cuenta creada en el primer uso, sin credenciales en el código; ciudad y moneda validadas; **variables de entorno** con `https` exigido (`__consultar`) y `.env.example` | ✅ | — |
| 3.1.2.G.15 | Protege la información sensible; controla flujo y sesión | 2,4 | Permisos `proyectos`/`tiempo`, revisados antes de pedir datos (`main.py:63`); matriz real 3 roles × 25 opciones igual a la documentada | ✅ | A8-01 corregido: la inactividad cuenta también en la pausa (`usar_sesion` `main.py:672-694`). A8-03 corregido: sin permiso `empleados`, solo id y nombre (`listar_empleados` `main.py:183-191`) |
| 3.1.2.I.16 | Explica autenticación y protección | 3,6 | `AUDITORIA.md` §2.11-2.13; `README.md` § Seguridad | ✅ | — |
| 3.1.3.G.17 | Conectividad, red y tiempos de espera | 2,4 | `__consultar`; degradación en dos capas (`__con_respaldo` `servicios.py:166-176` y última fila guardada); `SALIDA_TERMINAL.md` §6.2-6.3 | ✅ | — |
| 3.1.3.G.18 | Códigos HTTP; continuidad y comunicación segura de errores | 2,4 | Código revisado antes del cuerpo; mensajes fijos; configuración insegura rechazada sin repetirla (`SALIDA_TERMINAL.md` §6.4) | ✅ | Hallazgo Bajo abierto: redirecciones no verificadas (A8-06) |
| 3.1.3.I.19 | Explica excepciones, red y códigos | 4,2 | `AUDITORIA.md` §2.11; `SALIDA_TERMINAL.md` §4-6 | ✅ | — |
| 3.1.4.G.20 | Evidencia el uso de IA | 3,0 | `ANALISIS_IA.md` §4-7 (filas 26-63) y tabla de 5 aspectos | ✅ | — |
| 3.1.4.G.21 | Errores y vulnerabilidades del código de IA, refactorizados | 3,0 | `ANALISIS_IA.md` §4-7; `AUDITORIA.md` §2.10-2.13; pruebas de mutación | ✅ | — |
| 3.1.4.I.22 | Explica el uso de IA y la refactorización | 4,2 | `ANALISIS_IA.md` §5-7 | ✅ | — |

**Estado: 22 ✅.** Las dos brechas de la pasada 8 (3.1.1.G.12 y 3.1.2.G.15) se corrigieron el
23-sep-2026; el seguimiento está en `AUDITORIA.md` §2.13.

## Tabla 2 — Diagrama (`diagramas/modelo_u3.drawio`) ↔ código, miembro por miembro

Convención del diagrama: atributos y métodos de dominio; no el CRUD ni las constantes de clase. El
comparador busca cada fila del diagrama en su clase (camelCase → snake_case; `-` → `__`, `#` → `_`) y
compara los parámetros. **89 miembros, 0 diferencias.**

### EntidadReportable

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `# id: int [0..1]` | `_id` | `ecotech.py:205` | ✅ |
| `+ obtenerId(): int [0..1]` | `obtener_id` | `ecotech.py:207` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:211` | ✅ |

### Persona

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- nombre: str` | `__nombre` | `ecotech.py:221` | ✅ |
| `- direccion: str` | `__direccion` | `ecotech.py:222` | ✅ |
| `- telefono: str` | `__telefono` | `ecotech.py:239` | ✅ |
| `- correo: str {unique}` | `__correo` | `ecotech.py:240` | ✅ |
| `+ obtenerNombre(): str` | `obtener_nombre` | `ecotech.py:227` | ✅ |
| `+ actualizarContacto(telefono: str, correo: str): void` | `actualizar_contacto` | `ecotech.py:230` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:246` | ✅ |
| `# validarCorreo(correo: str): bool` | `_validar_correo` | `ecotech.py:249` | ✅ |
| `# validarTelefono(telefono: str): bool` | `_validar_telefono` | `ecotech.py:252` | ✅ |
| `- fijarContacto(telefono: str, correo: str): void` | `__fijar_contacto` | `ecotech.py:233` | ✅ |
| `# datosContacto(): tuple` | `_datos_contacto` | `ecotech.py:242` | ✅ |

### Empleado

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- fechaInicioContrato: date` | `__fecha_inicio_contrato` | `ecotech.py:272` | ✅ |
| `- salario: int` | `__salario` | `ecotech.py:273` | ✅ |
| `+ obtenerSalario(solicitante: Usuario): int` | `obtener_salario` | `ecotech.py:275` | ✅ |
| `+ registrarTiempo(proyecto: Proyecto, fecha: date, horas: float, descripcion: str, solicitante: Usuario): RegistroTiempo` | `registrar_tiempo` | `ecotech.py:279` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:307` | ✅ |

### Departamento

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- nombre: str` | `__nombre` | `ecotech.py:376` | ✅ |
| `+ obtenerNombre(): str` | `obtener_nombre` | `ecotech.py:378` | ✅ |
| `+ agregarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `agregar_empleado` | `ecotech.py:381` | ✅ |
| `+ quitarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `quitar_empleado` | `ecotech.py:398` | ✅ |
| `+ asignarGerente(empleado: Empleado, solicitante: Usuario): void` | `asignar_gerente` | `ecotech.py:415` | ✅ |
| `+ listarEmpleados(): list` | `listar_empleados` | `ecotech.py:429` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:438` | ✅ |

### Proyecto

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- nombre: str` | `__nombre` | `ecotech.py:517` | ✅ |
| `- descripcion: str` | `__descripcion` | `ecotech.py:518` | ✅ |
| `# fechaInicio: date` | `_fecha_inicio` | `ecotech.py:519` | ✅ |
| `- ciudad: str` | `__ciudad` | `ecotech.py:520` | ✅ |
| `- moneda: str` | `__moneda` | `ecotech.py:521` | ✅ |
| `+ asignarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `asignar_empleado` | `ecotech.py:523` | ✅ |
| `+ desasignarEmpleado(empleado: Empleado, solicitante: Usuario): bool` | `desasignar_empleado` | `ecotech.py:535` | ✅ |
| `+ listarEmpleados(): list` | `listar_empleados` | `ecotech.py:548` | ✅ |
| `+ horasConsumidas(): float` | `horas_consumidas` | `ecotech.py:557` | ✅ |
| `+ obtenerCiudad(): str` | `obtener_ciudad` | `ecotech.py:566` | ✅ |
| `+ obtenerMoneda(): str` | `obtener_moneda` | `ecotech.py:569` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:572` | ✅ |

### RegistroTiempo

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- fecha: date` | `__fecha` | `ecotech.py:641` | ✅ |
| `- horas: float` | `__horas` | `ecotech.py:642` | ✅ |
| `- descripcion: str` | `__descripcion` | `ecotech.py:643` | ✅ |
| `+ obtenerHoras(): float` | `obtener_horas` | `ecotech.py:645` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:648` | ✅ |
| `# validarHoras(horas: float): bool` | `_validar_horas` | `ecotech.py:653` | ✅ |
| `# validarFecha(fecha: date): bool` | `_validar_fecha` | `ecotech.py:656` | ✅ |

### Usuario

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `# id: int [0..1]` | `_id` | `ecotech.py:877` | ✅ |
| `- nombreUsuario: str` | `__nombre_usuario` | `ecotech.py:879` | ✅ |
| `- hashClave: str` | `__hash_clave` | `ecotech.py:884` | ✅ |
| `- rol: Rol` | `__rol` | `ecotech.py:880` | ✅ |
| `- intentosFallidos: int` | `__intentos_fallidos` | `ecotech.py:881` | ✅ |
| `- bloqueadoHasta: datetime [0..1]` | `__bloqueado_hasta` | `ecotech.py:882` | ✅ |
| `+ verificarClave(clave: str): bool` | `verificar_clave` | `ecotech.py:899` | ✅ |
| `+ cambiarClave(actual: str, nueva: str): bool` | `cambiar_clave` | `ecotech.py:907` | ✅ |
| `+ tienePermiso(modulo: str): bool` | `tiene_permiso` | `ecotech.py:924` | ✅ |
| `+ obtenerEmpleado(): Empleado [0..1]` | `obtener_empleado` | `ecotech.py:927` | ✅ |
| `+ autenticar(nombre: str, clave: str): Usuario [0..1]` | `autenticar` | `ecotech.py:976` | ✅ |
| `# hashear(clave: str, sal: bytes, costo: tuple): str` | `_hashear` | `ecotech.py:893` | ✅ |
| `# validarClave(clave: str): bool` | `_validar_clave` | `ecotech.py:915` | ✅ |

### Informe

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- titulo: str` | `__titulo` | `ecotech.py:1011` | ✅ |
| `- fechaGeneracion: date` | `__fecha_generacion` | `ecotech.py:1012` | ✅ |
| `- contenido: list` | `__contenido` | `ecotech.py:1013` | ✅ |
| `+ generar(titulo: str, entidades: list, solicitante: Usuario): Informe` | `generar` | `ecotech.py:1016` | ✅ |
| `+ exportar(ruta: str, formato: str): bool` | `exportar` | `ecotech.py:1021` | ✅ |
| `+ obtenerTexto(): str` | `obtener_texto` | `ecotech.py:1051` | ✅ |

### ServicioExterno

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- urlGeocodificacion: str` | `__url_geocodificacion` | `servicios.py:96` | ✅ |
| `- urlClima: str` | `__url_clima` | `servicios.py:98` | ✅ |
| `- urlIndicadores: str` | `__url_indicadores` | `servicios.py:99` | ✅ |
| `- tiempoEspera: float [0..1]` | `__tiempo_espera` | `servicios.py:102` | ✅ |
| `- ultimos: dict` | `__ultimos` | `servicios.py:106` | ✅ |
| `+ obtenerClima(ciudad: str): dict` | `obtener_clima` | `servicios.py:108` | ✅ |
| `+ obtenerTipoCambio(moneda: str): dict` | `obtener_tipo_cambio` | `servicios.py:156` | ✅ |
| `- consultar(url: str, params: dict): dict` | `__consultar` | `servicios.py:193` | ✅ |
| `# validarCiudad(ciudad: str): bool` | `_validar_ciudad` | `servicios.py:232` | ✅ |
| `- extraerValor(datos: dict): dict` | `__extraer_valor` | `servicios.py:178` | ✅ |
| `- conRespaldo(clave: tuple, consulta): dict` | `__con_respaldo` | `servicios.py:166` | ✅ |
| `- climaDe(ciudad: str): dict` | `__clima_de` | `servicios.py:116` | ✅ |

### RegistroClima

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- fechaConsulta: datetime` | `__fecha_consulta` | `ecotech.py:694` | ✅ |
| `- ciudad: str` | `__ciudad` | `ecotech.py:695` | ✅ |
| `- temperatura: float` | `__temperatura` | `ecotech.py:696` | ✅ |
| `- humedad: int` | `__humedad` | `ecotech.py:697` | ✅ |
| `- viento: float` | `__viento` | `ecotech.py:698` | ✅ |
| `- estado: str` | `__estado` | `ecotech.py:699` | ✅ |
| `- aptoTerreno: bool` | `__apto_terreno` | `ecotech.py:700` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:702` | ✅ |

### TipoCambio

| Miembro UML | Código | Dónde | Estado |
|---|---|---|---|
| `- moneda: str` | `__moneda` | `ecotech.py:784` | ✅ |
| `- fecha: date` | `__fecha` | `ecotech.py:785` | ✅ |
| `- valor: float` | `__valor` | `ecotech.py:786` | ✅ |
| `+ obtenerValor(): float` | `obtener_valor` | `ecotech.py:788` | ✅ |
| `+ obtenerResumen(): str` | `obtener_resumen` | `ecotech.py:791` | ✅ |

## Tabla 3 — Relaciones

| Relación | Multiplicidad | Código | Base |
|---|---|---|---|
| Empleado ▷ Persona; Persona, Departamento, Proyecto, RegistroTiempo, RegistroClima, TipoCambio ▷ EntidadReportable | — | declaraciones de clase | sin tabla propia para las abstractas |
| Departamento ◇— Empleado «contiene» | 0..1 — 0..* | `agregar_empleado`, `quitar_empleado` | `empleado.departamento_id` `ON DELETE SET NULL` |
| Departamento — Empleado «gerente» | 0..1 — 0..1 | `asignar_gerente` | `departamento.gerente_id` |
| Proyecto — Empleado «participa en» | 0..* — 0..* | `asignar_empleado`, `desasignar_empleado` | `empleado_proyecto` |
| Empleado ◆— RegistroTiempo «registra» | 1 — 0..* | `registrar_tiempo` `ecotech.py:279-305` | `ON DELETE CASCADE` |
| Proyecto — RegistroTiempo «imputa a» | 1 — 0..* | `horas_consumidas` | sin cascada: un proyecto con horas no se borra |
| **Proyecto ◆— RegistroClima «registra clima»** | 1 — 0..* | `RegistroClima.guardar(proyecto, …)`, `listar(proyecto)` | `registro_clima.proyecto_id` `ON DELETE CASCADE` |
| Usuario — Empleado «identifica a» | 0..1 — 0..1 | `obtener_empleado` | `usuario.empleado_id UNIQUE` `ON DELETE CASCADE` |
| Usuario — Rol «tiene» | 0..* — 1 | `self.__rol: Rol` | `CHECK (rol IN …)` |
| Informe ⇢ EntidadReportable «consulta» | — | `Informe.generar(…, entidades, …)` | sin tabla |

Ninguna relación tiene copia en memoria.
