"""EcoTech Solutions — menú de terminal.

Pide inicio de sesión y ejecuta el ciclo CRUD sobre las dos clases
relacionadas del modelo, `Departamento` y `Empleado`, más los servicios
externos de la Unidad 3. No contiene ninguna sentencia SQL ni ninguna
solicitud HTTP: viven en `ecotech.py` y en `servicios.py`.

    python3 main.py
"""

import getpass
import sqlite3
import time
from datetime import date

from ecotech import (Departamento, Empleado, Informe, Rol, Usuario, autorizar,
                     crear_tablas, hay_usuarios)
from servicios import ServicioExterno, ServicioNoDisponible

MENU = """
==================================================================
   EcoTech Solutions — Gestión de empleados
   Sesión: {usuario}
==================================================================
   C — CREAR                     U — ACTUALIZAR
    1. Datos de ejemplo           6. Renombrar departamento
    2. Departamento               7. Contacto del empleado
    3. Empleado (contratar)       8. Asignar a departamento

   R — LEER                      D — ELIMINAR
    4. Departamentos              9. Departamento
    5. Empleados                 10. Empleado

   S — SERVICIOS EXTERNOS        A — ADMINISTRACIÓN
   11. Clima para faena          13. Informe de dotación
   12. Pago en moneda extranjera 14. Crear usuario

   Escriba "x" para cancelar la acción en curso   ·   0. salir
=================================================================="""

# Techo de todo entero que teclee el usuario. Existe porque SQLite guarda
# enteros de 64 bits, y el mayor que cabe es 2**63-1 (2 elevado a 63, menos
# 1: 9.223.372.036.854.775.807). Un número más grande no lanza un error de
# base, lanza OverflowError al convertirlo, y eso mataría el programa.
MAXIMO_ENTERO = 10**9

PIDEN_DATOS = {"2", "3", "6", "7", "8", "9", "10", "11", "12", "13", "14"}

# Control de flujo: el permiso se revisa antes de pedir un solo dato. Los
# métodos de las clases lo vuelven a revisar al escribir.
PERMISO = {"1": "empleados", "2": "departamentos", "3": "empleados",
           "6": "departamentos", "7": "empleados", "8": "empleados",
           "9": "departamentos", "10": "empleados", "11": "proyectos",
           "12": "empleados", "13": "informes", "14": "usuarios"}

INACTIVIDAD_MAXIMA = 10 * 60                # segundos sin actividad antes de cerrar la sesión
ROLES = {"1": Rol.ADMIN_RRHH, "2": Rol.GERENTE, "3": Rol.EMPLEADO}
SERVICIO = ServicioExterno()

PIDE_ID_DEPARTAMENTO = "   Id del departamento: "
PIDE_ID_EMPLEADO = "   Id del empleado: "
PIDE_USUARIO = "   Usuario (3 a 20: minúsculas, números, . _ -): "
INTERRUMPIDO = "\n   Interrumpido. Hasta luego."
CREDENCIALES_INVALIDAS = ("   ! Credenciales inválidas o cuenta bloqueada "
                          "temporalmente.")


def limpiar_y_mostrar_menu(usuario: str) -> None:
    """Limpia la terminal y vuelve a dibujar el menú principal."""
    # Secuencia ANSI: borra la pantalla y lleva el cursor al inicio, sin
    # abrir una shell ni buscar un ejecutable en el PATH.
    print("\033[2J\033[H", end="")
    print(MENU.format(usuario=usuario))


# --- Entrada validada del usuario ------------------------------------
# Reintentan hasta recibir algo usable. El programa nunca avanza con un
# dato que las clases vayan a rechazar por formato.

class Cancelado(Exception):
    """El usuario escribió x en lugar del dato."""


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


def pedir_entero(mensaje: str) -> int:
    while True:
        valor = leer(mensaje)
        if not valor.isdecimal():
            print("   ! Escriba un número entero, sin puntos ni letras.")
        elif len(valor) > 20 or int(valor) > MAXIMO_ENTERO:
            print(f"   ! Demasiado grande. El máximo es {MAXIMO_ENTERO}.")
        else:
            return int(valor)


