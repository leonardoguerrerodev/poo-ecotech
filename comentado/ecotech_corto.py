"""EcoTech Solutions — sistema de gestión de empleados.

Implementación en Python del modelo UML validado en la Unidad 1
(`diagramas/modelo_u2.drawio`). Este archivo contiene, en este orden:

    1. Validaciones y autorización compartidas
    2. Esquema y conexión a la base de datos (SQLite, librería estándar)
    3. Las ocho clases del diagrama, cada una con su CRUD
    4. Autoverificación

Uso:
    python3 ecotech.py   → autoverificación sobre una base temporal hasta implementar la unidad 3
    python3 main.py      → menú de la aplicación
"""


# Un solo archivo (el docente pidió no modularizar) y solo biblioteca estándar.
import csv                                  # escribe el informe en CSV sin romper comas ni comillas
import hashlib                              # scrypt: convierte la clave en un hash que no se revierte
import os                                   # permisos 0600 de la base y rutas de la autoverificación
import re                                   # patrones de correo, teléfono y usuario
import secrets                              # sal aleatoria segura y comparación de hashes a tiempo fijo
import sqlite3                              # la base de datos: un archivo, sin servidor
from abc import ABC, abstractmethod         # clases abstractas que no se pueden instanciar
from contextlib import contextmanager       # `with conectar()`: abre y siempre cierra la conexión
from datetime import date                   # fechas de contrato, registros y proyectos
from enum import Enum                       # roles fijos: un rol mal escrito falla al crearse
from pathlib import Path                    # rutas: ubica la base y bloquea escapes con ".."

# =====================================================================
# 1. VALIDACIONES Y AUTORIZACIÓN COMPARTIDAS
# =====================================================================

# Correo permisivo a propósito, pero sin caracteres de control.
# Teléfono chileno con [0-9]: \d acepta dígitos de otros alfabetos.
PATRON_CORREO = re.compile(r"[^@\s\x00-\x1f\x7f]+@[^@\s\x00-\x1f\x7f]+\.[^@\s\x00-\x1f\x7f]+")
PATRON_USUARIO = re.compile(r"[a-z0-9._-]{3,20}")
PATRON_TELEFONO = re.compile(r"(\+?56)?[2-9][0-9]{8}")
SEPARADORES = re.compile(r"[\s()\-.]")

# Techo de negocio: un número gigante tumbaba SQLite. Repetido en el CHECK.
SALARIO_MAXIMO = 100_000_000

# Con estos caracteres una planilla lee la celda como fórmula.
INICIOS_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


# Puerta única de todo texto: no vacío, con tope y solo imprimible.
# Lo no imprimible (escapes, marcas invisibles) desarma la terminal al listar.
def texto(valor: str, campo: str, maximo: int = 120) -> str:
    limpio = valor.strip()
    if not limpio:
        raise ValueError(f"{campo} no puede estar vacío")
    if len(limpio) > maximo:
        raise ValueError(f"{campo} supera los {maximo} caracteres")
    if not limpio.isprintable():
        raise ValueError(f"{campo} contiene caracteres de control")
    return limpio


# El mismo número escrito distinto se guarda igual.
def canonico(telefono: str) -> str:
    return SEPARADORES.sub("", telefono)[-9:]


# Apóstrofo delante: la planilla no ejecuta la celda.
# Se aplica al exportar, no al guardar: el dato queda limpio.
def sin_formula(valor: str) -> str:
    return f"'{valor}" if valor.startswith(INICIOS_DE_FORMULA) else valor


# Único control de permisos. Lanza error: nadie olvida revisarlo.
def autorizar(solicitante: "Usuario", modulo: str) -> None:
    if not solicitante.tiene_permiso(modulo):
        raise PermissionError(f"No autorizado para operar sobre {modulo}")


# Sin id no hay fila: relacionar un objeto sin guardar no haría nada.
def exigir_guardado(entidad: "EntidadReportable") -> int:
    if entidad.obtener_id() is None:
        raise ValueError(f"{type(entidad).__name__} sin guardar: guárdelo "
                         "antes de relacionarlo")
    return entidad.obtener_id()


# =====================================================================
# 2. BASE DE DATOS
# =====================================================================

# SQLite: un archivo, sin servidor. La ruta sale de la carpeta de este
# archivo, no de donde se lanza el programa.
RUTA_ACTIVA = str(Path(__file__).with_name("ecotech.db"))


