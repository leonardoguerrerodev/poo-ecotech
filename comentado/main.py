"""EcoTech Solutions — menú de terminal.

Ejecuta el ciclo CRUD completo sobre las dos clases relacionadas del modelo:
`Departamento` y `Empleado`. No contiene ninguna sentencia SQL: toda la
persistencia vive en los métodos de las clases de `ecotech.py`.

    python3 main.py
"""

# QUÉ HACE ESTE ARCHIVO: dibujar el menú, leer lo que teclea el usuario y
# traducirlo a llamadas de método. Ni una sentencia SQL. Esa frontera es la
# que se defiende: si la interfaz fuera web, `ecotech.py` no cambia.
#
# POR QUÉ EMPLEADO Y DEPARTAMENTO: son las dos clases relacionadas que pide
# la evaluación, y su relación es la más ilustrativa, una agregación 1..N
# donde borrar el todo no borra las partes. La opción 4 lo demuestra en vivo.

import sqlite3
from datetime import date

# Importación selectiva y no `import *`: con asterisco entran también
# `sqlite3`, `re` y todo lo que ese módulo importó, y se pierde de vista de
# dónde sale cada nombre.
from ecotech import Departamento, Empleado, Rol, Usuario, crear_tablas

MENU = """
==================================================================
   EcoTech Solutions — Gestión de empleados
==================================================================
   DEPARTAMENTOS                EMPLEADOS
    1. Crear                     5. Contratar
    2. Listar                    6. Listar
    3. Renombrar                 7. Actualizar contacto
    4. Eliminar                  8. Eliminar
                                 9. Asignar a departamento
    s. Cargar datos de ejemplo   0. Salir
=================================================================="""

# Techo de todo entero tecleado, salido de la auditoría: SQLite guarda enteros
# de 64 bits y uno mayor lanza OverflowError al convertirlo. Un id de 25
# dígitos tumbaba el menú por seis caminos (las opciones 3, 4, 7, 8, 9 con el
# id y la 5 con el salario), y los seis cruzan por `pedir_entero`.
MAXIMO_ENTERO = 10**9


# --- Entrada validada del usuario ------------------------------------
# Reintentan hasta recibir algo usable, así el programa no avanza con un dato
# que las clases vayan a rechazar por formato.
#
# LAS DOS CAPAS NO SE PISAN: aquí se valida el FORMATO (que sea número, que
# sea fecha); en las clases, la REGLA DE NEGOCIO (salario positivo, contrato
# no futuro). Esta se salta llamando a la clase desde otro programa, la de
# allá no; por eso allá manda, y esta solo evita excepciones por un dedazo.

def pedir_texto(mensaje: str) -> str:
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("   ! No puede quedar vacío.")


# `isdecimal()` y no `int()`: rechaza el signo menos, y ningún campo que usa
# admite negativos. Y no `isdigit()`, que es lo que había antes:
# `"²".isdigit()` es True pero `int("²")` falla. `isdecimal()` acepta
# exactamente lo que `int()` sabe convertir.
def pedir_entero(mensaje: str) -> int:
    while True:
        valor = input(mensaje).strip()
        if not valor.isdecimal():
            print("   ! Escriba un número entero, sin puntos ni letras.")
        elif int(valor) > MAXIMO_ENTERO:
            print(f"   ! Demasiado grande. El máximo es {MAXIMO_ENTERO}.")
        else:
            return int(valor)


# `date.fromisoformat` valida el formato y el calendario: rechaza "2024-13-45",
# que un `split("-")` a mano aceptaría.
def pedir_fecha(mensaje: str) -> date:
    while True:
        try:
            return date.fromisoformat(input(mensaje).strip())
        except ValueError:
            print("   ! Formato de fecha: AAAA-MM-DD, por ejemplo 2024-03-01.")


# Recibe la clase, no una instancia: sirve igual para `Empleado` y
# `Departamento` porque las dos exponen el mismo `buscar()`, y una firma
# común evita escribir esto dos veces.
def buscar_o_avisar(clase, id: int):
    objeto = clase.buscar(id)
    if objeto is None:
        print(f"   ! No existe {clase.__name__.lower()} con id {id}.")
    return objeto


# --- Lecturas ---------------------------------------------------------
# La lista vacía se avisa: una pantalla en blanco deja al usuario sin saber
# si no hay datos o si el programa falló.

def listar_departamentos() -> None:
    departamentos = Departamento.listar()
    if not departamentos:
        print("   (no hay departamentos)")
    for departamento in departamentos:
        # El conteo sale de un COUNT(*) y no del largo de la lista en memoria:
        # la fuente de verdad de la relación es la clave foránea.
        total = departamento.contar_empleados()
        print(f"   [{departamento.obtener_id()}] "
              f"{departamento.obtener_nombre()} · "
              f"{total} empleado{'s' if total != 1 else ''}")