def pedir_fecha(mensaje: str) -> date:
    while True:
        try:
            return date.fromisoformat(leer(mensaje))
        except ValueError:
            print("   ! Formato de fecha: AAAA-MM-DD, por ejemplo 2024-03-01.")


def pedir_clave_nueva() -> str:
    """Sin eco en pantalla y dos veces. La política la valida Usuario."""
    while True:
        clave = getpass.getpass("   Clave (12 o más, con 3 de: minúscula, "
                                "mayúscula, número, símbolo): ")
        if clave.lower() == "x":
            raise Cancelado
        if clave == getpass.getpass("   Repita la clave: "):
            return clave
        print("   ! Las claves no coinciden.")


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

DESARROLLO = "Desarrollo Sostenible"
INVESTIGACION = "Investigación y Desarrollo"

PLANTILLA = [
    ("Juanita Bravo Sepúlveda", "Av. Matta 1234, Santiago",
     "+56 9 8765 4321", "jbravo@ecotech.cl", date(2023, 4, 17), 1450000,
     DESARROLLO),
    ("Ignacio Fuentes Cárdenas", "Los Carrera 890, Valparaíso",
     "+56 9 6543 2109", "ifuentes@ecotech.cl", date(2022, 11, 2), 1980000,
     DESARROLLO),
    ("Camila Reyes Ortiz", "Pedro de Valdivia 55, Providencia",
     "+56 9 7412 8536", "creyes@ecotech.cl", date(2024, 1, 8), 1260000,
     INVESTIGACION),
]


