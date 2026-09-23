"""EcoTech Solutions — menú de terminal.

Pide inicio de sesión y ejecuta el ciclo CRUD sobre las clases del modelo:
`Departamento` y `Empleado`, y `Proyecto` con sus horas, más los servicios
externos de la Unidad 3 aplicados a cada proyecto. No contiene ninguna sentencia SQL ni ninguna
solicitud HTTP: viven en `ecotech.py` y en `servicios.py`.

    python3 main.py
"""

import getpass
import sqlite3
import time
from datetime import date, datetime

from ecotech import (MONEDAS_PROYECTO, Departamento, Empleado, Informe,
                     Proyecto, RegistroClima, Rol, TipoCambio, Usuario,
                     autorizar, crear_tablas, hay_usuarios)
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
   11. Clima del proyecto        13. Informe de dotación
   12. Planilla en su moneda     14. Crear usuario

   P — PROYECTOS
   15. Crear proyecto            18. Quitar empleado
   16. Proyectos                 19. Registrar horas
   17. Asignar empleado          20. Eliminar proyecto

   H — HISTORIAL DE LAS APIS
   21. Guardar cambio del día    24. Borrar registro de clima
   22. Historial de clima        25. Borrar tipo de cambio
   23. Historial tipo de cambio

   Escriba "x" para cancelar la acción en curso   ·   0. salir