# Muestra `obtener_resumen()`, que no incluye el salario: listar la dotación
# no puede filtrar remuneraciones.
def listar_empleados() -> None:
    empleados = Empleado.listar()
    if not empleados:
        print("   (no hay empleados)")
    for empleado in empleados:
        print(f"   [{empleado.obtener_id()}] {empleado.obtener_resumen()}")


# --- Datos de ejemplo -------------------------------------------------
# Datos que parecen reales y no "test1": sirven para cargar el sistema en un
# segundo durante la defensa y para probar la normalización del teléfono con
# entradas escritas como las escribiría una persona.

PLANTILLA = [
    ("Juanita Bravo Sepúlveda", "Av. Matta 1234, Santiago",
     "+56 9 8765 4321", "jbravo@ecotech.cl", date(2023, 4, 17), 1450000,
     "Desarrollo Sostenible"),
    ("Ignacio Fuentes Cárdenas", "Los Carrera 890, Valparaíso",
     "+56 9 6543 2109", "ifuentes@ecotech.cl", date(2022, 11, 2), 1980000,
     "Desarrollo Sostenible"),
    ("Camila Reyes Ortiz", "Pedro de Valdivia 55, Providencia",
     "+56 9 7412 8536", "creyes@ecotech.cl", date(2024, 1, 8), 1260000,
     "Investigación y Desarrollo"),
]


def sembrar(solicitante: Usuario) -> None:
    """La C del ciclo, con datos que parecen reales."""
    # El diccionario guarda el id que devolvió cada INSERT para poder enlazar
    # después a cada empleado con su departamento: la clave foránea en la
    # práctica.
    departamentos = {
        nombre: Departamento(nombre).guardar(solicitante)
        for nombre in ("Desarrollo Sostenible", "Investigación y Desarrollo")
    }
    for nombre, direccion, telefono, correo, contrato, salario, dep in PLANTILLA:
        empleado = Empleado(nombre, direccion, telefono, correo,
                            contrato, salario)
        empleado.guardar(solicitante)
        empleado.asignar_departamento(departamentos[dep], solicitante)
    # Correrlo dos veces choca contra el UNIQUE del correo y levanta
    # IntegrityError, que el bucle principal atrapa. No es descuido: es la
    # demostración más simple de que el menú sobrevive a un error de base.
    print(f"   Cargados {len(departamentos)} departamentos "
          f"y {len(PLANTILLA)} empleados.")


# --- Despacho ---------------------------------------------------------
# Cadena de `if/elif` y no un diccionario de funciones: cada opción pide datos
# distintos, y un despacho por tabla obligaría a uniformar firmas que no se
# parecen. Aburrido y legible le gana a ingenioso.

def ejecutar(opcion: str, solicitante: Usuario) -> None:
    if opcion == "1":
        # C — construir ya valida: si el nombre no sirve, no se toca la base.
        departamento = Departamento(pedir_texto("   Nombre: "))
        print("   Departamento creado con id "
              f"{departamento.guardar(solicitante)}.")

    elif opcion == "2":
        # R
        listar_departamentos()

    elif opcion == "3":
        # U — se busca primero para confirmar que existe: un UPDATE sobre un
        # id inexistente no da error, solo afecta cero filas.
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        # Cortocircuito: si es None, no se pide el nombre nuevo ni se renombra.
        if departamento and departamento.renombrar(
                pedir_texto("   Nuevo nombre: "), solicitante):
            print(f"   Ahora se llama {departamento.obtener_nombre()}.")

    elif opcion == "4":
        # D — la operación que demuestra la agregación, y el mensaje lo dice
        # en voz alta porque es el punto que hay que defender.
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        if departamento and departamento.eliminar(solicitante):
            print("   Departamento eliminado. Sus empleados siguen vigentes, "
                  "sin departamento: la agregación es ON DELETE SET NULL.")

    elif opcion == "5":
        # C — los seis campos llegan al constructor con el tipo correcto; lo
        # que el constructor juzga es la regla de negocio.
        empleado = Empleado(pedir_texto("   Nombre completo: "),
                            pedir_texto("   Dirección: "),
                            pedir_texto("   Teléfono: "),
                            pedir_texto("   Correo: "),
                            pedir_fecha("   Inicio de contrato (AAAA-MM-DD): "),
                            pedir_entero("   Salario: "))
        print(f"   Empleado contratado con id {empleado.guardar(solicitante)}.")

    elif opcion == "6":
        # R
        listar_empleados()

    elif opcion == "7":
        # U — imprime el resumen después de actualizar para que el usuario vea
        # el teléfono ya normalizado: escribe "22 987 6543", sale "229876543".
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado:
            empleado.actualizar_contacto(pedir_texto("   Nuevo teléfono: "),
                                         pedir_texto("   Nuevo correo: "))
            print(f"   {empleado.obtener_resumen()}")

    elif opcion == "8":
        # D
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado and empleado.eliminar(solicitante):
            print("   Empleado eliminado, junto con sus registros de tiempo.")

    elif opcion == "9":
        # U — el `return` temprano evita pedir el segundo id cuando el primero
        # ya falló. Anidar dos `if` daría lo mismo pero se lee peor.
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado is None:
            return
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        if departamento and empleado.asignar_departamento(
                departamento.obtener_id(), solicitante):
            print(f"   {empleado.obtener_nombre()} quedó en "
                  f"{departamento.obtener_nombre()}.")

    elif opcion == "s":
        sembrar(solicitante)

    else:
        print("   ! Opción desconocida.")