# Seis tablas en un bloque porque las claves foráneas se cruzan.
# SET NULL = agregación, CASCADE = composición. Las reglas también en la tabla.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS departamento (
    id         INTEGER PRIMARY KEY,
    nombre     TEXT NOT NULL,
    gerente_id INTEGER,
    FOREIGN KEY (gerente_id) REFERENCES empleado(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS empleado (
    id                    INTEGER PRIMARY KEY,
    nombre                TEXT    NOT NULL,
    direccion             TEXT    NOT NULL,
    telefono              TEXT    NOT NULL,
    correo                TEXT    NOT NULL UNIQUE,
    fecha_inicio_contrato TEXT    NOT NULL,
    salario               INTEGER NOT NULL
                          CHECK (salario > 0 AND salario <= 100000000),
    departamento_id       INTEGER,
    FOREIGN KEY (departamento_id) REFERENCES departamento(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS proyecto (
    id           INTEGER PRIMARY KEY,
    nombre       TEXT NOT NULL,
    descripcion  TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS empleado_proyecto (
    empleado_id INTEGER NOT NULL,
    proyecto_id INTEGER NOT NULL,
    PRIMARY KEY (empleado_id, proyecto_id),
    FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE,
    FOREIGN KEY (proyecto_id) REFERENCES proyecto(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS registro_tiempo (
    id          INTEGER PRIMARY KEY,
    fecha       TEXT NOT NULL,
    horas       REAL NOT NULL CHECK (horas > 0 AND horas <= 24),
    descripcion TEXT NOT NULL,
    empleado_id INTEGER NOT NULL,
    proyecto_id INTEGER NOT NULL,
    FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE,
    FOREIGN KEY (proyecto_id) REFERENCES proyecto(id)
);
CREATE TABLE IF NOT EXISTS usuario (
    id             INTEGER PRIMARY KEY,
    nombre_usuario TEXT NOT NULL UNIQUE,
    hash_clave     TEXT NOT NULL,
    rol            TEXT NOT NULL
                   CHECK (rol IN ('ADMIN_RRHH','GERENTE','EMPLEADO')),
    empleado_id    INTEGER UNIQUE,
    FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE
);
"""


# Cambia de base: la autoverificación la usa para no tocar la real.
def usar_base(ruta: str) -> None:
    global RUTA_ACTIVA
    RUTA_ACTIVA = ruta


# Una conexión por operación: claves foráneas activas, filas por nombre,
# COMMIT o ROLLBACK automático, y siempre se cierra.
@contextmanager
def conectar():
    con = sqlite3.connect(RUTA_ACTIVA)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


# Deja la base en 0600: adentro hay sueldos. Si el chmod falla, avisa y sigue.
def crear_tablas() -> None:
    with conectar() as con:
        con.executescript(ESQUEMA)
    try:
        os.chmod(RUTA_ACTIVA, 0o600)
    except OSError as error:
        print(f"   ! No se pudo restringir los permisos de la base: {error}")


# =====================================================================
# 3. CLASES DEL MODELO UML
# =====================================================================


# UML a Python: -privado = __atributo, #protegido = _atributo.
# Enum: un rol mal escrito falla al crearse, no al revisar permisos.
class Rol(Enum):
    ADMIN_RRHH = "ADMIN_RRHH"
    GERENTE = "GERENTE"
    EMPLEADO = "EMPLEADO"


# Abstracción común: Informe depende de ella y no de cuatro clases.
class EntidadReportable(ABC):
    """Abstracta. No tiene tabla: aporta el id y el contrato del resumen."""

    def __init__(self, id: int | None = None):
        self._id = id

    def obtener_id(self) -> int | None:
        return self._id

    @abstractmethod
    def obtener_resumen(self) -> str:
        ...


# Superclase abstracta: un empleado es una persona.
class Persona(EntidadReportable):
    """Abstracta. No tiene tabla: sus campos viven en la tabla de la hija."""

    def __init__(self, nombre: str, direccion: str, telefono: str,
                 correo: str, id: int | None = None):
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre")
        self.__direccion = texto(direccion, "La dirección", 200)
        # Privado: el público de la hija escribe en la base y se dispararía al leer.
        self.__fijar_contacto(telefono, correo)

    def obtener_nombre(self) -> str:
        return self.__nombre

    def actualizar_contacto(self, telefono: str, correo: str) -> None:
        self.__fijar_contacto(telefono, correo)

    # El correo pasa por texto(): tope de 254 y solo imprimible.
    def __fijar_contacto(self, telefono: str, correo: str) -> None:
        correo = texto(correo, "El correo", 254)
        if not self._validar_correo(correo):
            raise ValueError(f"Correo inválido: {correo!r}")
        if not self._validar_telefono(telefono):
            raise ValueError(f"Teléfono inválido: {telefono!r}")
        self.__telefono = canonico(telefono)
        self.__correo = correo

    # Puerta protegida para que la hija guarde los campos privados.
    def _datos_contacto(self) -> tuple[str, str, str]:
        return (self.__direccion, self.__telefono, self.__correo)

    @abstractmethod
    def obtener_resumen(self) -> str:
        return f"{self.__nombre} | {self.__correo} | {self.__telefono}"

    def _validar_correo(self, correo: str) -> bool:
        return bool(PATRON_CORREO.fullmatch(correo))

    # fullmatch: el número completo, no un pedazo.
    def _validar_telefono(self, telefono: str) -> bool:
        return bool(PATRON_TELEFONO.fullmatch(SEPARADORES.sub("", telefono)))


class Empleado(Persona):
    """tabla: empleado"""

    # Columnas con nombre, nunca SELECT *.
    COLUMNAS = ("id, nombre, direccion, telefono, correo,"
                " fecha_inicio_contrato, salario")

    # Valida antes de construir: no quedan objetos a medias.
    def __init__(self, nombre: str, direccion: str, telefono: str, correo: str,
                 fecha_inicio_contrato: date, salario: int,
                 id: int | None = None):
        if not 0 < salario <= SALARIO_MAXIMO:
            raise ValueError(f"Salario fuera de rango (1 a {SALARIO_MAXIMO}): "
                             f"{salario}")
        if fecha_inicio_contrato > date.today():
            raise ValueError("Contrato con fecha futura: "
                             f"{fecha_inicio_contrato.isoformat()}")
        super().__init__(nombre, direccion, telefono, correo, id)
        self.__fecha_inicio_contrato = fecha_inicio_contrato
        self.__salario = salario
        self.__registros: list["RegistroTiempo"] = []
        # Proyecto no se guarda en esta unidad: esa relación vive en memoria.
        self._proyectos: list["Proyecto"] = []

    # El sueldo pide permiso en la clase, no en la pantalla.
    def obtener_salario(self, solicitante: "Usuario") -> int:
        autorizar(solicitante, "empleados")
        return self.__salario

    # Composición: el empleado crea sus registros y valida fechas.
    def registrar_tiempo(self, proyecto: "Proyecto", fecha: date, horas: float,
                         descripcion: str) -> "RegistroTiempo":
        if proyecto not in self._proyectos:
            raise ValueError("El empleado no está asignado a ese proyecto")
        if fecha < self.__fecha_inicio_contrato:
            raise ValueError("La fecha es anterior al inicio del contrato")
        if fecha < proyecto._fecha_inicio:
            raise ValueError("La fecha es anterior al inicio del proyecto")
        registro = RegistroTiempo(fecha, horas, descripcion)
        self.__registros.append(registro)
        proyecto._registros.append(registro)
        return registro

    # Sin salario: un informe no filtra sueldos.
    def obtener_resumen(self) -> str:
        return (f"{super().obtener_resumen()} | "
                f"contrato: {self.__fecha_inicio_contrato.isoformat()}")

    # --- Persistencia (CRUD) ---------------------------------------

    # Todo el SQL usa ?: el dato nunca se mezcla con la consulta.
    # Un segundo guardar se rechaza: duplicaría la fila.
    def guardar(self, solicitante: "Usuario") -> int:
        """C — INSERT. El id lo asigna SQLite, no el objeto."""
        if self._id is not None:
            raise ValueError(f"El empleado ya está guardado con id {self._id}")
        direccion, telefono, correo = self._datos_contacto()
        with conectar() as con:
            cur = con.execute(
                "INSERT INTO empleado (nombre, direccion, telefono, correo,"
                " fecha_inicio_contrato, salario) VALUES (?, ?, ?, ?, ?, ?)",
                (self.obtener_nombre(), direccion, telefono, correo,
                 self.__fecha_inicio_contrato.isoformat(),
                 self.obtener_salario(solicitante)))
        self._id = cur.lastrowid
        return self._id

    # Devuelve objetos, no filas.
    @classmethod
    def listar(cls) -> list["Empleado"]:
        """R — todos, ordenados por nombre."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {cls.COLUMNAS} FROM empleado ORDER BY nombre").fetchall()
        return [cls._desde_fila(fila) for fila in filas]

    # None si no existe: no encontrar no es un error.
    @classmethod
    def buscar(cls, id: int) -> "Empleado | None":
        """R — uno por id."""
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM empleado WHERE id = ?",
                (id,)).fetchone()
        return None if fila is None else cls._desde_fila(fila)

    # Valida con Persona y recién después escribe.
    def actualizar_contacto(self, telefono: str, correo: str) -> None:
        """U — valida heredando de Persona y recién entonces escribe."""
        super().actualizar_contacto(telefono, correo)
        if self._id is None:
            return
        _, telefono_guardado, correo_guardado = self._datos_contacto()
        with conectar() as con:
            con.execute(
                "UPDATE empleado SET telefono = ?, correo = ? WHERE id = ?",
                (telefono_guardado, correo_guardado, self._id))

    # Pide permiso. rowcount dice si de verdad borró algo.
    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — arrastra los registros de tiempo por ON DELETE CASCADE."""
        autorizar(solicitante, "empleados")
        with conectar() as con:
            cur = con.execute("DELETE FROM empleado WHERE id = ?", (self._id,))
        return cur.rowcount == 1

    # La fila pasa por el constructor: un dato malo se detecta al leer.
    @classmethod
    def _desde_fila(cls, fila: sqlite3.Row) -> "Empleado":
        return cls(fila["nombre"], fila["direccion"], fila["telefono"],
                   fila["correo"],
                   date.fromisoformat(fila["fecha_inicio_contrato"]),
                   fila["salario"], id=fila["id"])


class Departamento(EntidadReportable):
    """tabla: departamento"""

    # La relación con empleados vive solo en la base, sin copias en memoria.
    def __init__(self, nombre: str, id: int | None = None):
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre del departamento")

    def obtener_nombre(self) -> str:
        return self.__nombre

    # Los métodos del UML escriben la base, con permiso y en una transacción.
    # IS NOT y no <>: comparado con NULL, <> nunca es verdadero.
    def agregar_empleado(self, empleado: "Empleado",
                         solicitante: "Usuario") -> bool:
        """U — la clave foránea de la agregación."""
        autorizar(solicitante, "empleados")
        id_departamento = exigir_guardado(self)
        id_empleado = exigir_guardado(empleado)
        with conectar() as con:
            con.execute(
                "UPDATE departamento SET gerente_id = NULL"
                " WHERE gerente_id = ? AND id <> ?",
                (id_empleado, id_departamento))
            cur = con.execute(
                "UPDATE empleado SET departamento_id = ?"
                " WHERE id = ? AND departamento_id IS NOT ?",
                (id_departamento, id_empleado, id_departamento))
        return cur.rowcount == 1

    # Solo suelta a uno propio; si era gerente, el cargo queda vacante.
    def quitar_empleado(self, empleado: "Empleado",
                        solicitante: "Usuario") -> bool:
        """U — la clave foránea vuelve a NULL."""
        autorizar(solicitante, "empleados")
        id_departamento = exigir_guardado(self)
        id_empleado = exigir_guardado(empleado)
        with conectar() as con:
            cur = con.execute(
                "UPDATE empleado SET departamento_id = NULL"
                " WHERE id = ? AND departamento_id = ?",
                (id_empleado, id_departamento))
            con.execute(
                "UPDATE departamento SET gerente_id = NULL"
                " WHERE id = ? AND gerente_id = ?",
                (id_departamento, id_empleado))
        return cur.rowcount == 1

    # El gerente debe ser del departamento: se revisa en la misma sentencia.
    def asignar_gerente(self, empleado: "Empleado",
                        solicitante: "Usuario") -> None:
        """U — gerente_id, solo si el empleado pertenece al departamento."""
        autorizar(solicitante, "departamentos")
        id_departamento = exigir_guardado(self)
        id_empleado = exigir_guardado(empleado)
        with conectar() as con:
            cur = con.execute(
                "UPDATE departamento SET gerente_id = ? WHERE id = ? AND EXISTS"
                " (SELECT 1 FROM empleado WHERE id = ? AND departamento_id = ?)",
                (id_empleado, id_departamento, id_empleado, id_departamento))
        if cur.rowcount != 1:
            raise ValueError("El gerente debe pertenecer al departamento")

    # Objetos nuevos desde la base: tocar la lista no cambia la relación.
    def listar_empleados(self) -> list["Empleado"]:
        """R — los empleados cuya clave foránea apunta aquí."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {Empleado.COLUMNAS} FROM empleado"
                " WHERE departamento_id = ? ORDER BY nombre",
                (self._id,)).fetchall()
        return [Empleado._desde_fila(fila) for fila in filas]

    # Gerente y conteo desde la base: informe y pantalla coinciden.
    def obtener_resumen(self) -> str:
        with conectar() as con:
            fila = con.execute(
                "SELECT e.nombre FROM departamento d"
                " JOIN empleado e ON e.id = d.gerente_id WHERE d.id = ?",
                (self._id,)).fetchone()
        gerente = "sin gerente" if fila is None else fila["nombre"]
        return (f"Departamento: {self.__nombre} | Gerente: {gerente} | "
                f"Empleados: {self.contar_empleados()}")

    # --- Persistencia (CRUD) ---------------------------------------

    # Crear también pide permiso: importa qué se escribe, no qué se lee.
    def guardar(self, solicitante: "Usuario") -> int:
        """C — INSERT."""
        autorizar(solicitante, "departamentos")
        if self._id is not None:
            raise ValueError(f"El departamento ya está guardado con id {self._id}")
        with conectar() as con:
            cur = con.execute("INSERT INTO departamento (nombre) VALUES (?)",
                              (self.__nombre,))
        self._id = cur.lastrowid
        return self._id

    @classmethod
    def listar(cls) -> list["Departamento"]:
        """R — todos, ordenados por nombre."""
        with conectar() as con:
            filas = con.execute(
                "SELECT id, nombre FROM departamento ORDER BY nombre").fetchall()
        return [cls(fila["nombre"], id=fila["id"]) for fila in filas]

    @classmethod
    def buscar(cls, id: int) -> "Departamento | None":
        """R — uno por id."""
        with conectar() as con:
            fila = con.execute(
                "SELECT id, nombre FROM departamento WHERE id = ?",
                (id,)).fetchone()
        return None if fila is None else cls(fila["nombre"], id=fila["id"])

    # Misma validación que al crear; el objeto cambia solo si la base aceptó.
    def renombrar(self, nombre: str, solicitante: "Usuario") -> bool:
        """U — valida antes de escribir y sincroniza el objeto en memoria."""
        autorizar(solicitante, "departamentos")
        nuevo = texto(nombre, "El nombre del departamento")
        with conectar() as con:
            cur = con.execute("UPDATE departamento SET nombre = ? WHERE id = ?",
                              (nuevo, self._id))
        if cur.rowcount == 1:
            self.__nombre = nuevo
        return cur.rowcount == 1

    # Agregación: los empleados siguen, con departamento en NULL.
    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — los empleados sobreviven: la agregación es ON DELETE SET NULL."""
        autorizar(solicitante, "departamentos")
        with conectar() as con:
            cur = con.execute("DELETE FROM departamento WHERE id = ?",
                              (self._id,))
        return cur.rowcount == 1

    # COUNT(*) trae un número, no la tabla entera.
    def contar_empleados(self) -> int:
        with conectar() as con:
            fila = con.execute(
                "SELECT COUNT(*) AS total FROM empleado WHERE departamento_id = ?",
                (self._id,)).fetchone()
        return fila["total"]


# Sin persistir en esta unidad: vive en memoria.
class Proyecto(EntidadReportable):
    """tabla: proyecto"""

    def __init__(self, nombre: str, descripcion: str, fecha_inicio: date,
                 id: int | None = None):
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre del proyecto")
        self.__descripcion = texto(descripcion, "La descripción", 500)
        self._fecha_inicio = fecha_inicio
        self._registros: list["RegistroTiempo"] = []
        self.__empleados: list["Empleado"] = []

    # Muchos a muchos: se actualizan los dos lados.
    def asignar_empleado(self, empleado: "Empleado") -> bool:
        if empleado in self.__empleados:
            return False
        self.__empleados.append(empleado)
        empleado._proyectos.append(self)
        return True

    def desasignar_empleado(self, empleado: "Empleado") -> bool:
        if empleado not in self.__empleados:
            return False
        self.__empleados.remove(empleado)
        empleado._proyectos.remove(self)
        return True

    # 0.0 inicial: siempre devuelve float.
    def horas_consumidas(self) -> float:
        return sum((r.obtener_horas() for r in self._registros), 0.0)

    def obtener_resumen(self) -> str:
        return (f"Proyecto: {self.__nombre} | "
                f"Inicio: {self._fecha_inicio.isoformat()} | "
                f"Empleados: {len(self.__empleados)} | "
                f"Horas consumidas: {self.horas_consumidas():.2f}")


class RegistroTiempo(EntidadReportable):
    """tabla: registro_tiempo"""

    # Valida antes de existir.
    def __init__(self, fecha: date, horas: float, descripcion: str,
                 id: int | None = None):
        if not self._validar_horas(horas):
            raise ValueError(f"Horas inválidas: {horas}")
        if not self._validar_fecha(fecha):
            raise ValueError(f"Fecha inválida (futura): {fecha.isoformat()}")
        super().__init__(id)
        self.__fecha = fecha
        self.__horas = horas
        self.__descripcion = texto(descripcion, "La descripción", 500)

    def obtener_horas(self) -> float:
        return self.__horas

    def obtener_resumen(self) -> str:
        return (f"Registro: {self.__fecha.isoformat()} | "
                f"Horas: {self.__horas:.2f} | "
                f"Descripción: {self.__descripcion}")

    # Más de 0 y hasta 24, igual que el CHECK.
    def _validar_horas(self, horas: float) -> bool:
        return 0 < horas <= 24

    # No se registran horas del futuro.
    def _validar_fecha(self, fecha: date) -> bool:
        return fecha <= date.today()


# Credencial: no se reporta ni se fusiona con Empleado.
class Usuario:
    """tabla: usuario — credencial de acceso, no es entidad reportable."""

    # Permisos por rol en una tabla, no en ifs.
    _PERMISOS = {
        Rol.ADMIN_RRHH: {"empleados", "departamentos", "proyectos", "informes"},
        Rol.GERENTE: {"departamentos", "proyectos", "informes"},
        Rol.EMPLEADO: {"proyectos"},
    }

    # Guarda solo el hash: la clave en claro no queda en ningún lado.
    def __init__(self, nombre_usuario: str, clave: str, rol: Rol,
                 id: int | None = None, hash_clave: str | None = None):
        # Minúsculas: Ana y ana son la misma cuenta.
        nombre_usuario = nombre_usuario.strip().lower()
        if not PATRON_USUARIO.fullmatch(nombre_usuario):
            raise ValueError(f"Nombre de usuario inválido: {nombre_usuario!r}")
        self._id = id
        self.__nombre_usuario = nombre_usuario
        self.__rol = rol
        if hash_clave is not None:
            self.__hash_clave = hash_clave
        else:
            if not self._validar_clave(clave):
                raise ValueError("La clave no cumple la política de seguridad")
            self.__hash_clave = self._hashear(clave, secrets.token_bytes(16))

    # Costo de scrypt: lento a propósito para frenar ataques.
    COSTO = (2**16, 8, 1)

    # scrypt con sal aleatoria. El hash guarda su costo para poder subirlo.
    @classmethod
    def _hashear(cls, clave: str, sal: bytes, costo=None) -> str:
        n, r, p = costo or cls.COSTO
        h = hashlib.scrypt(clave.encode(), salt=sal, n=n, r=r, p=p, dklen=32,
                           maxmem=256 * 1024 * 1024)
        return f"scrypt${n}${r}${p}${sal.hex()}${h.hex()}"

    # compare_digest: el tiempo no revela cuánto se acertó.
    def verificar_clave(self, clave: str) -> bool:
        partes = self.__hash_clave.split("$")
        if len(partes) != 6 or partes[0] != "scrypt":
            raise ValueError("El hash almacenado no tiene el formato esperado")
        n, r, p = (int(partes[1]), int(partes[2]), int(partes[3]))
        calculado = self._hashear(clave, bytes.fromhex(partes[4]), (n, r, p))
        return secrets.compare_digest(calculado.split("$")[5], partes[5])

    # Pide la clave actual y usa sal nueva.
    def cambiar_clave(self, actual: str, nueva: str) -> bool:
        if not self._validar_clave(nueva):
            raise ValueError("La clave no cumple la política de seguridad")
        if not self.verificar_clave(actual):
            return False
        self.__hash_clave = self._hashear(nueva, secrets.token_bytes(16))
        return True

    # Mínimo 12 caracteres y 3 de 4 tipos.
    def _validar_clave(self, clave: str) -> bool:
        if len(clave) < 12:
            return False
        familias = (any(c.islower() for c in clave),
                    any(c.isupper() for c in clave),
                    any(c.isdigit() for c in clave),
                    any(not c.isalnum() for c in clave))
        return sum(familias) >= 3

    # Rol desconocido = sin permisos.
    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in self._PERMISOS.get(self.__rol, set())


# Documento derivado: sin tabla.
class Informe:
    """Sin tabla: se genera al vuelo desde las entidades reportables."""

    def __init__(self, titulo: str, contenido: list[str]):
        self.__titulo = texto(titulo, "El título del informe")
        self.__fecha_generacion = date.today()
        self.__contenido = contenido

    # Polimorfismo: un método sirve para cualquier entidad reportable.
    @staticmethod
    def generar(titulo: str, entidades: list[EntidadReportable],
                solicitante: Usuario) -> "Informe":
        autorizar(solicitante, "informes")
        return Informe(titulo, [e.obtener_resumen() for e in entidades])

    # resolve() antes de comparar: bloquea rutas con .. fuera de la carpeta.
    def exportar(self, ruta: str, formato: str = "csv") -> bool:
        if formato not in ("csv", "txt"):
            raise ValueError(f"Formato no soportado: {formato!r}")
        base_dir = Path.cwd().resolve()
        destino = Path(ruta).expanduser()
        if not destino.is_absolute():
            destino = base_dir / destino
        destino = destino.resolve()
        if not destino.is_relative_to(base_dir):
            raise ValueError(f"La ruta sale de la carpeta de trabajo: {ruta!r}")
        # csv escapa comas y sin_formula frena fórmulas. Falla de disco: False.
        try:
            if formato == "csv":
                with open(destino, "w", newline="", encoding="utf-8") as archivo:
                    escritor = csv.writer(archivo)
                    escritor.writerow([sin_formula(self.__titulo),
                                       self.__fecha_generacion.isoformat()])
                    escritor.writerows([sin_formula(linea)]
                                       for linea in self.__contenido)
            else:
                with open(destino, "w", encoding="utf-8") as archivo:
                    archivo.write(self.obtener_texto())
            return True
        except OSError as error:
            print(f"Error al exportar el informe: {error}")
            return False

    def obtener_texto(self) -> str:
        return "\n".join(
            [f"{self.__titulo} ({self.__fecha_generacion.isoformat()})",
             *self.__contenido])


# =====================================================================
# 4. AUTOVERIFICACIÓN
# =====================================================================


# Verdadero si la acción falla como debe.
def _rechaza(accion, excepcion=ValueError) -> bool:
    """Verdadero si la acción falla como se espera. La red del refactor."""
    try:
        accion()
    except excepcion:
        return True
    return False


# Un assert por regla: si alguien afloja una, se cae aquí.
def _autoverificar() -> None:
    hoy = date.today()
    contrato = date(2024, 3, 1)
    admin = Usuario("rrhh.admin", "Clave-RRHH-2026", Rol.ADMIN_RRHH)
    basico = Usuario("j.bravo", "Clave-Bravo-2026", Rol.EMPLEADO)

    def nueva(correo: str = "jbravo@ecotech.cl") -> Empleado:
        return Empleado("Juanita Bravo Sepúlveda", "Av. Matta 1234",
                        "+56 9 8765 4321", correo, contrato, 1450000)

    # --- Lo que el dominio debe rechazar
    assert _rechaza(lambda: nueva("sin-arroba")), "correo sin @"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "123", "j@e.cl",
                                     contrato, 1000)), "teléfono corto"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "229876543", "j@e.cl",
                                     contrato, 0)), "salario cero"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "229876543", "j@e.cl",
                                     contrato, 10**25)), "salario desbordado"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "229876543", "j@e.cl",
                                     date(2099, 1, 1), 1000)), "contrato futuro"
    assert _rechaza(lambda: RegistroTiempo(hoy, 25, "x")), "más de 24 horas"
    assert _rechaza(lambda: Departamento("   ")), "nombre en blanco"
    assert _rechaza(lambda: Usuario("ana", "corta", Rol.EMPLEADO)), "clave corta"
    assert _rechaza(lambda: Departamento("Legal\x1b[2J")), "escape de terminal"
    assert _rechaza(lambda: nueva("j\x1bbravo@ecotech.cl")), "correo con escape"
    assert _rechaza(lambda: nueva("a@" + "b" * 260 + ".cl")), "correo sin tope"
    assert _rechaza(lambda: Departamento("Legal‮")), "marca bidi"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "٩٨٧٦٥٤٣٢١", "j@e.cl",
                                     contrato, 1000)), "dígitos no ASCII"
    assert _rechaza(lambda: nueva().obtener_salario(basico),
                    PermissionError), "salario sin permiso"

    # --- Credenciales
    assert admin.verificar_clave("Clave-RRHH-2026")
    assert not admin.verificar_clave("otra")
    assert "Clave-RRHH-2026" not in str(admin.__dict__), "la clave quedó en claro"
    assert admin.tiene_permiso("informes")
    assert not basico.tiene_permiso("informes")
    n, r, p = Usuario.COSTO
    muestra = Usuario._hashear("Clave-Muestra-2026", secrets.token_bytes(16))
    assert muestra.split("$")[:4] == ["scrypt", str(n), str(r), str(p)], \
        "el hash no registra su costo"
    sin_formato = Usuario("ana", "", Rol.EMPLEADO, hash_clave="basura")
    assert _rechaza(lambda: sin_formato.verificar_clave("x")), "hash mal formado"

    # --- CRUD sobre las dos clases relacionadas, en orden
    crear_tablas()
    assert oct(os.stat(RUTA_ACTIVA).st_mode)[-3:] == "600", "base legible por otros"

    dep = Departamento("Desarrollo Sostenible")
    id_dep = dep.guardar(admin)                                     # C
    assert id_dep is not None and dep.obtener_id() == id_dep
    ana = nueva()
    id_ana = ana.guardar(admin)                                     # C

    assert len(Departamento.listar()) == 1                          # R
    assert len(Empleado.listar()) == 1
    assert Empleado.buscar(id_ana).obtener_nombre() == "Juanita Bravo Sepúlveda"
    assert Empleado.buscar(999) is None
    assert "987654321" in Empleado.buscar(id_ana).obtener_resumen(), "canónico"

    assert dep.renombrar("Investigación y Desarrollo", admin)       # U
    assert Departamento.buscar(id_dep).obtener_nombre() == "Investigación y Desarrollo"
    ana.actualizar_contacto("22 987 6543", "j.bravo@ecotech.cl")
    assert "j.bravo@ecotech.cl" in Empleado.buscar(id_ana).obtener_resumen()
    assert dep.agregar_empleado(ana, admin)
    assert not dep.agregar_empleado(ana, admin), "ya pertenecía"
    assert dep.contar_empleados() == 1
    dep.asignar_gerente(ana, admin)

    # --- La relación vive en la base: otra instancia lee lo mismo
    copia = Departamento.buscar(id_dep)
    assert copia.obtener_resumen().endswith(
        "Gerente: Juanita Bravo Sepúlveda | Empleados: 1"), "resumen desfasado"
    assert [e.obtener_id() for e in copia.listar_empleados()] == [id_ana]
    beto = nueva("beto@ecotech.cl")
    beto.guardar(admin)
    assert _rechaza(lambda: dep.asignar_gerente(beto, admin)), "gerente ajeno"
    assert _rechaza(lambda: Departamento("Legal").agregar_empleado(ana, admin)), \
        "relación con un departamento sin guardar"
    assert _rechaza(lambda: ana.guardar(admin)), "doble INSERT"
    legal = Departamento("Legal")
    legal.guardar(admin)
    assert legal.agregar_empleado(ana, admin)
    assert copia.obtener_resumen().endswith("sin gerente | Empleados: 0"), \
        "el gerente se fue y el cargo siguió ocupado"
    assert legal.quitar_empleado(ana, admin)
    assert not legal.quitar_empleado(ana, admin), "quitar dos veces"
    assert dep.agregar_empleado(ana, admin)

    # --- Ninguna escritura pasa sin permiso del módulo que le toca
    assert _rechaza(lambda: dep.renombrar("Pirata", basico), PermissionError)
    assert _rechaza(lambda: dep.eliminar(basico), PermissionError)
    assert _rechaza(lambda: ana.eliminar(basico), PermissionError)
    assert _rechaza(lambda: dep.agregar_empleado(beto, basico), PermissionError)
    assert _rechaza(lambda: dep.quitar_empleado(ana, basico), PermissionError)
    assert _rechaza(lambda: dep.asignar_gerente(ana, basico), PermissionError)
    assert _rechaza(lambda: Departamento("X").guardar(basico), PermissionError)
    assert Departamento.buscar(id_dep) is not None, "nada de eso llegó a ejecutarse"
    assert dep.contar_empleados() == 1

    assert dep.eliminar(admin)                                      # D
    assert Empleado.buscar(id_ana) is not None, "la agregación es SET NULL"
    assert legal.agregar_empleado(ana, admin)
    legal.asignar_gerente(ana, admin)
    assert ana.eliminar(admin)
    assert Empleado.buscar(id_ana) is None
    assert legal.obtener_resumen().endswith("sin gerente | Empleados: 0"), \
        "gerente borrado que sigue en el cargo"
    assert not ana.eliminar(admin), "borrar dos veces no puede devolver éxito"

    # --- El informe depende de la abstracción, no de las clases concretas
    salida = Informe.generar("Dotación", [Departamento("Legal"), nueva()],
                             admin).obtener_texto()
    assert "Legal" in salida and "Juanita" in salida
    assert _rechaza(lambda: Informe.generar("X", [], basico), PermissionError)

    # --- La exportación no entrega fórmulas a la planilla
    informe = Informe("Dotación", ["=1+1", "@SUM(A1:A9)", "Juanita Bravo"])
    assert informe.exportar("dotacion.csv")
    filas = Path("dotacion.csv").read_text(encoding="utf-8").splitlines()
    assert filas[1] == "'=1+1" and filas[2] == "'@SUM(A1:A9)", "fórmula sin neutralizar"
    assert filas[3] == "Juanita Bravo", "se tocó un valor que no era fórmula"
    assert _rechaza(lambda: informe.exportar("../fuga.csv")), "path traversal"


# Base y carpeta temporales: no toca ecotech.db y se borran solas.
if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as carpeta:
        usar_base(os.path.join(carpeta, "autoverificacion.db"))
        os.chdir(carpeta)
        _autoverificar()
    print("OK · dominio · seguridad · CRUD sobre Empleado y Departamento")
