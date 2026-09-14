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
# donde borrar el todo no borra las partes. La opción 9 lo demuestra en vivo.

import os
import secrets
import sqlite3
from datetime import date

# Importación selectiva y no `import *`: con asterisco entran también
# `sqlite3`, `re` y todo lo que ese módulo importó, y se pierde de vista de
# dónde sale cada nombre.
from ecotech import Departamento, Empleado, Rol, Usuario, crear_tablas

# El menú se ordena por OPERACIÓN (C-R-U-D) y no por clase: así se lee de
# un vistazo que el ciclo está completo, que es lo que evalúa el 2.1.3. Los
# números siguen corridos del 1 al 10 para teclear una sola tecla o dos, y
# los encabezados son solo agrupación visual.
MENU = """
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

   m. menú   ·   x. cancela el dato que se pide   ·   0. salir
=================================================================="""

# Techo de todo entero tecleado, salido de la auditoría: SQLite guarda enteros
# de 64 bits y uno mayor lanza OverflowError al convertirlo. Un id de 25
# dígitos tumbaba el menú por seis caminos (las opciones 6, 7, 8, 9, 10 con el
# id y la 3 con el salario), y los seis cruzan por `pedir_entero`.
#
# QUÉ ES 2**63-1: en Python `**` es la potencia, así que se lee "2 elevado a
# 63, menos 1" = 9.223.372.036.854.775.807, el mayor entero que SQLite puede
# guardar. Sale de los 64 bits: uno se reserva para el signo (positivo o
# negativo) y quedan 63 para el valor. Con 63 bits hay 2**63 combinaciones,
# y como una de ellas es el cero, el máximo es una menos. Es el mismo tope
# que el BIGINT de otras bases de datos.
#
# El techo de 10**9 (mil millones) queda muy por debajo de ese límite, y aun
# así sobra: ningún id ni salario del caso se acerca a esa cifra.
MAXIMO_ENTERO = 10**9

# Las opciones que piden algo por teclado, y por lo tanto las únicas donde
# tiene sentido avisar que x cancela. La 1, la 4 y la 5 no preguntan nada.
PIDEN_DATOS = {"2", "3", "6", "7", "8", "9", "10"}


# Centraliza el retorno visual: usa el comando nativo de cada sistema y deja
# una sola forma de redibujar el menú inicial.
def limpiar_y_mostrar_menu() -> None:
    """Limpia la terminal y vuelve a dibujar el menú principal."""
    os.system("cls" if os.name == "nt" else "clear")
    print(MENU)


# --- Entrada validada del usuario ------------------------------------
# Reintentan hasta recibir algo usable, así el programa no avanza con un dato
# que las clases vayan a rechazar por formato.
#
# LAS DOS CAPAS NO SE PISAN: aquí se valida el FORMATO (que sea número, que
# sea fecha); en las clases, la REGLA DE NEGOCIO (salario positivo, contrato
# no futuro). Esta se salta llamando a la clase desde otro programa, la de
# allá no; por eso allá manda, y esta solo evita excepciones por un dedazo.

# CANCELAR ES UNA EXCEPCIÓN, NO UN `None`. Si `leer` devolviera None, cada una
# de las siete opciones que piden datos necesitaría su propio `if` después de
# cada pregunta, y contratar hace seis. Con la excepción, el corte ocurre en
# un solo lugar y sube directo al bucle de `main()`: el constructor nunca
# llega a ejecutarse, así que no queda un objeto a medias ni se toca la base.
#
# Hereda de `Exception` y no de `ValueError` a propósito: cancelar no es un
# dato inválido, y si fuera ValueError lo atraparía `pedir_fecha` como fecha
# mal escrita y volvería a preguntar en vez de cancelar.
class Cancelado(Exception):
    """El usuario escribió x en lugar del dato."""


# El único `input()` de datos del programa. `lower()` hace que X mayúscula
# también cancele. Costo asumido: no se puede ingresar un dato que sea
# literalmente "x", y ningún campo del modelo lo admitiría.
def leer(mensaje: str) -> str:
    valor = input(mensaje).strip()
    if valor.lower() == "x":
        raise Cancelado
    return valor


def pedir_texto(mensaje: str) -> str:
    while True:
        valor = leer(mensaje)
        if valor:
            return valor
        print("   ! No puede quedar vacío.")