def sembrar(solicitante: Usuario) -> None:
    """La C del ciclo, con datos que parecen reales."""
    if Departamento.listar() or Empleado.listar():
        print("   ! Ya hay datos cargados: los ejemplos solo se crean "
              "sobre una base vacía.")
        return
    departamentos = {
        nombre: Departamento(nombre) for nombre in (DESARROLLO, INVESTIGACION)
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


# --- Opciones que piden datos -----------------------------------------

def crear_departamento(solicitante: Usuario) -> None:
    departamento = Departamento(pedir_texto("   Nombre: "))
    print("   Departamento creado con id "
          f"{departamento.guardar(solicitante)}.")


def contratar_empleado(solicitante: Usuario) -> None:
    empleado = Empleado(pedir_texto("   Nombre completo: "),
                        pedir_texto("   Dirección: "),
                        pedir_texto("   Teléfono: "),
                        pedir_texto("   Correo: "),
                        pedir_fecha("   Inicio de contrato (AAAA-MM-DD): "),
                        pedir_entero("   Salario: "))
    print(f"   Empleado contratado con id {empleado.guardar(solicitante)}.")


def renombrar_departamento(solicitante: Usuario) -> None:
    departamento = buscar_o_avisar(Departamento,
                                   pedir_entero(PIDE_ID_DEPARTAMENTO))
    if departamento and departamento.renombrar(
            pedir_texto("   Nuevo nombre: "), solicitante):
        print(f"   Ahora se llama {departamento.obtener_nombre()}.")


def editar_contacto(_solicitante: Usuario) -> None:
    empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    if empleado:
        empleado.actualizar_contacto(pedir_texto("   Nuevo teléfono: "),
                                     pedir_texto("   Nuevo correo: "))
        print(f"   {empleado.obtener_resumen()}")


def asignar_a_departamento(solicitante: Usuario) -> None:
    empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    if empleado is None:
        return
    departamento = buscar_o_avisar(Departamento,
                                   pedir_entero(PIDE_ID_DEPARTAMENTO))
    if departamento is None:
        return
    if departamento.agregar_empleado(empleado, solicitante):
        print(f"   {empleado.obtener_nombre()} quedó en "
              f"{departamento.obtener_nombre()}.")
    else:
        print(f"   ! {empleado.obtener_nombre()} ya pertenecía a "
              f"{departamento.obtener_nombre()}.")


def eliminar_departamento(solicitante: Usuario) -> None:
    departamento = buscar_o_avisar(Departamento,
                                   pedir_entero(PIDE_ID_DEPARTAMENTO))
    if departamento and departamento.eliminar(solicitante):
        print("   Departamento eliminado. Sus empleados siguen vigentes, "
              "sin departamento: la agregación es ON DELETE SET NULL.")


def eliminar_empleado(solicitante: Usuario) -> None:
    empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    if empleado and empleado.eliminar(solicitante):
        print("   Empleado eliminado, junto con sus registros de tiempo.")


# --- Servicios externos y administración (Unidad 3) --------------------

def clima_para_faena(_solicitante: Usuario) -> None:
    datos = SERVICIO.obtener_clima(pedir_texto("   Ciudad de la faena: "))
    print(f"   {datos['ciudad']}: {datos['estado']}, {datos['temperatura']} °C, "
          f"humedad {datos['humedad']} %, viento {datos['viento']} km/h.")
    if datos["apto_terreno"]:
        print("   Condiciones aptas para trabajo en terreno.")
    else:
        print("   ! Riesgo para trabajo en terreno: considere reprogramar.")


def pago_en_moneda_extranjera(solicitante: Usuario) -> None:
    empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    if empleado is None:
        return
    salario = empleado.obtener_salario(solicitante)
    moneda = pedir_texto(f"   Moneda ({', '.join(ServicioExterno.MONEDAS)}): ")
    valor = SERVICIO.obtener_tipo_cambio(moneda)
    moneda = moneda.strip().upper()
    print(f"   {empleado.obtener_nombre()}: {salario:,} CLP = "
          f"{salario / valor:,.2f} {moneda}  (1 {moneda} = {valor:,.2f} CLP hoy)")


def informe_de_dotacion(solicitante: Usuario) -> None:
    informe = Informe.generar(
        "Dotación EcoTech", [*Departamento.listar(), *Empleado.listar()],
        solicitante)
    print("   " + informe.obtener_texto().replace("\n", "\n   "))
    if leer("   ¿Exportar a informe_dotacion.csv? (s/n): ").lower() == "s" \
            and informe.exportar("informe_dotacion.csv"):
        print("   Exportado a informe_dotacion.csv (sin sueldos).")


def crear_usuario(solicitante: Usuario) -> None:
    nombre = pedir_texto(PIDE_USUARIO)
    rol = None
    while rol is None:
        rol = ROLES.get(leer("   Rol (1 ADMIN_RRHH · 2 GERENTE · 3 EMPLEADO): "))
    usuario = Usuario(nombre, pedir_clave_nueva(), rol)
    print(f"   Usuario creado con id {usuario.guardar(solicitante)}.")


# --- Despacho ---------------------------------------------------------

ACCIONES = {
    "1": sembrar, "2": crear_departamento, "3": contratar_empleado,        # C
    "4": lambda _: listar_departamentos(),                                 # R
    "5": lambda _: listar_empleados(),
    "6": renombrar_departamento, "7": editar_contacto,                     # U
    "8": asignar_a_departamento,
    "9": eliminar_departamento, "10": eliminar_empleado,                   # D
    "11": clima_para_faena, "12": pago_en_moneda_extranjera,               # S
    "13": informe_de_dotacion, "14": crear_usuario,                        # A
}


def ejecutar(opcion: str, solicitante: Usuario) -> None:
    accion = ACCIONES.get(opcion)
    if accion is None:
        print("   ! Opción desconocida.")
        return
    if opcion in PERMISO:
        autorizar(solicitante, PERMISO[opcion])
    if opcion in PIDEN_DATOS:
        print("   (escriba x para cancelar)")
    accion(solicitante)


# --- Bucle del menú ---------------------------------------------------

def pedir_opcion() -> str | None:
    try:
        return input("\n   Opción: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return None


def atender(opcion: str, solicitante: Usuario) -> bool:
    """Ejecuta la opción y traduce cada error a un mensaje. False: salir."""
    try:
        ejecutar(opcion, solicitante)
    except Cancelado:
        print("   Acción cancelada. No se guardó nada.")
    except sqlite3.IntegrityError as error:
        if "usuario.nombre_usuario" in str(error):
            print("   ! Ese nombre de usuario ya existe. Use otro.")
        elif error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            print("   ! Ese correo ya está registrado. Use otro.")
        else:
            print("   ! La base rechazó el dato por una restricción. "
                  "No se guardó nada.")
    except sqlite3.OperationalError:
        print("   ! No se pudo acceder a la base de datos. Intente de nuevo.")
    except sqlite3.Error:
        print("   ! La base rechazó la operación. No se guardó nada.")
    except PermissionError as error:
        print(f"   ! {error}")
    except ServicioNoDisponible as error:
        print(f"   ! {error}")
    except ValueError as error:
        print(f"   ! {error}")
    except (KeyboardInterrupt, EOFError):
        return False
    except Exception as error:
        # Solo el tipo: el texto de una excepción desconocida puede traer
        # rutas, consultas o datos que el usuario no debe ver.
        print(f"   ! Error inesperado ({type(error).__name__}). "
              "La acción no se completó.")
    return True


def pausar() -> bool:
    try:
        input("\n   Presione Enter para continuar...")
    except (KeyboardInterrupt, EOFError):
        return False
    return True


# --- Sesión -----------------------------------------------------------

def alta_inicial() -> None:
    """Primera ejecución: la base no tiene cuentas y se crea la de RRHH."""
    print("\n   Configuración inicial: cree la cuenta de administrador "
          "(ADMIN_RRHH).")
    while True:
        try:
            Usuario(pedir_texto(PIDE_USUARIO), pedir_clave_nueva(),
                    Rol.ADMIN_RRHH).guardar()
            print("   Cuenta creada. Ahora inicie sesión.")
            return
        except ValueError as error:
            print(f"   ! {error}")


def iniciar_sesion() -> tuple[Usuario, str]:
    """Pide credenciales hasta que sean válidas. El bloqueo lo aplica Usuario."""
    print("\n   Inicio de sesión — EcoTech Solutions")
    while True:
        nombre = input("   Usuario: ").strip()
        clave = getpass.getpass("   Clave: ")
        if not nombre or not clave:
            print("   ! Usuario y clave son obligatorios.")
            continue
        try:
            usuario = Usuario.autenticar(nombre, clave)
        except ValueError:
            # Hash corrupto en la base o clave que no se puede codificar
            # (UnicodeEncodeError hereda de ValueError). Mismo mensaje que
            # una clave mala: el login no revela nada sobre la cuenta.
            usuario = None
        if usuario is not None:
            return usuario, nombre.lower()
        print(CREDENCIALES_INVALIDAS)


def usar_sesion(solicitante: Usuario, nombre: str) -> bool:
    """El menú de una sesión. True: caducó y vuelve al login. False: salir."""
    limpiar_y_mostrar_menu(nombre)
    ultima_actividad = time.monotonic()
    while True:
        opcion = pedir_opcion()
        if opcion == "0":
            print("   Hasta luego.")
            return False
        if time.monotonic() - ultima_actividad > INACTIVIDAD_MAXIMA:
            print("   ! Sesión cerrada por inactividad. Inicie sesión de nuevo.")
            return True
        if opcion is None or not atender(opcion, solicitante) or not pausar():
            print(INTERRUMPIDO)
            return False
        ultima_actividad = time.monotonic()
        limpiar_y_mostrar_menu(nombre)


def main() -> None:
    try:
        crear_tablas()
        if not hay_usuarios():
            alta_inicial()
        while usar_sesion(*iniciar_sesion()):
            pass
    except sqlite3.Error:
        print("   ! No se pudo abrir la base de datos. El programa se cierra.")
    except (Cancelado, KeyboardInterrupt, EOFError):
        print(INTERRUMPIDO)


if __name__ == "__main__":
    main()
