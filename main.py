"""EcoTech Solutions — menú de terminal.

Ejecuta el ciclo CRUD completo sobre las dos clases relacionadas del modelo:
`Departamento` y `Empleado`. No contiene ninguna sentencia SQL: toda la
persistencia vive en los métodos de las clases de `ecotech.py`.

    python3 main.py
"""

import secrets
import sqlite3
from datetime import date

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

# Techo de todo entero que teclee el usuario. Existe porque SQLite guarda
# enteros de 64 bits: un número mayor a 2**63-1 no lanza un error de base,
# lanza OverflowError al convertirlo, y eso mataría el programa.
MAXIMO_ENTERO = 10**9


# --- Entrada validada del usuario ------------------------------------
# Reintentan hasta recibir algo usable. El programa nunca avanza con un
# dato que las clases vayan a rechazar por formato.

def pedir_texto(mensaje: str) -> str:
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("   ! No puede quedar vacío.")


def pedir_entero(mensaje: str) -> int:
    while True:
        valor = input(mensaje).strip()
        if not valor.isdecimal():
            print("   ! Escriba un número entero, sin puntos ni letras.")
        elif int(valor) > MAXIMO_ENTERO:
            print(f"   ! Demasiado grande. El máximo es {MAXIMO_ENTERO}.")
        else:
            return int(valor)


def pedir_fecha(mensaje: str) -> date:
    while True:
        try:
            return date.fromisoformat(input(mensaje).strip())
        except ValueError:
            print("   ! Formato de fecha: AAAA-MM-DD, por ejemplo 2024-03-01.")


def buscar_o_avisar(clase, id: int):
    objeto = clase.buscar(id)
    if objeto is None:
        print(f"   ! No existe {clase.__name__.lower()} con id {id}.")
    return objeto


# --- Lecturas ---------------------------------------------------------

def listar_departamentos() -> None:
    departamentos = Departamento.listar()
    if not departamentos:
        print("   (no hay departamentos)")
    for departamento in departamentos:
        total = departamento.contar_empleados()
        print(f"   [{departamento.obtener_id()}] "
              f"{departamento.obtener_nombre()} · "
              f"{total} empleado{'s' if total != 1 else ''}")


def listar_empleados() -> None:
    empleados = Empleado.listar()
    if not empleados:
        print("   (no hay empleados)")
    for empleado in empleados:
        print(f"   [{empleado.obtener_id()}] {empleado.obtener_resumen()}")


# --- Datos de ejemplo -------------------------------------------------

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
    departamentos = {
        nombre: Departamento(nombre).guardar(solicitante)
        for nombre in ("Desarrollo Sostenible", "Investigación y Desarrollo")
    }
    for nombre, direccion, telefono, correo, contrato, salario, dep in PLANTILLA:
        empleado = Empleado(nombre, direccion, telefono, correo,
                            contrato, salario)
        empleado.guardar(solicitante)
        empleado.asignar_departamento(departamentos[dep], solicitante)
    print(f"   Cargados {len(departamentos)} departamentos "
          f"y {len(PLANTILLA)} empleados.")


# --- Despacho ---------------------------------------------------------

def ejecutar(opcion: str, solicitante: Usuario) -> None:
    if opcion == "1":
        departamento = Departamento(pedir_texto("   Nombre: "))
        print("   Departamento creado con id "
              f"{departamento.guardar(solicitante)}.")

    elif opcion == "2":
        listar_departamentos()

    elif opcion == "3":
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        if departamento and departamento.renombrar(
                pedir_texto("   Nuevo nombre: "), solicitante):
            print(f"   Ahora se llama {departamento.obtener_nombre()}.")

    elif opcion == "4":
        departamento = buscar_o_avisar(Departamento,
                                       pedir_entero("   Id del departamento: "))
        if departamento and departamento.eliminar(solicitante):
            print("   Departamento eliminado. Sus empleados siguen vigentes, "
                  "sin departamento: la agregación es ON DELETE SET NULL.")

    elif opcion == "5":
        empleado = Empleado(pedir_texto("   Nombre completo: "),
                            pedir_texto("   Dirección: "),
                            pedir_texto("   Teléfono: "),
                            pedir_texto("   Correo: "),
                            pedir_fecha("   Inicio de contrato (AAAA-MM-DD): "),
                            pedir_entero("   Salario: "))
        print(f"   Empleado contratado con id {empleado.guardar(solicitante)}.")

    elif opcion == "6":
        listar_empleados()

    elif opcion == "7":
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado:
            empleado.actualizar_contacto(pedir_texto("   Nuevo teléfono: "),
                                         pedir_texto("   Nuevo correo: "))
            print(f"   {empleado.obtener_resumen()}")

    elif opcion == "8":
        empleado = buscar_o_avisar(Empleado, pedir_entero("   Id del empleado: "))
        if empleado and empleado.eliminar(solicitante):
            print("   Empleado eliminado, junto con sus registros de tiempo.")

    elif opcion == "9":
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
    try:
        crear_tablas()
    except sqlite3.Error as error:
        print(f"   ! No se pudo preparar la base de datos: {error}")
        return

    solicitante = Usuario("rrhh.admin", secrets.token_urlsafe(24) + "aA1!",
                          Rol.ADMIN_RRHH)
    print(MENU)

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
        except sqlite3.IntegrityError:
            print("   ! Ese correo ya está registrado. Use otro.")
        except sqlite3.OperationalError as error:
            print(f"   ! No se pudo acceder a la base de datos: {error}")
        except sqlite3.Error:
            print("   ! La base rechazó la operación. No se guardó nada.")
        except PermissionError as error:
            print(f"   ! {error}")
        except ValueError as error:
            print(f"   ! {error}")
        except (KeyboardInterrupt, EOFError):
            print("\n   Interrumpido. Hasta luego.")
            return
        except Exception as error:
            print(f"   ! Error inesperado ({type(error).__name__}): {error}")


if __name__ == "__main__":
    main()