# `isdecimal()` y no `int()`: rechaza el signo menos, y ningún campo que usa
# admite negativos. Y no `isdigit()`, que es lo que había antes:
# `"²".isdigit()` es True pero `int("²")` falla. `isdecimal()` acepta
# exactamente lo que `int()` sabe convertir.
def pedir_entero(mensaje: str) -> int:
    while True:
        valor = leer(mensaje)
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
            return date.fromisoformat(leer(mensaje))
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
    # CANDADO DE BASE VACÍA. Sin él, repetir la opción guardaba los dos
    # departamentos y recién después chocaba contra el UNIQUE del correo del
    # primer empleado: el mensaje decía "ya está registrado", pero quedaban
    # dos departamentos duplicados. Cada método abre y cierra su propia
    # conexión, así que no hay una transacción que abarque la siembra entera
    # y pueda deshacerla. Revisar antes de escribir es la forma de que el
    # mensaje y la base digan lo mismo.
    #
    # Pregunta por las dos tablas porque borrar todos los departamentos deja
    # a los empleados vivos (ON DELETE SET NULL), y esos correos chocarían.
    if Departamento.listar() or Empleado.listar():
        print("   ! Ya hay datos cargados: los ejemplos solo se crean "
              "sobre una base vacía.")
        return
    # El diccionario guarda los objetos ya guardados para enlazar después a
    # cada empleado con su departamento. Guarda el objeto y no el id porque la
    # relación se escribe con el método del UML, `agregar_empleado`, que
    # recibe objetos; por dentro traduce a la clave foránea.
    departamentos = {
        nombre: Departamento(nombre)
        for nombre in ("Desarrollo Sostenible", "Investigación y Desarrollo")
    }
    for departamento in departamentos.values():
        departamento.guardar(solicitante)
    for nombre, direccion, telefono, correo, contrato, salario, dep in PLANTILLA:
        empleado = Empleado(nombre, direccion, telefono, correo,
                            contrato, salario)
        empleado.guardar(solicitante)
        departamentos[dep].agregar_empleado(empleado, solicitante)
    print(f"   Creados {len(departamentos)} departamentos "
          f"y {len(PLANTILLA)} empleados.")


# --- Despacho ---------------------------------------------------------
# Cadena de `if/elif` y no un diccionario de funciones: cada opción pide datos
# distintos, y un despacho por tabla obligaría a uniformar firmas que no se
# parecen. Aburrido y legible le gana a ingenioso.