=================================================================="""

# Techo de todo entero que teclee el usuario. Existe porque SQLite guarda
# enteros de 64 bits, y el mayor que cabe es 2**63-1 (2 elevado a 63, menos
# 1: 9.223.372.036.854.775.807). Un número más grande no lanza un error de
# base, lanza OverflowError al convertirlo, y eso mataría el programa.
MAXIMO_ENTERO = 10**9

PIDEN_DATOS = {"2", "3", "6", "7", "8", "9", "10", "11", "12", "13", "14",
               "15", "17", "18", "19", "20", "22", "24", "25"}

# Control de flujo: el permiso se revisa antes de pedir un solo dato. Los
# métodos de las clases lo vuelven a revisar al escribir.
PERMISO = {"1": "empleados", "2": "departamentos", "3": "empleados",
           "6": "departamentos", "7": "empleados", "8": "empleados",
           "9": "departamentos", "10": "empleados", "11": "proyectos",
           "12": "empleados", "13": "informes", "14": "usuarios",
           "15": "proyectos", "17": "proyectos", "18": "proyectos",
           "19": "tiempo", "20": "proyectos", "21": "proyectos",
           "24": "proyectos", "25": "proyectos"}

INACTIVIDAD_MAXIMA = 10 * 60                # segundos sin actividad antes de cerrar la sesión
ROLES = {"1": Rol.ADMIN_RRHH, "2": Rol.GERENTE, "3": Rol.EMPLEADO}
SERVICIO = ServicioExterno()

PIDE_ID_DEPARTAMENTO = "   Id del departamento: "
PIDE_ID_EMPLEADO = "   Id del empleado: "
PIDE_ID_PROYECTO = "   Id del proyecto: "
PIDE_USUARIO = "   Usuario (3 a 20: minúsculas, números, . _ -): "
INTERRUMPIDO = "\n   Interrumpido. Hasta luego."
SESION_CADUCADA = "   ! Sesión cerrada por inactividad. Inicie sesión de nuevo."
AVISO_REFERENCIAL = ("   ! Valor referencial: el servicio no respondió y se muestra "
                     "el último dato obtenido en esta sesión.")
AVISO_REFERENCIAL_BASE = ("   ! Valor referencial: el servicio no respondió y se muestra "
                          "el último dato guardado en la base.")
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


def pedir_horas(mensaje: str) -> float:
    """El rango (más de 0, hasta 24) lo valida RegistroTiempo."""
    while True:
        valor = leer(mensaje).replace(",", ".")
        try:
            if len(valor) <= 5:
                return float(valor)
        except ValueError:
            pass
        print("   ! Escriba las horas como número, por ejemplo 7.5.")


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


def listar_proyectos() -> None:
    proyectos = Proyecto.listar()
    if not proyectos:
        print("   (no hay proyectos)")
    for proyecto in proyectos:
        print(f"   [{proyecto.obtener_id()}] {proyecto.obtener_resumen()}")


# --- Datos de ejemplo -------------------------------------------------

DESARROLLO = "Desarrollo Sostenible"
INVESTIGACION = "Investigación y Desarrollo"
CORREO_IFUENTES = "ifuentes@ecotech.cl"

PLANTILLA = [
    ("Juanita Bravo Sepúlveda", "Av. Matta 1234, Santiago",
     "+56 9 8765 4321", "jbravo@ecotech.cl", date(2023, 4, 17), 1450000,
     DESARROLLO),
    ("Ignacio Fuentes Cárdenas", "Los Carrera 890, Valparaíso",
     "+56 9 6543 2109", CORREO_IFUENTES, date(2022, 11, 2), 1980000,
     DESARROLLO),
    ("Camila Reyes Ortiz", "Pedro de Valdivia 55, Providencia",
     "+56 9 7412 8536", "creyes@ecotech.cl", date(2024, 1, 8), 1260000,
     INVESTIGACION),
]

# Un proyecto en Chile, pagado en pesos, y otro en España, pagado en euros.
PROYECTOS = [
    ("Parque Eólico Costero", "Montaje de aerogeneradores en el litoral",
     date(2024, 2, 5), "Valparaíso", "CLP",
     ("jbravo@ecotech.cl", CORREO_IFUENTES)),
    ("Planta Solar Castilla", "Asesoría en eficiencia energética",
     date(2024, 5, 6), "Madrid", "EUR",
     (CORREO_IFUENTES, "creyes@ecotech.cl")),
]


def sembrar(solicitante: Usuario) -> None:
    """La C del ciclo, con datos que parecen reales."""
    if Departamento.listar() or Empleado.listar() or Proyecto.listar():
        print("   ! Ya hay datos cargados: los ejemplos solo se crean "
              "sobre una base vacía.")
        return
    departamentos = {
        nombre: Departamento(nombre) for nombre in (DESARROLLO, INVESTIGACION)
    }
    for departamento in departamentos.values():
        departamento.guardar(solicitante)
    empleados = {}
    for nombre, direccion, telefono, correo, contrato, salario, dep in PLANTILLA:
        empleado = Empleado(nombre, direccion, telefono, correo,
                            contrato, salario)
        empleado.guardar(solicitante)
        departamentos[dep].agregar_empleado(empleado, solicitante)
        empleados[correo] = empleado
    for nombre, descripcion, inicio, ciudad, moneda, correos in PROYECTOS:
        proyecto = Proyecto(nombre, descripcion, inicio, ciudad, moneda)
        proyecto.guardar(solicitante)
        for correo in correos:
            proyecto.asignar_empleado(empleados[correo], solicitante)
    print(f"   Creados {len(departamentos)} departamentos, "
          f"{len(PLANTILLA)} empleados y {len(PROYECTOS)} proyectos.")


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

def buscar_proyecto() -> Proyecto | None:
    return buscar_o_avisar(Proyecto, pedir_entero(PIDE_ID_PROYECTO))


def clima_del_proyecto(solicitante: Usuario) -> None:
    proyecto = buscar_proyecto()
    if proyecto is None:
        return
    try:
        datos = SERVICIO.obtener_clima(proyecto.obtener_ciudad())
    except ServicioNoDisponible:
        guardado = RegistroClima.ultimo(proyecto)
        if guardado is None:
            raise
        print(AVISO_REFERENCIAL_BASE)
        print(f"   {guardado.obtener_resumen()}")
        return
    if datos["referencial"]:
        print(AVISO_REFERENCIAL)
    print(f"   {datos['ciudad']}: {datos['estado']}, {datos['temperatura']} °C, "
          f"humedad {datos['humedad']} %, viento {datos['viento']} km/h.")
    if datos["apto_terreno"]:
        print("   Condiciones aptas para trabajo en terreno.")
    else:
        print("   ! Riesgo para trabajo en terreno: considere reprogramar.")
    if not datos["referencial"]:
        registro = RegistroClima(datetime.now(), datos["ciudad"], datos["temperatura"],
                                 datos["humedad"], datos["viento"], datos["estado"],
                                 datos["apto_terreno"])
        print("   Guardado en el historial del proyecto (registro "
              f"{registro.guardar(proyecto, solicitante)}).")


def tipo_cambio_del_dia(moneda: str, solicitante: Usuario) -> float:
    """Pedir, validar, guardar e informar, con respaldo en memoria y en la base."""
    try:
        cambio = SERVICIO.obtener_tipo_cambio(moneda)
    except ServicioNoDisponible:
        guardado = TipoCambio.ultimo(moneda)
        if guardado is None:
            raise
        print(AVISO_REFERENCIAL_BASE)
        print(f"   {guardado.obtener_resumen()}")
        return guardado.obtener_valor()
    if cambio["referencial"]:
        print(AVISO_REFERENCIAL)
    elif TipoCambio(moneda, date.today(), cambio["valor"]).guardar(solicitante):
        print("   Tipo de cambio del día guardado en el historial.")
    return cambio["valor"]


def planilla_del_proyecto(solicitante: Usuario) -> None:
    """Sueldos del equipo en la moneda del país donde se ejecuta el proyecto."""
    proyecto = buscar_proyecto()
    if proyecto is None:
        return
    empleados = proyecto.listar_empleados()
    if not empleados:
        print("   ! El proyecto no tiene empleados asignados.")
        return
    moneda = proyecto.obtener_moneda()
    if moneda == "CLP":
        valor = 1.0                                     # CLP no consulta la API
        print("   Planilla en CLP: el proyecto se paga en pesos, sin conversión.")
    else:
        valor = tipo_cambio_del_dia(moneda, solicitante)   # una consulta por planilla
        print(f"   Planilla en {moneda}  (1 {moneda} = {valor:,.2f} CLP)")
    for empleado in empleados:
        salario = empleado.obtener_salario(solicitante)
        linea = f"   {empleado.obtener_nombre()}: {salario:,} CLP"
        if moneda != "CLP":
            linea += f" = {salario / valor:,.2f} {moneda}"
        print(linea)


def informe_de_dotacion(solicitante: Usuario) -> None:
    informe = Informe.generar(
        "Dotación EcoTech",
        [*Departamento.listar(), *Empleado.listar(), *Proyecto.listar()],
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
    empleado_id = None
    if rol is Rol.EMPLEADO or (rol is Rol.GERENTE and leer(
            "   ¿Vincular a un empleado? (s/n): ").lower() == "s"):
        empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
        if empleado is None:
            return
        empleado_id = empleado.obtener_id()
    usuario = Usuario(nombre, pedir_clave_nueva(), rol, empleado_id=empleado_id)
    print(f"   Usuario creado con id {usuario.guardar(solicitante)}.")


# --- Proyectos y horas -------------------------------------------------

def crear_proyecto(solicitante: Usuario) -> None:
    proyecto = Proyecto(pedir_texto("   Nombre: "),
                        pedir_texto("   Descripción: "),
                        pedir_fecha("   Inicio (AAAA-MM-DD): "),
                        pedir_texto("   Ciudad donde se ejecuta: "),
                        pedir_texto("   Moneda de pago "
                                    f"({', '.join(MONEDAS_PROYECTO)}): "))
    print(f"   Proyecto creado con id {proyecto.guardar(solicitante)}.")


def asignar_a_proyecto(solicitante: Usuario) -> None:
    empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    if empleado is None:
        return
    proyecto = buscar_proyecto()
    if proyecto is None:
        return
    if proyecto.asignar_empleado(empleado, solicitante):
        print(f"   {empleado.obtener_nombre()} ahora participa en el proyecto "
              f"{proyecto.obtener_id()}.")
    else:
        print(f"   ! {empleado.obtener_nombre()} ya estaba en ese proyecto.")


def quitar_de_proyecto(solicitante: Usuario) -> None:
    empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    if empleado is None:
        return
    proyecto = buscar_proyecto()
    if proyecto is None:
        return
    if proyecto.desasignar_empleado(empleado, solicitante):
        print(f"   {empleado.obtener_nombre()} salió del proyecto; "
              "sus horas ya registradas se conservan.")
    else:
        print(f"   ! {empleado.obtener_nombre()} no estaba en ese proyecto.")


def registrar_horas(solicitante: Usuario) -> None:
    """RRHH registra a nombre de cualquiera; los demás, solo las suyas."""
    if solicitante.tiene_permiso("empleados"):
        empleado = buscar_o_avisar(Empleado, pedir_entero(PIDE_ID_EMPLEADO))
    else:
        empleado = solicitante.obtener_empleado()
        if empleado is None:
            print("   ! Su cuenta no está vinculada a un empleado.")
        else:
            print(f"   Registro a nombre de {empleado.obtener_nombre()}.")
    if empleado is None:
        return
    proyecto = buscar_proyecto()
    if proyecto is None:
        return
    registro = empleado.registrar_tiempo(
        proyecto, pedir_fecha("   Fecha (AAAA-MM-DD): "),
        pedir_horas("   Horas: "), pedir_texto("   Descripción: "), solicitante)
    print(f"   Registradas {registro.obtener_horas():g} h. El proyecto suma "
          f"{proyecto.horas_consumidas():.2f} h.")


def eliminar_proyecto(solicitante: Usuario) -> None:
    proyecto = buscar_proyecto()
    if proyecto and proyecto.eliminar(solicitante):
        print("   Proyecto eliminado, junto con sus asignaciones.")


# --- Historial de las APIs: C, R y D, sin U (un dato de la API es evidencia) --

def guardar_tipos_de_cambio(solicitante: Usuario) -> None:
    """21 · Pedir, validar, guardar e informar cuántos se guardaron."""
    guardados = repetidos = descartados = 0
    for moneda in TipoCambio.MONEDAS:
        try:
            cambio = SERVICIO.obtener_tipo_cambio(moneda)
        except ServicioNoDisponible as error:
            print(f"   ! {moneda}: {error}")
            descartados += 1
            continue
        if cambio["referencial"]:
            print(f"   ! {moneda}: el servicio no respondió; un valor referencial "
                  "no se guarda.")
            descartados += 1
        elif TipoCambio(moneda, date.today(), cambio["valor"]).guardar(solicitante):
            guardados += 1
        else:
            repetidos += 1
    print(f"   Guardados: {guardados} · ya registrados hoy: {repetidos} · "
          f"descartados: {descartados}")


def historial_de_clima(_solicitante: Usuario) -> None:
    proyecto = buscar_proyecto()
    if proyecto is None:
        return
    registros = RegistroClima.listar(proyecto)
    if not registros:
        print("   (el proyecto no tiene consultas de clima guardadas)")
    for registro in registros:
        print(f"   [{registro.obtener_id()}] {registro.obtener_resumen()}")


def listar_tipos_de_cambio() -> None:
    tipos = TipoCambio.listar()
    if not tipos:
        print("   (no hay tipos de cambio guardados)")
    for tipo in tipos:
        print(f"   [{tipo.obtener_id()}] {tipo.obtener_resumen()}")


def borrar_registro_de_clima(solicitante: Usuario) -> None:
    registro = buscar_o_avisar(RegistroClima,
                               pedir_entero("   Id del registro de clima: "))
    if registro and registro.eliminar(solicitante):
        print("   Registro de clima eliminado.")


def borrar_tipo_de_cambio(solicitante: Usuario) -> None:
    tipo = buscar_o_avisar(TipoCambio, pedir_entero("   Id del tipo de cambio: "))
    if tipo and tipo.eliminar(solicitante):
        print("   Tipo de cambio eliminado.")


# --- Despacho ---------------------------------------------------------

ACCIONES = {
    "1": sembrar, "2": crear_departamento, "3": contratar_empleado,        # C
    "4": lambda _: listar_departamentos(),                                 # R
    "5": lambda _: listar_empleados(),
    "6": renombrar_departamento, "7": editar_contacto,                     # U
    "8": asignar_a_departamento,
    "9": eliminar_departamento, "10": eliminar_empleado,                   # D
    "11": clima_del_proyecto, "12": planilla_del_proyecto,                 # S
    "13": informe_de_dotacion, "14": crear_usuario,                        # A
    "15": crear_proyecto, "16": lambda _: listar_proyectos(),              # P
    "17": asignar_a_proyecto, "18": quitar_de_proyecto,
    "19": registrar_horas, "20": eliminar_proyecto,
    "21": guardar_tipos_de_cambio, "22": historial_de_clima,               # H
    "23": lambda _: listar_tipos_de_cambio(),
    "24": borrar_registro_de_clima, "25": borrar_tipo_de_cambio,
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
        elif "usuario.empleado_id" in str(error):
            print("   ! Ese empleado ya tiene una cuenta.")
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
            print(SESION_CADUCADA)
            return True
        if opcion is None or not atender(opcion, solicitante):
            print(INTERRUMPIDO)
            return False
        ultima_actividad = time.monotonic()      # la pausa también cuenta
        if not pausar():
            print(INTERRUMPIDO)
            return False
        if time.monotonic() - ultima_actividad > INACTIVIDAD_MAXIMA:
            print(SESION_CADUCADA)
            return True
        limpiar_y_mostrar_menu(nombre)


def main() -> None:
    try:
        crear_tablas()
        if not hay_usuarios():
            alta_inicial()
        seguir = True
        while seguir:
            seguir = usar_sesion(*iniciar_sesion())
    except sqlite3.Error:
        print("   ! No se pudo abrir la base de datos. El programa se cierra.")
    except (Cancelado, KeyboardInterrupt, EOFError):
        print(INTERRUMPIDO)


if __name__ == "__main__":
    main()
