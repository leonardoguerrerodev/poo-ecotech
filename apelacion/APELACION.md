**Revisión de puntaje ES2 · Leonardo Guerrero · commit "36f94ac" (23-09)**

Cinco descuentos no coinciden con el código entregado: 2 puntos en la Unidad 2 y 6,5 en la Unidad 3. En cada uno va el texto del indicador, su comentario y la respuesta a cada afirmación. Los enlaces abren las líneas en el [commit evaluado](https://github.com/leonardoguerrerodev/poo-ecotech/tree/36f94ac5b6292a9c20a2957217c5226a90ca4eb9).

[![Prueba de la apelación](https://github.com/leonardoguerrerodev/poo-ecotech/actions/workflows/apelacion.yml/badge.svg)](https://github.com/leonardoguerrerodev/poo-ecotech/actions/workflows/apelacion.yml)

**Prueba:** [**"prueba_apelacion.py"**](prueba_apelacion.py) intenta hacer lo que dice cada comentario y muestra lo que pasa. Su salida real está en [**"SALIDA_APELACION.md"**](SALIDA_APELACION.md), y GitHub la vuelve a correr sola en cada push, después de comprobar que el código es idéntico al del commit evaluado (el sello de arriba). Para revisarlo a fondo (método, cada afirmación por separado, contraejemplos buscados y límites) está [**"AUDITORIA_APELACION.md"**](AUDITORIA_APELACION.md).

**1. 2.1.4.G.14 · 3/5**

> Indicador: "Valida las entradas de datos del usuario y gestiona adecuadamente los errores detectados, evitando interrupciones en el funcionamiento del sistema."
>
> Su comentario: "Hay validación de entradas en el menú y 86 consultas parametrizadas, pero las validaciones viven en la capa de interfaz y no en el dominio: un objeto construido por código puede quedar en estado inválido."
>
> Observaciones: "Las validaciones residen en la capa de interfaz y no en el dominio. Un objeto construido desde otro punto del código puede quedar en estado inválido y la base de datos lo acepta. La regla es que cada clase defienda su propio estado y no delegue esa responsabilidad en el menú."

- **No viven en la interfaz:** están en el constructor de cada clase, como **"Persona"** ([ecotech.py L221-225](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L221-L225)) y **"Empleado"** ([ecotech.py L265-270](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L265-L270)). El menú solo revisa el formato (que sea un número, que la fecha se lea).
- **Un objeto con datos inválidos no se crea por código:** con teléfono, correo o nombre inválidos, salario fuera de rango o contrato con fecha futura, la clase lanza **"ValueError"** ([ecotech.py L236-238](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L236-L238), [ecotech.py L266-269](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L266-L269)) y el objeto no existe. La autoverificación lo prueba sin menú ([ecotech.py L1082-1087](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L1082-L1087)).
- **La base rechaza los rangos críticos:** salario, horas, moneda, rol y datos de clima tienen **"CHECK"** ([ecotech.py L97](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L97), [ecotech.py L119](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L119), [ecotech.py L142-146](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L142-L146)).
- **El indicador no pide que la validación esté en el dominio:** pide validar las entradas y gestionar los errores sin que el sistema se caiga. Eso se cumple, y además la validación está en las clases.

**2. 3.1.2.I.6 · 4,5/6**

> Indicador: "Valida y sanea credenciales y entradas de usuario utilizadas en consultas API."
>
> Su comentario: "Valida las credenciales y las entradas del menú, pero sin saneamiento explícito de los parámetros que viajan a las APIs."

- **La ciudad se sanea antes de viajar:** se le quitan los espacios de los bordes, debe tener de 2 a 80 caracteres y solo letras, espacio, guion, punto o apóstrofo ([servicios.py L28](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L28), [servicios.py L232-234](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L232-L234)). Si no cumple, **"ValueError"** y la API no se consulta ([servicios.py L109-112](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L109-L112)). Viaja en **"params"**, que **"requests"** codifica ([servicios.py L117-118](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L117-L118)).
- **La moneda escrita por el usuario nunca viaja:** se busca en una lista cerrada y a la API va un código fijo, "dolar", "euro" o "uf" ([servicios.py L92](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L92), [servicios.py L158-162](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L158-L162)).
- **Lo que viaja de una API a otra también se revisa:** latitud y longitud se validan en rango antes de mandarlas ([servicios.py L123-125](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L123-L125)).
- **La configuración del ".env" se revisa:** solo **"https"** y tiempo de espera de 0 a 60 segundos ([servicios.py L196-198](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L196-L198)).
- **Y la ciudad ya se validó antes, en la clase "Proyecto"** ([ecotech.py L520](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L520)): pasa por dos filtros.

**3. 3.1.2.I.8 · 5,3/7**

> Indicador (rúbrica publicada): "restringiendo además el acceso al consumo de APIs mediante controles seguros de flujo y sesión."
>
> Observaciones: "El consumo de las APIs no restringe por rol ni por sesión."

- **Control de flujo:** el permiso se revisa antes de pedir un solo dato, como dice el propio comentario del código ([main.py L61-62](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L61-L62)), y **"autorizar()"** lo comprueba antes de ejecutar la opción ([main.py L575-576](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L575-L576)).
- **Sí restringe por sesión:** sin login no se llega al menú ([main.py L704](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L704)), y la sesión se cierra a los 10 minutos sin actividad ([main.py L681](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L681)).
- **Sí restringe por rol:** cada opción de API exige un permiso ([main.py L63-69](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L63-L69)) que depende del rol ([ecotech.py L855-860](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L855-L860)). Un EMPLEADO no puede usar la 11 ni la 21, y un GERENTE no puede usar la 12.
- **Lo que llega de la API se guarda con permiso dentro de las clases:** **"RegistroClima.guardar()"** y **"TipoCambio.guardar()"** llaman a **"autorizar()"** ([ecotech.py L713](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L713), [ecotech.py L800](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L800)).

**4. 3.1.3.I.11 · 4,5/6**

> Indicador: "Valida y gestiona los códigos de respuesta HTTP devueltos por la API."
>
> Su comentario: "Usa status_code en tres puntos, pero no distingue 404 de 500 ni informa el código al usuario."
>
> Observaciones: "status_code se emplea sin distinguir el estado recibido."

- **Sí distingue 404 de 500:** 400, 404 y 429 tienen mensaje propio ([servicios.py L53-57](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L53-L57)) y los 500 van por otra rama ([servicios.py L216-219](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L216-L219)).
- **Los mensajes de error muestran el código:** "(404)", "falla interna (500)" y, para cualquier otro, "Respuesta inesperada (código)" ([servicios.py L218](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L218), [servicios.py L220-221](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L220-L221)).
- **Comunicar el error al usuario es la I.12:** "Garantiza continuidad operativa y comunica errores de forma segura", donde puso 7/7.

**5. 3.1.4.I.16 · 5,3/7**

> Indicador: "Refactoriza el código generado por IA y justifica técnicamente las decisiones adoptadas."
>
> Su comentario: "La refactorización está documentada y justificada, pero no se declara ningún fragmento descartado: solo adoptados y corregidos."
>
> Observaciones: "El documento de uso de inteligencia artificial registra fragmentos adoptados y corregidos, pero ninguno descartado. El indicador 3.1.4.I.16 valora también la decisión de descartar."

- **Sí hay fragmentos descartados en la Unidad 3**, en **"docs/ANALISIS_IA.md"**, cada uno con su razón técnica:
  - fila 27 ([ANALISIS_IA.md L114](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L114)): validar por **"Content-Type"**; mindicador.cl manda el euro como **"text/html"** aunque es JSON válido, así que habría rechazado datos correctos.
  - fila 40 ([ANALISIS_IA.md L127](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L127)): leer una llave de API; ninguna de las dos APIs la pide, y código para una llave que no existe no se puede probar.
  - fila 41 ([ANALISIS_IA.md L128](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L128)): getters para mostrar la sesión; no están en el UML y el menú ya tiene el dato.
  - fila 61 ([ANALISIS_IA.md L216](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L216)): instalar **"python-dotenv"**; diez líneas de biblioteca estándar hacen lo mismo sin sumar una dependencia.
- **Y diez más en la Unidad 2** ([ANALISIS_IA.md L14](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L14): "diez se descartaron").
- **El indicador no menciona descartar:** su texto es "Refactoriza el código generado por IA y justifica técnicamente las decisiones adoptadas", igual que en la rúbrica publicada.
- **"Descartar" se evalúa en la Unidad 2, y ahí puso 5/5:** el 2.1.5.G.18 dice "Modifica, adapta **o descarta** el código generado por IA en función de los requerimientos de la solución, justificando técnicamente las decisiones adoptadas", y su comentario fue "La auditoría deja registro de qué se modificó y por qué, con la decisión técnica declarada en cada caso". El mismo criterio ya se evaluó con nota máxima.

<details>
<summary><b>Ver el código citado, con explicación</b></summary>

**1. 2.1.4.G.14 (3/5), validaciones en el dominio**

> Su comentario: "las validaciones viven en la capa de interfaz y no en el dominio: un objeto construido por código puede quedar en estado inválido".

**"Persona"** pasa el nombre y la dirección por **"texto()"**, que rechaza textos vacíos, muy largos o con caracteres de control. El teléfono y el correo se revisan en **"__fijar_contacto()"**. Si algo falla, tira **"ValueError"** y el objeto no se crea (**"ecotech.py"**, [líneas 221-225](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L221-L225), sin los comentarios):

```python
self.__nombre = texto(nombre, "El nombre")
self.__direccion = texto(direccion, "La dirección", 200)
self.__fijar_contacto(telefono, correo)
```

**"Empleado"** no se deja crear con un salario fuera de rango ni con un contrato con fecha futura ([líneas 265-270](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L265-L270)):

```python
if not 0 < salario <= SALARIO_MAXIMO:
    raise ValueError(f"Salario fuera de rango (1 a {SALARIO_MAXIMO}): "
                     f"{salario}")
if fecha_inicio_contrato > date.today():
    raise ValueError("Contrato con fecha futura: "
                     f"{fecha_inicio_contrato.isoformat()}")
```

Y aunque alguien se saltara la clase, la tabla tampoco lo acepta ([línea 97](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L97)):

```python
CHECK (salario > 0 AND salario <= 100000000),
```

Además, la autoverificación prueba justo el caso del comentario: crea empleados inválidos por código, sin pasar por el menú, y revisa que la clase los rechace ([líneas 1082-1087](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/ecotech.py#L1082-L1087)):

```python
# --- Lo que el dominio debe rechazar
assert _rechaza(lambda: Empleado("J", calle, "123", correo,
                                 contrato, 1000)), "teléfono corto"
assert _rechaza(lambda: Empleado("J", calle, "229876543", correo,
                                 contrato, 0)), "salario cero"
```

**2. 3.1.2.I.6 (4,5/6), saneamiento de lo que viaja a las APIs**

> Su comentario: "Valida las credenciales y las entradas del menú, pero sin saneamiento explícito de los parámetros que viajan a las APIs".

El saneamiento está en **"servicios.py"**, no en el menú, y se hace antes de que el dato salga a la red.

La ciudad solo puede tener letras, espacios, guion, punto o apóstrofo ([servicios.py L28](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L28)):

```python
PATRON_CIUDAD = re.compile(r"[^\W\d_]+(?:[ '.-][^\W\d_]+)*")
```

**"_validar_ciudad()"** le quita los espacios de los bordes, exige de 2 a 80 caracteres y que calce entera con ese patrón ([servicios.py L232-234](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L232-L234)):

```python
def _validar_ciudad(self, ciudad: str) -> bool:
    limpia = ciudad.strip()
    return 2 <= len(limpia) <= 80 and bool(PATRON_CIUDAD.fullmatch(limpia))
```

Si no pasa, lanza **"ValueError"** y la API no se consulta. Si pasa, viaja ya limpia ([servicios.py L109-112](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L109-L112)) y dentro de **"params"**, que **"requests"** codifica en la URL ([servicios.py L117-118](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L117-L118)):

```python
if not self._validar_ciudad(ciudad):
    raise ValueError("Ciudad inválida: de 2 a 80 letras, con espacios, "
                     "guion, punto o apóstrofo")
ciudad = ciudad.strip()
```

```python
lugares = self.__consultar(self.__url_geocodificacion, {
    "name": ciudad, "count": 1, "language": "es"}).get("results")
```

La latitud y la longitud vienen de la primera API y se revisan antes de mandarlas a la segunda ([servicios.py L123-125](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L123-L125)):

```python
if not (_en_rango(lugar["latitude"], -90, 90)
        and _en_rango(lugar["longitude"], -180, 180)):
    raise ServicioNoDisponible(FORMATO_INESPERADO)
```

Con la moneda, lo que escribe el usuario nunca viaja: se busca en una lista cerrada y a la API va un código fijo ([servicios.py L92](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L92), [servicios.py L158-162](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L158-L162)):

```python
MONEDAS = {"USD": "dolar", "EUR": "euro", "UF": "uf"}
```

```python
codigo = self.MONEDAS.get(moneda.strip().upper())
if codigo is None:
    raise ValueError("Moneda no soportada. Use: "
                     + ", ".join(self.MONEDAS))
url = f"{self.__url_indicadores}/{codigo}"
```

Y la configuración que viene del **".env"** también se revisa: solo **"https"** y un tiempo de espera de 0 a 60 segundos ([servicios.py L196-198](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L196-L198)):

```python
if (not url.startswith("https://") or self.__tiempo_espera is None
        or not 0 < self.__tiempo_espera <= TIEMPO_LECTURA_MAXIMO):
    raise ServicioNoDisponible(CONFIGURACION_INVALIDA)
```

**3. 3.1.2.I.8 (5,3/7), acceso a las APIs**

> Su comentario: "El consumo de las APIs no restringe por rol ni por sesión".

Las opciones que usan las APIs (11 clima, 12 planilla, 21 tipo de cambio) piden sesión y permiso según el rol.

Sin login no se llega al menú. El programa pide usuario y clave, y solo abre la sesión si son correctos (**"main.py"**, [línea 704](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L704)):

```python
seguir = usar_sesion(*iniciar_sesion())
```

Si pasan 10 minutos sin hacer nada, la sesión se cierra y hay que entrar de nuevo ([línea 71](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L71) y [línea 681](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L681)):

```python
INACTIVIDAD_MAXIMA = 10 * 60
if time.monotonic() - ultima_actividad > INACTIVIDAD_MAXIMA:
```

Cada opción tiene el permiso que necesita. Las de API son la 11 (**"proyectos"**), la 12 (**"empleados"**) y la 21 (**"proyectos"**) ([líneas 63-69](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L63-L69)):

```python
PERMISO = {"1": "empleados", "2": "departamentos", "3": "empleados",
           "6": "departamentos", "7": "empleados", "8": "empleados",
           "9": "departamentos", "10": "empleados", "11": "proyectos",
           "12": "empleados", "13": "informes", "14": "usuarios",
           "15": "proyectos", "17": "proyectos", "18": "proyectos",
           "19": "tiempo", "20": "proyectos", "21": "proyectos",
           "24": "proyectos", "25": "proyectos"}
```

Antes de ejecutar la opción, **"autorizar()"** revisa que el rol tenga ese permiso. Si no lo tiene, la opción no corre y la API ni se consulta ([líneas 575-576](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/main.py#L575-L576)):

```python
if opcion in PERMISO:
    autorizar(solicitante, PERMISO[opcion])
```

**4. 3.1.3.I.11 (4,5/6), códigos HTTP**

> Su comentario: "no distingue 404 de 500 ni informa el código al usuario".

Cada código tiene su mensaje y todos le muestran el número al usuario.

400, 404 y 429 tienen un mensaje propio que explica qué pasó (**"servicios.py"**, [líneas 53-57](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L53-L57)):

```python
MENSAJES_HTTP = {
    400: "El servicio externo rechazó la consulta (400).",
    404: "El servicio externo no encontró el recurso pedido (404).",
    429: "Demasiadas consultas al servicio externo: espere un momento (429).",
}
```

Cuando llega la respuesta se lee **"status_code"**. Si es 500 o más, es una falla del servidor y el mensaje lo dice con el código. Si es otro, usa la tabla de arriba, y si no está en la tabla, un mensaje general que igual muestra el código ([líneas 214-220](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/servicios.py#L214-L220)):

```python
estado = respuesta.status_code
if estado != 200:
    if estado >= 500:
        raise ServicioNoDisponible(
            f"El servicio externo tiene una falla interna ({estado}). "
            "Intente más tarde.")
    raise ServicioNoDisponible(MENSAJES_HTTP.get(
        estado, f"Respuesta inesperada del servicio externo ({estado})."))
```

**5. 3.1.4.I.16 (5,3/7), código descartado**

> Su comentario: "no se declara ningún fragmento descartado: solo adoptados y corregidos".

En **"docs/ANALISIS_IA.md"** hay 16 filas marcadas **Descartar**: diez de la Unidad 2 (la [línea 14](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L14) lo resume: "diez se descartaron") y seis de la Unidad 3, en la tabla de la [sección 4](https://github.com/leonardoguerrerodev/poo-ecotech/blob/36f94ac5b6292a9c20a2957217c5226a90ca4eb9/docs/ANALISIS_IA.md?plain=1#L109) en adelante. Las cuatro de código de la Unidad 3:

```
| 27 | Revisar el Content-Type de la respuesta | ... | Descartar | mindicador.cl devuelve el euro con text/html aunque el cuerpo es JSON válido ...
| 40 | Llave de API por variable de entorno | ... | Descartar | Ninguna de las dos APIs la exige y el código para una llave que no existe no se puede probar ...
| 41 | Getters para mostrar la sesión | ... | Descartar | Son los mismos getters descartados en la fila 9, y el diagrama no los tiene ...
| 61 | Lector del .env | ... | Descartar | Diez líneas de biblioteca estándar leen CLAVE=VALOR; una dependencia más es superficie de cadena de suministro ...
```

</details>