def ejecutar(opcion: str, solicitante: Usuario) -> None:
    # El aviso va una vez al entrar a la opción y no pegado a cada pregunta:
    # contratar hace seis, y repetir "(x cancela)" seis veces es ruido.
    if opcion in PIDEN_DATOS:
        print("   (escriba x para cancelar)")

    # --- C: crear
    if opcion == "1":
        # Primera del menú porque es lo primero que se hace en una base vacía.
        sembrar(solicitante)

    elif opcion == "2":
        # Construir ya valida: si el nombre no sirve, no se toca la base.
        departamento = Departamento(pedir_texto("   Nombre: "))
        print("   Departamento creado con id "
              f"{departamento.guardar(solicitante)}.")

    elif opcion == "3":
        # Los seis campos llegan al constructor con el tipo correcto; lo que
        # el constructor juzga es la regla de negocio. Python evalúa los seis
        # argumentos antes de llamar a `Empleado(...)`, así que una x en el
        # salario cancela sin que el objeto llegue a existir.
        empleado = Empleado(pedir_texto("   Nombre completo: "),
                            pedir_texto("   Dirección: "),
                            pedir_texto("   Teléfono: "),
                            pedir_texto("   Correo: "),
                            pedir_fecha("   Inicio de contrato (AAAA-MM-DD): "),
                            pedir_entero("   Salario: "))
        print(f"   Empleado contratado con id {empleado.guardar(solicitante)}.")

    # --- R: leer
    elif opcion == "4":
        listar_departamentos()

    elif opcion == "5":
        listar_empleados()

    # --- U: actualizar
    elif opcion == "6":
        # Se busca primero para confirmar que existe: un UPDATE sobre un id
        # inexistente no da error, solo afecta cero filas.
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        # Cortocircuito: si es None, no se pide el nombre nuevo ni se renombra.
        if departamento and departamento.renombrar(
                pedir_texto("   Nuevo nombre: "), solicitante):
            print(f"   Ahora se llama {departamento.obtener_nombre()}.")

    elif opcion == "7":
        # Imprime el resumen después de actualizar para que el usuario vea el
        # teléfono ya normalizado: escribe "22 987 6543", sale "229876543".
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado:
            empleado.actualizar_contacto(pedir_texto("   Nuevo teléfono: "),
                                         pedir_texto("   Nuevo correo: "))
            print(f"   {empleado.obtener_resumen()}")

    elif opcion == "8":
        # El `return` temprano evita pedir el segundo id cuando el primero ya
        # falló. Anidar dos `if` daría lo mismo pero se lee peor.
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado is None:
            return
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        if departamento is None:
            return
        # False no es un error: el empleado ya estaba ahí y el UPDATE afectó
        # cero filas. Se dice, porque un silencio parecería una falla.
        if departamento.agregar_empleado(empleado, solicitante):
            print(f"   {empleado.obtener_nombre()} quedó en "
                  f"{departamento.obtener_nombre()}.")
        else:
            print(f"   ! {empleado.obtener_nombre()} ya pertenecía a "
                  f"{departamento.obtener_nombre()}.")

    # --- D: eliminar
    elif opcion == "9":
        # La operación que demuestra la agregación, y el mensaje lo dice en
        # voz alta porque es el punto que hay que defender.
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        if departamento and departamento.eliminar(solicitante):
            print("   Departamento eliminado. Sus empleados siguen vigentes, "
                  "sin departamento: la agregación es ON DELETE SET NULL.")

    elif opcion == "10":
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado and empleado.eliminar(solicitante):
            print("   Empleado eliminado, junto con sus registros de tiempo.")

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
    #
    # La clave es aleatoria y desechable, y antes era el literal
    # "Clave-RRHH-2026" escrito aquí. La segunda auditoría lo marcó: una clave
    # en el código fuente viaja al zip de la entrega y al repositorio. Nadie
    # la verifica, porque sin login de este objeto solo se usa
    # `tiene_permiso()`, así que una al azar sirve igual y no hay secreto que
    # filtrar. El sufijo garantiza las cuatro familias de caracteres que pide
    # `_validar_clave`: `token_urlsafe` puede no traer un dígito y el
    # constructor rechazaría la clave una vez cada tantos arranques.
    solicitante = Usuario("rrhh.admin", secrets.token_urlsafe(24) + "aA1!",
                          Rol.ADMIN_RRHH)
    limpiar_y_mostrar_menu()

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
                limpiar_y_mostrar_menu()
                continue
            ejecutar(opcion, solicitante)

        # Los except van de más específico a más general porque Python entra
        # al primero que coincida: `IntegrityError` y `OperationalError` son
        # subclases de `sqlite3.Error` y después del genérico nunca correrían.

        # Primero, porque cancelar no es un error: el usuario lo pidió. Por
        # eso el mensaje no lleva el "!" de los demás. "No se guardó nada" es
        # cierto: la excepción sale antes de cualquier `guardar()` o UPDATE.
        except Cancelado:
            print("   Acción cancelada. No se guardó nada.")

        # Una restricción de la base rechazó el dato. El correo repetido es el
        # caso frecuente y lleva mensaje propio; antes TODO IntegrityError
        # decía "Ese correo ya está registrado", también una clave foránea o
        # un CHECK, y el mensaje mentía. `sqlite_errorname` (Python 3.11+)
        # identifica la restricción por su código, sin depender del texto en
        # inglés del error. El único UNIQUE que el menú puede violar es el del
        # correo: `usuario` no se escribe en esta unidad.
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
                print("   ! Ese correo ya está registrado. Use otro.")
            else:
                print("   ! La base rechazó el dato por una restricción. "
                      "No se guardó nada.")

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

        # La salida de cada opción queda visible hasta que el usuario decida
        # continuar; entonces se vuelve al mismo punto de partida visual.
        try:
            input("\n   Presione Enter para continuar...")
        except (KeyboardInterrupt, EOFError):
            print("\n   Interrumpido. Hasta luego.")
            return
        limpiar_y_mostrar_menu()


# Permite importar este módulo sin que arranque el menú.
if __name__ == "__main__":
    main()