def main() -> None:
    # Este try va aparte del bucle: si la base no se puede ni preparar
    # (carpeta sin permiso, disco lleno), no tiene sentido mostrar un menú que
    # no va a funcionar. Es el único error del que el programa no se recupera.
    try:
        crear_tablas()
    except sqlite3.Error as error:
        print(f"   ! No se pudo preparar la base de datos: {error}")
        return

    # Solicitante fijo, simplificación consciente: el login es de la Unidad 3.
    # `Usuario` ya tiene scrypt, roles y permisos; falta la pantalla que
    # pregunte quién es. Va como ADMIN_RRHH porque el menú administra
    # empleados, que es el módulo protegido.
    solicitante = Usuario("rrhh.admin", "Clave-RRHH-2026", Rol.ADMIN_RRHH)
    print(MENU)

    # EL BUCLE QUE NO SE CAE: el try va DENTRO del while. Afuera, la primera
    # excepción termina el programa; adentro, se imprime el motivo y la
    # siguiente vuelta pide otra opción. Es el requisito de "evitar que el
    # sistema se interrumpa ante errores de ejecución".
    while True:
        try:
            opcion = input("\n   Opción (m = menú): ").strip().lower()
            if opcion == "0":
                print("   Hasta luego.")
                return
            if opcion == "m":
                print(MENU)
                continue
            ejecutar(opcion, solicitante)

        # Los except van de más específico a más general porque Python entra
        # al primero que coincida: `IntegrityError` y `OperationalError` son
        # subclases de `sqlite3.Error` y después del genérico nunca correrían.

        # Una restricción de la base rechazó el dato (el UNIQUE del correo, un
        # CHECK). Es el error más frecuente en uso normal, de ahí el mensaje
        # propio.
        except sqlite3.IntegrityError:
            print("   ! Ese correo ya está registrado. Use otro.")

        # El archivo de la base no está disponible: borrado, sin permisos,
        # bloqueado, disco lleno. Aquí sí conviene mostrar el texto del error,
        # porque el usuario tiene que actuar sobre el sistema de archivos.
        except sqlite3.OperationalError as error:
            print(f"   ! No se pudo acceder a la base de datos: {error}")

        # Red para cualquier otro fallo de SQLite. "No se guardó nada" es
        # cierto: el `with con:` de `conectar()` hizo ROLLBACK. Se oculta el
        # detalle técnico para no filtrar la estructura de la base.
        except sqlite3.Error:
            print("   ! La base rechazó la operación. No se guardó nada.")

        # El rol no alcanza. Se distingue de ValueError porque el usuario no
        # tiene que corregir el dato: tiene que pedir permiso.
        except PermissionError as error:
            print(f"   ! {error}")

        # Una regla de negocio rechazó el dato. El mensaje viene de la clase
        # que lo rechazó y ya nombra el campo, por eso se imprime tal cual.
        except ValueError as error:
            print(f"   ! {error}")

        # Ctrl-C y fin de la entrada no son errores, son formas legítimas de
        # terminar. Sin esto, Ctrl-C escupiría un traceback en pantalla.
        except (KeyboardInterrupt, EOFError):
            print("\n   Interrumpido. Hasta luego.")
            return

        # ÚLTIMO RECURSO. Lo malo es `except: pass`, que traga el error sin
        # rastro; este nombra el tipo y vuelve al menú, así que "no se
        # interrumpe" vale para todos los errores y no solo los previstos.
        # `Exception` no cubre KeyboardInterrupt ni SystemExit.
        except Exception as error:
            print(f"   ! Error inesperado ({type(error).__name__}): {error}")


# Permite importar este módulo sin que arranque el menú.
if __name__ == "__main__":
    main()
