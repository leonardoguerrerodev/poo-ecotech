**Salida de la prueba de la apelación**

Ejecutada el 29-09-2026 con **"python3 apelacion/prueba_apelacion.py"** (Python 3.14.4). La prueba comprueba con git que **"ecotech.py"**, **"main.py"**, **"servicios.py"** y **"docs/ANALISIS_IA.md"** son idénticos a los del commit evaluado **"36f94ac"**. La misma prueba corre en GitHub Actions en cada push: [ver las ejecuciones](https://github.com/leonardoguerrerodev/poo-ecotech/actions/workflows/apelacion.yml).

```
Prueba de la apelación
Código probado: idéntico al commit evaluado 36f94ac

2.1.4.G.14 · "un objeto construido por código puede quedar en estado inválido"
   OK  teléfono '123', sin menú: la clase lanza ValueError (Teléfono inválido: '123') y el objeto no se crea
   OK  correo sin @, sin menú: la clase lanza ValueError (Correo inválido: 'juan.eco.cl') y el objeto no se crea
   OK  nombre vacío, sin menú: la clase lanza ValueError (El nombre no puede estar vacío) y el objeto no se crea
   OK  salario 0, sin menú: la clase lanza ValueError (Salario fuera de rango (1 a 100000000): 0) y el objeto no se crea
   OK  contrato en 2099, sin menú: la clase lanza ValueError (Contrato con fecha futura: 2099-01-01) y el objeto no se crea
   OK  departamento sin nombre, sin menú: la clase lanza ValueError (El nombre del departamento no puede estar vacío) y el objeto no se crea
   OK  proyecto con moneda inventada, sin menú: la clase lanza ValueError (Moneda no soportada. Use: CLP, USD, EUR) y el objeto no se crea

2.1.4.G.14 · "y la base de datos lo acepta"
   OK  INSERT directo con salario 0, sin pasar por la clase: la base lo rechaza (CHECK constraint failed: salario > 0 AND salario <= 100000000)

3.1.2.I.6 · "sin saneamiento explícito de los parámetros que viajan a las APIs"
   OK  ciudad 'Santiago<script>': ValueError antes de la red; la API se llamó 0 veces
   OK  ciudad "'; DROP TABLE x;--": ValueError antes de la red; la API se llamó 0 veces
   OK  ciudad con escape de terminal: ValueError antes de la red; la API se llamó 0 veces
   OK  ciudad de 81 letras: ValueError antes de la red; la API se llamó 0 veces
   OK  ciudad '123': ValueError antes de la red; la API se llamó 0 veces
   OK  ciudad '  Puerto Montt  ': viaja limpia ('Puerto Montt') y dentro de params, que requests codifica
   OK  moneda 'BTC': ValueError antes de la red; la API no se llamó
   OK  moneda ' usd ': lo que escribió el usuario no viaja; a la API va un código fijo (https://mindicador.cl/api/dolar)
   OK  latitud 999 recibida de la primera API: se rechaza y no viaja a la segunda (llamadas: 1)
   OK  URL http en el .env: se rechaza sin conectarse (La configuración del servicio externo no es válida: se ...)
   OK  ciudad vacía en Proyecto: la clase la rechaza antes de guardarla (La ciudad no puede estar vacío)

3.1.2.I.8 · "El consumo de las APIs no restringe por rol"
   OK  opción 11 con rol EMPLEADO: PermissionError (No autorizado para operar sobre proyectos); datos pedidos: 0, llamadas a la API: 0
   OK  opción 21 con rol EMPLEADO: PermissionError (No autorizado para operar sobre proyectos); datos pedidos: 0, llamadas a la API: 0
   OK  opción 12 con rol GERENTE: PermissionError (No autorizado para operar sobre empleados); datos pedidos: 0, llamadas a la API: 0
   OK  RegistroClima.guardar() con rol EMPLEADO: la clase lo rechaza (No autorizado para operar sobre proyectos)
   OK  TipoCambio.guardar() con rol EMPLEADO: la clase lo rechaza (No autorizado para operar sobre proyectos)

3.1.2.I.8 · "ni por sesión"
   OK  login con clave equivocada: autenticar() devuelve None, no hay sesión
   OK  login con la clave correcta: autenticar() entrega el usuario de la sesión
   (que el menú solo se abre con ese usuario y se cierra por inactividad se ve en main.py L704 y L681; no se simula aquí)

3.1.3.I.11 · "no distingue 404 de 500 ni informa el código al usuario"
   OK  respuesta 400: "El servicio externo rechazó la consulta (400)."
   OK  respuesta 404: "El servicio externo no encontró el recurso pedido (404)."
   OK  respuesta 429: "Demasiadas consultas al servicio externo: espere un momento (429)."
   OK  respuesta 500: "El servicio externo tiene una falla interna (500). Intente más tarde."
   OK  respuesta 503: "El servicio externo tiene una falla interna (503). Intente más tarde."
   OK  respuesta 418: "Respuesta inesperada del servicio externo (418)."
   OK  400, 404, 429 y 500 dan cuatro mensajes distintos, y cada uno trae su código

3.1.4.I.16 · "no se declara ningún fragmento descartado"
   OK  Unidad 3: 6 fragmentos marcados Descartar (filas 27, 40, 41, 45, 56, 61)
   OK  Unidad 2: 10 fragmentos marcados Descartar (filas 5, 6, 8, 9, 10, 15, 16, 18, 20, 24)

Las cinco afirmaciones revisadas: en ninguna el código se comporta como dice la corrección.
```
