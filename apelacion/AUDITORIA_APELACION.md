**Auditoría de la apelación · ES2 · Leonardo Guerrero**

Este documento es para revisar la apelación a fondo. [**"APELACION.md"**](APELACION.md) es el resumen; aquí está el método, cada afirmación de la corrección separada y contrastada con el código, lo que se buscó para ver si la corrección podía tener razón, y los límites de lo que se afirma.

**Qué se auditó:** el commit evaluado **"36f94ac"** ([ver el árbol](https://github.com/leonardoguerrerodev/poo-ecotech/tree/36f94ac5b6292a9c20a2957217c5226a90ca4eb9)), en **"ecotech.py"**, **"main.py"**, **"servicios.py"** y **"docs/ANALISIS_IA.md"**. Todos los enlaces apuntan a ese commit.

**Contra qué:** la hoja de retroalimentación del docente (instrumentos TI3021_EA_U2_ES02_EV04 y TI3021_RU_U3_ES03_EV06) y la rúbrica publicada en el AAI para la ES2, de 22 indicadores.


**1. Método**

1. Se transcribió literal cada comentario de la hoja: el del indicador y el de las observaciones finales.
2. Cada comentario se separó en afirmaciones simples, una por cosa que se puede comprobar.
3. Cada afirmación se contrastó con el código, línea por línea.
4. Se buscó activamente un contraejemplo: alguna parte del código donde la afirmación sí fuera cierta.
5. Cada afirmación se reprodujo con una prueba automática, sin internet y sin tocar la base real ([**"prueba_apelacion.py"**](prueba_apelacion.py), salida en [**"SALIDA_APELACION.md"**](SALIDA_APELACION.md)). GitHub Actions la vuelve a correr y antes comprueba que el código es idéntico al del commit evaluado.
6. Se declaró lo que no se afirma.


**2. Correspondencia entre la hoja y la rúbrica publicada**

La hoja del docente divide cada indicador "G" de la rúbrica publicada en dos. Los textos coinciden:

| Hoja del docente | Rúbrica publicada | Texto del indicador en la hoja |
|---|---|---|
| 2.1.4.G.14 | 2.1.4.G.7, segunda parte | "Valida las entradas de datos del usuario y gestiona adecuadamente los errores detectados, evitando interrupciones en el funcionamiento del sistema." |
| 2.1.5.G.18 | 2.1.5.G.9, segunda parte | "Modifica, adapta o descarta el código generado por IA en función de los requerimientos de la solución, justificando técnicamente las decisiones adoptadas." |
| 3.1.2.I.6 | 3.1.2.G.14, segunda parte | "Valida y sanea credenciales y entradas de usuario utilizadas en consultas API." |
| 3.1.2.I.8 | 3.1.2.G.15, segunda parte | "restringiendo además el acceso al consumo de APIs mediante controles seguros de flujo y sesión" (texto de la rúbrica publicada) |
| 3.1.3.I.11 | 3.1.3.G.18, primera parte | "Valida y gestiona los códigos de respuesta HTTP devueltos por la API." |
| 3.1.3.I.12 | 3.1.3.G.18, segunda parte | "Garantiza continuidad operativa y comunica errores de forma segura." |
| 3.1.4.I.16 | 3.1.4.G.21, segunda parte | "Refactoriza el código generado por IA y justifica técnicamente las decisiones adoptadas." |


**3. Resumen**

| Indicador | Puntaje | En disputa | Afirmaciones | Refutadas | Pruebas |
|---|---|---|---|---|---|
| 2.1.4.G.14 | 3/5 | 2 | 3 | 3 | 8 |
| 3.1.2.I.6 | 4,5/6 | 1,5 | 1 | 1 | 11 |
| 3.1.2.I.8 | 5,3/7 | 1,75 | 2 | 2 | 7 |
| 3.1.3.I.11 | 4,5/6 | 1,5 | 3 | 3 | 7 |
| 3.1.4.I.16 | 5,3/7 | 1,75 | 2 | 2 | 2 |

Si se acogen, la Unidad 2 sube 2 puntos y la Unidad 3 pasa de 93,5 a 100.


**4. 2.1.4.G.14 · 3/5**

> Comentario: "Hay validación de entradas en el menú y 86 consultas parametrizadas, pero las validaciones viven en la capa de interfaz y no en el dominio: un objeto construido por código puede quedar en estado inválido."
>
> Observaciones: "Las validaciones residen en la capa de interfaz y no en el dominio. Un objeto construido desde otro punto del código puede quedar en estado inválido y la base de datos lo acepta. La regla es que cada clase defienda su propio estado y no delegue esa responsabilidad en el menú."

**A1. "Las validaciones viven en la capa de interfaz y no en el dominio."**

- *Evidencia:* las reglas del negocio están en los constructores: **"Persona"** valida nombre, dirección, teléfono y correo ([ecotech.py L221-225](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L221-L225), [ecotech.py L233-240](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L233-L240)); **"Empleado"**, salario y fecha de contrato ([ecotech.py L265-270](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L265-L270)); **"Departamento"**, **"Proyecto"**, **"RegistroTiempo"**, **"RegistroClima"**, **"TipoCambio"** y **"Usuario"** también validan en su constructor.
- *Qué hace el menú:* sus funciones **"pedir_*"** solo revisan el formato de lo que se teclea, que sea un número o una fecha legible ([main.py L112](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L112), [main.py L120](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L120), [main.py L131](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L131), [main.py L139](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L139)). Su **"except ValueError"** no valida: atrapa el error que lanzó la clase y lo muestra ([main.py L615-616](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L615-L616)).
- *Contraejemplo buscado:* métodos que cambien el estado sin validar. Los que modifican datos ya creados (**"actualizar_contacto"**, **"renombrar"**, **"cambiar_clave"**) vuelven a validar ([ecotech.py L230-231](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L230-L231), [ecotech.py L478-481](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L478-L481), [ecotech.py L907-909](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L907-L909)).
- *Veredicto:* no se sostiene.

**A2. "Un objeto construido por código puede quedar en estado inválido."**

- *Evidencia:* con datos inválidos el constructor lanza **"ValueError"** ([ecotech.py L236-238](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L236-L238), [ecotech.py L266-269](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L266-L269)) y el objeto no llega a existir. La autoverificación del propio código ya lo probaba sin menú ([ecotech.py L1082-1091](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L1082-L1091)).
- *Reproducción:* siete objetos inválidos creados por código, sin menú; los siete lanzan **"ValueError"**. Ver **"2.1.4.G.14"** en [**"SALIDA_APELACION.md"**](SALIDA_APELACION.md).
- *Veredicto:* no se sostiene.

**A3. "La base de datos lo acepta."**

- *Evidencia:* por la clase no llega ningún objeto inválido (A2). Aun saltándose la clase, la base rechaza los rangos críticos con **"CHECK"**: salario, horas, moneda, rol y datos de clima ([ecotech.py L97](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L97), [ecotech.py L107](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L107), [ecotech.py L119](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L119), [ecotech.py L131](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L131), [ecotech.py L142-151](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L142-L151)).
- *Reproducción:* un **"INSERT"** directo con salario 0 es rechazado por la base.
- *Veredicto:* no se sostiene.

**Sobre el texto del indicador:** pide validar las entradas y gestionar los errores sin que el sistema se interrumpa. No pide que la validación esté en el dominio. Se cumple lo que pide y, además, lo que pide el comentario.


**5. 3.1.2.I.6 · 4,5/6**

> Comentario: "Valida las credenciales y las entradas del menú, pero sin saneamiento explícito de los parámetros que viajan a las APIs."

**A1. "Sin saneamiento explícito de los parámetros que viajan a las APIs."**

Todos los parámetros que salen a la red pasan por **"servicios.py"**, y toda salida a la red pasa por un único **"requests.get"** ([servicios.py L200](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L200)). Parámetro por parámetro:

| Parámetro | Saneamiento | Dónde |
|---|---|---|
| Ciudad | **"strip()"**, de 2 a 80 caracteres, solo letras, espacio, guion, punto o apóstrofo (lista blanca por expresión regular) | [servicios.py L28](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L28), [servicios.py L232-234](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L232-L234), [servicios.py L109-112](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L109-L112) |
| Ciudad, al viajar | Va en **"params"**: **"requests"** la codifica en la URL, no se concatena a mano | [servicios.py L117-118](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L117-L118) |
| Latitud y longitud | Vienen de la primera API y se revisa el rango antes de mandarlas a la segunda | [servicios.py L123-125](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L123-L125) |
| Moneda | Lista cerrada; el texto del usuario no viaja, viaja un código fijo | [servicios.py L92](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L92), [servicios.py L158-162](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L158-L162) |
| URL y tiempo de espera (del **".env"**) | Solo **"https"**; tiempo de 0 a 60 segundos | [servicios.py L196-198](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L196-L198) |
| Ciudad guardada en el proyecto | **"texto()"** en el constructor de **"Proyecto"**: segundo filtro | [ecotech.py L520](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L520) |

- *Reproducción:* cinco ciudades maliciosas o fuera de formato (etiqueta HTML, inyección, escape de terminal, 81 letras, números) se rechazan antes de la red; la ciudad viaja limpia; una moneda inventada no llega a la red; lo que el usuario escribe como moneda no viaja; una latitud imposible no pasa a la segunda API; una URL **"http"** en el **".env"** se rechaza sin conectarse. Ver **"3.1.2.I.6"** en la salida.
- *Contraejemplo buscado:* alguna llamada a la red que no pase por **"__consultar"**, o algún parámetro sin filtro. No hay: las tres consultas ([servicios.py L117](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L117), [servicios.py L126](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L126), [servicios.py L164](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L164)) usan datos ya filtrados.
- *Veredicto:* no se sostiene.


**6. 3.1.2.I.8 · 5,3/7**

> Observaciones: "El consumo de las APIs no restringe por rol ni por sesión."

**A1. "No restringe por rol."**

- *Evidencia:* el menú llama a las APIs en tres lugares ([main.py L333](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L333), [main.py L360](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L360), [main.py L501](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L501)), que corresponden a las opciones 11, 12 y 21. Las tres exigen permiso ([main.py L63-69](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L63-L69)), el permiso depende del rol ([ecotech.py L855-860](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L855-L860)) y **"autorizar()"** lo revisa antes de ejecutar la opción ([main.py L575-576](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L575-L576)). Guardar lo que llega de la API exige permiso dentro de las clases ([ecotech.py L713](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L713), [ecotech.py L800](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L800)).
- *Reproducción:* un EMPLEADO en las opciones 11 y 21 y un GERENTE en la 12 reciben **"PermissionError"**; no se les pide ningún dato y la API se llama 0 veces. Guardar un registro de clima o un tipo de cambio sin permiso es rechazado por la clase.
- *Veredicto:* no se sostiene.

**A2. "Ni por sesión."**

- *Evidencia:* sin credenciales válidas no se llega al menú ([main.py L704](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L704)), y la sesión se cierra a los 10 minutos sin actividad ([main.py L71](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L71), [main.py L681](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L681)).
- *Reproducción:* una clave equivocada no entrega usuario; la correcta sí. El cierre por inactividad no se simula en la prueba (necesitaría manipular el reloj); se acredita con el código citado.
- *Veredicto:* no se sostiene.

**Sobre el texto del indicador:** pide "controles seguros de flujo y sesión". El control de flujo es literalmente lo que hace el código, y así lo dice su comentario: "el permiso se revisa antes de pedir un solo dato" ([main.py L61-62](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L61-L62)).


**7. 3.1.3.I.11 · 4,5/6**

> Comentario: "Usa status_code en tres puntos, pero no distingue 404 de 500 ni informa el código al usuario."
>
> Observaciones: "status_code se emplea sin distinguir el estado recibido."

**A1. "No distingue 404 de 500."** 400, 404 y 429 tienen mensaje propio ([servicios.py L53-57](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L53-L57)); 500 o más van por otra rama ([servicios.py L216-219](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L216-L219)). *Veredicto:* no se sostiene.

**A2. "No informa el código al usuario."** Todos los mensajes de error llevan el código, incluido uno genérico para cualquier otro ([servicios.py L218](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L218), [servicios.py L220-221](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L220-L221)), y el menú los muestra ([main.py L613-614](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L613-L614)). *Veredicto:* no se sostiene.

**A3. "status_code se emplea sin distinguir el estado recibido."** El código se lee una vez ([servicios.py L214](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L214)) y se decide por él antes de leer el cuerpo. Las otras dos apariciones de **"status_code"** en el archivo ([servicios.py L263](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L263), [servicios.py L322](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L322)) son respuestas simuladas de la autoverificación. *Veredicto:* no se sostiene.

- *Reproducción:* 400, 404, 429, 500, 503 y 418 simulados; cada uno con su código en el mensaje, y 400, 404, 429 y 500 con cuatro mensajes distintos.
- *Sobre el texto del indicador:* pide validar y gestionar los códigos. Comunicar el error al usuario es la I.12 ("comunica errores de forma segura"), evaluada con 7/7.


**8. 3.1.4.I.16 · 5,3/7**

> Comentario: "La refactorización está documentada y justificada, pero no se declara ningún fragmento descartado: solo adoptados y corregidos."
>
> Observaciones: "El documento de uso de inteligencia artificial registra fragmentos adoptados y corregidos, pero ninguno descartado. El indicador 3.1.4.I.16 valora también la decisión de descartar."

**A1. "No se declara ningún fragmento descartado."**

**"docs/ANALISIS_IA.md"** tiene 16 filas con la decisión **Descartar**, cada una con su fundamento técnico.

| Unidad | Filas | Dónde |
|---|---|---|
| 3 | 27, 40, 41, 45, 56, 61 | tabla desde la [sección 4](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L109) |
| 2 | 5, 6, 8, 9, 10, 15, 16, 18, 20, 24 | tabla de la sección 1; la [línea 14](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L14) dice "diez se descartaron" |

Las cuatro de código de la Unidad 3: fila 27, validar por **"Content-Type"** ([ANALISIS_IA.md L114](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L114)); fila 40, llave de API sin uso ([ANALISIS_IA.md L127](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L127)); fila 41, getters fuera del UML ([ANALISIS_IA.md L128](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L128)); fila 61, **"python-dotenv"** ([ANALISIS_IA.md L216](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L216)).

- *Reproducción:* la prueba cuenta las filas **Descartar** de cada unidad directamente en el documento.
- *Veredicto:* no se sostiene.

**A2. "El indicador valora también la decisión de descartar."**

- El texto del indicador en la hoja es "Refactoriza el código generado por IA y justifica técnicamente las decisiones adoptadas". El de la rúbrica publicada (3.1.4.G.21) dice lo mismo. Ninguno menciona descartar.
- Descartar se evalúa en el 2.1.5.G.18 de la Unidad 2 ("Modifica, adapta o descarta…"), calificado con 5/5 y el comentario "La auditoría deja registro de qué se modificó y por qué, con la decisión técnica declarada en cada caso".
- Aun si el indicador lo exigiera, A1 muestra que está hecho.


**9. Límites: lo que no se afirma**

Una auditoría también dice dónde termina. Ninguno de estos puntos hace cierta una afirmación de la corrección, pero se declaran:

1. **G.14.** El constructor de **"Empleado"** revisa el rango del salario, no su tipo: un valor booleano pasaría como 1, que está dentro del rango permitido. Los **"CHECK"** de la base cubren rangos numéricos y listas cerradas, no el formato del correo ni del teléfono; esos los valida la clase.
2. **I.8.** El permiso para consultar la API se revisa en el flujo del programa (antes de ejecutar la opción), no dentro de **"ServicioExterno"**. Son datos públicos, sin llave; lo que se protege dentro de las clases es guardarlos. El cierre de sesión por inactividad no está cubierto por la prueba automática.
3. **I.11.** Cuando la API falla pero hay un dato anterior, el programa muestra un aviso y ese dato, no el código de error: prioriza la continuidad. Ese comportamiento es el que se premió en la I.12.
4. **I.16.** De las seis filas descartadas de la Unidad 3, la 45 (un conteo del diagrama) y la 56 (un comentario para SonarCloud) no son código de la aplicación; las de código son 27, 40, 41 y 61. La hoja usa cinco niveles cuya descripción no se conoce; se razona sobre el texto del indicador.


**10. Cómo reproducirlo**

```bash
git clone https://github.com/leonardoguerrerodev/poo-ecotech.git
cd poo-ecotech
pip install -r requirements.txt
python3 apelacion/prueba_apelacion.py
```

La prueba comprueba primero con git que los archivos citados son los del commit evaluado. Sin internet funciona igual: las APIs se simulan. Las ejecuciones en GitHub están en [Actions](https://github.com/leonardoguerrerodev/poo-ecotech/actions/workflows/apelacion.yml).
