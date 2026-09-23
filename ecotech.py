"""EcoTech Solutions — sistema de gestión de empleados.

Implementación en Python del modelo UML validado en la Unidad 1 y revisado en la
Unidad 2 (`diagramas/modelo_u2.drawio`). Este archivo contiene, en este orden:

    1. Validaciones y autorización compartidas
    2. Esquema y conexión a la base de datos (SQLite, librería estándar)
    3. Las ocho clases del diagrama, cada una con su CRUD
    4. Autoverificación

Uso:
    python3 ecotech.py   → autoverificación sobre una base temporal
    python3 main.py      → inicio de sesión y menú de la aplicación
"""

import csv                                  # escribe el informe en CSV sin romper comas ni comillas
import hashlib                              # scrypt: convierte la clave en un hash que no se revierte
import math                                 # compara horas con tolerancia: nunca == entre decimales
import os                                   # permisos 0600 de la base y rutas de la autoverificación
import re                                   # patrones de correo, teléfono y usuario
import secrets                              # sal aleatoria segura y comparación de hashes a tiempo fijo
import sqlite3                              # la base de datos: un archivo, sin servidor
from abc import ABC, abstractmethod         # clases abstractas que no se pueden instanciar
from contextlib import contextmanager       # `with conectar()`: abre y siempre cierra la conexión
from datetime import date, datetime, timedelta  # fechas de contrato y bloqueo temporal del login
from enum import Enum                       # roles fijos: un rol mal escrito falla al crearse
from pathlib import Path                    # rutas: ubica la base y bloquea escapes con ".."

# =====================================================================
# 1. VALIDACIONES Y AUTORIZACIÓN COMPARTIDAS
# =====================================================================

PATRON_CORREO = re.compile(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+")
PATRON_USUARIO = re.compile(r"[a-z0-9._-]{3,20}")
PATRON_TELEFONO = re.compile(r"(\+?56)?[2-9]\d{8}", re.ASCII)
SEPARADORES = re.compile(r"[\s()\-.]")

SALARIO_MAXIMO = 100_000_000
MONEDAS_PROYECTO = ("CLP", "USD", "EUR")
TIPO_CAMBIO_MAXIMO = 1_000_000

INICIOS_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def texto(valor: str, campo: str, maximo: int = 120) -> str:
    limpio = valor.strip()
    if not limpio:
        raise ValueError(f"{campo} no puede estar vacío")
    if len(limpio) > maximo:
        raise ValueError(f"{campo} supera los {maximo} caracteres")
    if not limpio.isprintable():
        raise ValueError(f"{campo} contiene caracteres de control")
    return limpio


def canonico(telefono: str) -> str:
    return SEPARADORES.sub("", telefono)[-9:]


def sin_formula(valor: str) -> str:
    return f"'{valor}" if valor.startswith(INICIOS_DE_FORMULA) else valor


def autorizar(solicitante: "Usuario", modulo: str) -> None:
    if not solicitante.tiene_permiso(modulo):
        raise PermissionError(f"No autorizado para operar sobre {modulo}")


def exigir_guardado(entidad: "EntidadReportable") -> int:
    if entidad.obtener_id() is None:
        raise ValueError(f"{type(entidad).__name__} sin guardar: guárdelo "
                         "antes de relacionarlo")
    return entidad.obtener_id()


# =====================================================================
# 2. BASE DE DATOS
# =====================================================================

RUTA_ACTIVA = str(Path(__file__).with_name("ecotech.db"))

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
    fecha_inicio TEXT NOT NULL,
    ciudad       TEXT NOT NULL,
    moneda       TEXT NOT NULL CHECK (moneda IN ('CLP','USD','EUR'))
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
    intentos_fallidos INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0),
    bloqueado_hasta   TEXT,
    empleado_id    INTEGER UNIQUE,
    FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS registro_clima (
    id             INTEGER PRIMARY KEY,
    proyecto_id    INTEGER NOT NULL,
    fecha_consulta TEXT    NOT NULL,
    ciudad         TEXT    NOT NULL,
    temperatura    REAL    NOT NULL CHECK (temperatura BETWEEN -90 AND 60),
    humedad        INTEGER NOT NULL CHECK (humedad BETWEEN 0 AND 100),
    viento         REAL    NOT NULL CHECK (viento >= 0),
    estado         TEXT    NOT NULL,
    apto_terreno   INTEGER NOT NULL CHECK (apto_terreno IN (0, 1)),
    FOREIGN KEY (proyecto_id) REFERENCES proyecto(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS tipo_cambio (
    id     INTEGER PRIMARY KEY,
    moneda TEXT NOT NULL CHECK (moneda IN ('USD','EUR')),
    fecha  TEXT NOT NULL,
    valor  REAL NOT NULL CHECK (valor > 0 AND valor <= 1000000),
    UNIQUE (moneda, fecha)
);
"""


def usar_base(ruta: str) -> None:
    global RUTA_ACTIVA
    RUTA_ACTIVA = ruta


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


def crear_tablas() -> None:
    with conectar() as con:
        con.executescript(ESQUEMA)
    try:
        os.chmod(RUTA_ACTIVA, 0o600)
    except OSError:
        print("   ! No se pudo restringir los permisos de la base de datos.")


def hay_usuarios() -> bool:
    with conectar() as con:
        return con.execute("SELECT 1 FROM usuario LIMIT 1").fetchone() is not None


# =====================================================================
# 3. CLASES DEL MODELO UML
# =====================================================================


class Rol(Enum):
    ADMIN_RRHH = "ADMIN_RRHH"
    GERENTE = "GERENTE"
    EMPLEADO = "EMPLEADO"


class EntidadReportable(ABC):
    """Abstracta. No tiene tabla: aporta el id y el contrato del resumen."""

    def __init__(self, id: int | None = None):
        self._id = id

    def obtener_id(self) -> int | None:
        return self._id

    @abstractmethod
    def obtener_resumen(self) -> str:
        ...


class Persona(EntidadReportable):
    """Abstracta. No tiene tabla: sus campos viven en la tabla de la hija."""

    def __init__(self, nombre: str, direccion: str, telefono: str,
                 correo: str, id: int | None = None):
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre")
        self.__direccion = texto(direccion, "La dirección", 200)
        # Privado a propósito: el constructor no debe despachar al método
        # sobrescrito de la hija, que escribe en la base.
        self.__fijar_contacto(telefono, correo)

    def obtener_nombre(self) -> str:
        return self.__nombre

    def actualizar_contacto(self, telefono: str, correo: str) -> None:
        self.__fijar_contacto(telefono, correo)

    def __fijar_contacto(self, telefono: str, correo: str) -> None:
        correo = texto(correo, "El correo", 254)
        if not self._validar_correo(correo):
            raise ValueError(f"Correo inválido: {correo!r}")
        if not self._validar_telefono(telefono):
            raise ValueError(f"Teléfono inválido: {telefono!r}")
        self.__telefono = canonico(telefono)
        self.__correo = correo

    def _datos_contacto(self) -> tuple[str, str, str]:
        return (self.__direccion, self.__telefono, self.__correo)

    @abstractmethod
    def obtener_resumen(self) -> str:
        return f"{self.__nombre} | {self.__correo} | {self.__telefono}"

    def _validar_correo(self, correo: str) -> bool:
        return bool(PATRON_CORREO.fullmatch(correo))

    def _validar_telefono(self, telefono: str) -> bool:
        return bool(PATRON_TELEFONO.fullmatch(SEPARADORES.sub("", telefono)))


class Empleado(Persona):
    """tabla: empleado"""

    COLUMNAS = ("id, nombre, direccion, telefono, correo,"
                " fecha_inicio_contrato, salario")

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

    def obtener_salario(self, solicitante: "Usuario") -> int:
        autorizar(solicitante, "empleados")
        return self.__salario

    def registrar_tiempo(self, proyecto: "Proyecto", fecha: date, horas: float,
                         descripcion: str,
                         solicitante: "Usuario") -> "RegistroTiempo":
        """C de RegistroTiempo: la composición nace solo desde el empleado."""
        autorizar(solicitante, "tiempo")
        if not solicitante.tiene_permiso("empleados"):
            propio = solicitante.obtener_empleado()
            if propio is None or propio.obtener_id() != self._id:
                raise PermissionError("Solo puede registrar sus propias horas")
        id_empleado = exigir_guardado(self)
        id_proyecto = exigir_guardado(proyecto)
        if fecha < self.__fecha_inicio_contrato:
            raise ValueError("La fecha es anterior al inicio del contrato")
        if fecha < proyecto._fecha_inicio:
            raise ValueError("La fecha es anterior al inicio del proyecto")
        registro = RegistroTiempo(fecha, horas, descripcion)
        with conectar() as con:
            if con.execute("SELECT 1 FROM empleado_proyecto"
                           " WHERE empleado_id = ? AND proyecto_id = ?",
                           (id_empleado, id_proyecto)).fetchone() is None:
                raise ValueError("El empleado no está asignado a ese proyecto")
            cur = con.execute(
                "INSERT INTO registro_tiempo (fecha, horas, descripcion,"
                " empleado_id, proyecto_id) VALUES (?, ?, ?, ?, ?)",
                (*registro._datos(), id_empleado, id_proyecto))
        registro._id = cur.lastrowid
        return registro

    def obtener_resumen(self) -> str:
        return (f"{super().obtener_resumen()} | "
                f"contrato: {self.__fecha_inicio_contrato.isoformat()}")

    # --- Persistencia (CRUD) ---------------------------------------

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

    @classmethod
    def listar(cls) -> list["Empleado"]:
        """R — todos, ordenados por nombre."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {cls.COLUMNAS} FROM empleado ORDER BY nombre").fetchall()
        return [cls._desde_fila(fila) for fila in filas]

    @classmethod
    def buscar(cls, id: int) -> "Empleado | None":
        """R — uno por id."""
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM empleado WHERE id = ?",
                (id,)).fetchone()
        return None if fila is None else cls._desde_fila(fila)

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

    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — arrastra los registros de tiempo por ON DELETE CASCADE."""
        autorizar(solicitante, "empleados")
        with conectar() as con:
            cur = con.execute("DELETE FROM empleado WHERE id = ?", (self._id,))
        return cur.rowcount == 1

    @classmethod
    def _desde_fila(cls, fila: sqlite3.Row) -> "Empleado":
        return cls(fila["nombre"], fila["direccion"], fila["telefono"],
                   fila["correo"],
                   date.fromisoformat(fila["fecha_inicio_contrato"]),
                   fila["salario"], id=fila["id"])


class Departamento(EntidadReportable):
    """tabla: departamento"""

    def __init__(self, nombre: str, id: int | None = None):
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre del departamento")

    def obtener_nombre(self) -> str:
        return self.__nombre

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

    def listar_empleados(self) -> list["Empleado"]:
        """R — los empleados cuya clave foránea apunta aquí."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {Empleado.COLUMNAS} FROM empleado"
                " WHERE departamento_id = ? ORDER BY nombre",
                (self._id,)).fetchall()
        return [Empleado._desde_fila(fila) for fila in filas]

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

    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — los empleados sobreviven: la agregación es ON DELETE SET NULL."""
        autorizar(solicitante, "departamentos")
        with conectar() as con:
            cur = con.execute("DELETE FROM departamento WHERE id = ?",
                              (self._id,))
        return cur.rowcount == 1

    def contar_empleados(self) -> int:
        with conectar() as con:
            fila = con.execute(
                "SELECT COUNT(*) AS total FROM empleado WHERE departamento_id = ?",
                (self._id,)).fetchone()
        return fila["total"]


class Proyecto(EntidadReportable):
    """tabla: proyecto"""

    COLUMNAS = "id, nombre, descripcion, fecha_inicio, ciudad, moneda"

    def __init__(self, nombre: str, descripcion: str, fecha_inicio: date,
                 ciudad: str, moneda: str, id: int | None = None):
        moneda = moneda.strip().upper()
        if moneda not in MONEDAS_PROYECTO:
            raise ValueError("Moneda no soportada. Use: "
                             + ", ".join(MONEDAS_PROYECTO))
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre del proyecto")
        self.__descripcion = texto(descripcion, "La descripción", 500)
        self._fecha_inicio = fecha_inicio
        self.__ciudad = texto(ciudad, "La ciudad", 80)
        self.__moneda = moneda

    def asignar_empleado(self, empleado: "Empleado",
                         solicitante: "Usuario") -> bool:
        """U — una fila en la tabla de la asociación."""
        autorizar(solicitante, "proyectos")
        id_proyecto = exigir_guardado(self)
        id_empleado = exigir_guardado(empleado)
        with conectar() as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO empleado_proyecto (empleado_id, proyecto_id)"
                " VALUES (?, ?)", (id_empleado, id_proyecto))
        return cur.rowcount == 1

    def desasignar_empleado(self, empleado: "Empleado",
                            solicitante: "Usuario") -> bool:
        """U — borra la fila de la asociación; las horas ya imputadas quedan."""
        autorizar(solicitante, "proyectos")
        id_proyecto = exigir_guardado(self)
        id_empleado = exigir_guardado(empleado)
        with conectar() as con:
            cur = con.execute(
                "DELETE FROM empleado_proyecto"
                " WHERE empleado_id = ? AND proyecto_id = ?",
                (id_empleado, id_proyecto))
        return cur.rowcount == 1

    def listar_empleados(self) -> list["Empleado"]:
        """R — los empleados asignados, leídos de la asociación."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {Empleado.COLUMNAS} FROM empleado WHERE id IN"
                " (SELECT empleado_id FROM empleado_proyecto WHERE proyecto_id = ?)"
                " ORDER BY nombre", (self._id,)).fetchall()
        return [Empleado._desde_fila(fila) for fila in filas]

    def horas_consumidas(self) -> float:
        if self._id is None:
            return 0.0
        with conectar() as con:
            fila = con.execute(
                "SELECT COALESCE(SUM(horas), 0) AS total FROM registro_tiempo"
                " WHERE proyecto_id = ?", (self._id,)).fetchone()
        return float(fila["total"])

    def obtener_ciudad(self) -> str:
        return self.__ciudad

    def obtener_moneda(self) -> str:
        return self.__moneda

    def obtener_resumen(self) -> str:
        return (f"Proyecto: {self.__nombre} | "
                f"Descripción: {self.__descripcion} | "
                f"Ciudad: {self.__ciudad} | Moneda: {self.__moneda} | "
                f"Inicio: {self._fecha_inicio.isoformat()} | "
                f"Empleados: {len(self.listar_empleados())} | "
                f"Horas consumidas: {self.horas_consumidas():.2f}")

    # --- Persistencia (CRUD) ---------------------------------------

    def guardar(self, solicitante: "Usuario") -> int:
        """C — INSERT."""
        autorizar(solicitante, "proyectos")
        if self._id is not None:
            raise ValueError(f"El proyecto ya está guardado con id {self._id}")
        with conectar() as con:
            cur = con.execute(
                "INSERT INTO proyecto (nombre, descripcion, fecha_inicio,"
                " ciudad, moneda) VALUES (?, ?, ?, ?, ?)",
                (self.__nombre, self.__descripcion,
                 self._fecha_inicio.isoformat(), self.__ciudad, self.__moneda))
        self._id = cur.lastrowid
        return self._id

    @classmethod
    def listar(cls) -> list["Proyecto"]:
        """R — todos, ordenados por nombre."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {cls.COLUMNAS} FROM proyecto ORDER BY nombre").fetchall()
        return [cls._desde_fila(fila) for fila in filas]

    @classmethod
    def buscar(cls, id: int) -> "Proyecto | None":
        """R — uno por id."""
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM proyecto WHERE id = ?",
                (id,)).fetchone()
        return None if fila is None else cls._desde_fila(fila)

    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — se rechaza si tiene horas imputadas: esa historia no se borra."""
        autorizar(solicitante, "proyectos")
        with conectar() as con:
            if con.execute("SELECT 1 FROM registro_tiempo WHERE proyecto_id = ?"
                           " LIMIT 1", (self._id,)).fetchone():
                raise ValueError("El proyecto tiene horas registradas: "
                                 "no se puede eliminar")
            cur = con.execute("DELETE FROM proyecto WHERE id = ?", (self._id,))
        return cur.rowcount == 1

    @classmethod
    def _desde_fila(cls, fila: sqlite3.Row) -> "Proyecto":
        return cls(fila["nombre"], fila["descripcion"],
                   date.fromisoformat(fila["fecha_inicio"]), fila["ciudad"],
                   fila["moneda"], id=fila["id"])


class RegistroTiempo(EntidadReportable):
    """tabla: registro_tiempo"""

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

    def _validar_horas(self, horas: float) -> bool:
        return 0 < horas <= 24

    def _validar_fecha(self, fecha: date) -> bool:
        return fecha <= date.today()

    # --- Persistencia (CRUD) ---------------------------------------
    # C: Empleado.registrar_tiempo · D: ON DELETE CASCADE del empleado.
    # Sin U ni D propios: un registro de horas no se edita, es traza.

    @classmethod
    def listar(cls, proyecto: "Proyecto") -> list["RegistroTiempo"]:
        """R — las horas imputadas a un proyecto, por fecha."""
        with conectar() as con:
            filas = con.execute(
                "SELECT id, fecha, horas, descripcion FROM registro_tiempo"
                " WHERE proyecto_id = ? ORDER BY fecha, id",
                (proyecto.obtener_id(),)).fetchall()
        return [cls(date.fromisoformat(fila["fecha"]), fila["horas"],
                    fila["descripcion"], id=fila["id"]) for fila in filas]

    def _datos(self) -> tuple[str, float, str]:
        return (self.__fecha.isoformat(), self.__horas, self.__descripcion)


class RegistroClima(EntidadReportable):
    """tabla: registro_clima — lo que informó el servicio de clima para un proyecto."""

    COLUMNAS = ("id, fecha_consulta, ciudad, temperatura, humedad, viento, estado,"
                " apto_terreno")

    def __init__(self, fecha_consulta: datetime, ciudad: str, temperatura: float,
                 humedad: int, viento: float, estado: str, apto_terreno: bool,
                 id: int | None = None):
        for campo, valor, minimo, maximo in (("temperatura", temperatura, -90, 60),
                                             ("humedad", humedad, 0, 100),
                                             ("viento", viento, 0, 500)):
            if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                    or not math.isfinite(valor) or not minimo <= valor <= maximo):
                raise ValueError(f"Dato de clima fuera de rango: {campo}")
        super().__init__(id)
        self.__fecha_consulta = fecha_consulta
        self.__ciudad = texto(ciudad, "La ciudad")
        self.__temperatura = float(temperatura)
        self.__humedad = int(humedad)
        self.__viento = float(viento)
        self.__estado = texto(estado, "El estado del clima", 40)
        self.__apto_terreno = bool(apto_terreno)

    def obtener_resumen(self) -> str:
        return (f"Clima {self.__fecha_consulta:%Y-%m-%d %H:%M} | {self.__ciudad} | "
                f"{self.__estado}, {self.__temperatura:.1f} °C, humedad "
                f"{self.__humedad} %, viento {self.__viento:.1f} km/h | "
                + ("apto para terreno" if self.__apto_terreno else "riesgo en terreno"))

    # --- Persistencia (CRUD) ---------------------------------------
    # C: guardar · R: listar, buscar, ultimo · D: eliminar. Sin U: es evidencia.

    def guardar(self, proyecto: "Proyecto", solicitante: "Usuario") -> int:
        """C — INSERT, ligado al proyecto consultado."""
        autorizar(solicitante, "proyectos")
        if self._id is not None:
            raise ValueError(f"El registro ya está guardado con id {self._id}")
        id_proyecto = exigir_guardado(proyecto)
        with conectar() as con:
            cur = con.execute(
                "INSERT INTO registro_clima (proyecto_id, fecha_consulta, ciudad,"
                " temperatura, humedad, viento, estado, apto_terreno)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id_proyecto, self.__fecha_consulta.isoformat(timespec="seconds"),
                 self.__ciudad, self.__temperatura, self.__humedad, self.__viento,
                 self.__estado, int(self.__apto_terreno)))
        self._id = cur.lastrowid
        return self._id

    @classmethod
    def listar(cls, proyecto: "Proyecto") -> list["RegistroClima"]:
        """R — el historial de un proyecto, del más reciente al más antiguo."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {cls.COLUMNAS} FROM registro_clima WHERE proyecto_id = ?"
                " ORDER BY fecha_consulta DESC, id DESC",
                (proyecto.obtener_id(),)).fetchall()
        return [cls._desde_fila(fila) for fila in filas]

    @classmethod
    def ultimo(cls, proyecto: "Proyecto") -> "RegistroClima | None":
        """R — el último valor conocido: respaldo cuando la red falla."""
        registros = cls.listar(proyecto)
        return registros[0] if registros else None

    @classmethod
    def buscar(cls, id: int) -> "RegistroClima | None":
        """R — uno por id."""
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM registro_clima WHERE id = ?",
                (id,)).fetchone()
        return None if fila is None else cls._desde_fila(fila)

    def eliminar(self, solicitante: "Usuario") -> bool:
        """D"""
        autorizar(solicitante, "proyectos")
        with conectar() as con:
            cur = con.execute("DELETE FROM registro_clima WHERE id = ?", (self._id,))
        return cur.rowcount == 1

    @classmethod
    def _desde_fila(cls, fila: sqlite3.Row) -> "RegistroClima":
        return cls(datetime.fromisoformat(fila["fecha_consulta"]), fila["ciudad"],
                   fila["temperatura"], fila["humedad"], fila["viento"],
                   fila["estado"], bool(fila["apto_terreno"]), id=fila["id"])


class TipoCambio(EntidadReportable):
    """tabla: tipo_cambio — el valor del día de una moneda, según mindicador.cl."""

    COLUMNAS = "id, moneda, fecha, valor"
    MONEDAS = ("USD", "EUR")

    def __init__(self, moneda: str, fecha: date, valor: float,
                 id: int | None = None):
        moneda = moneda.strip().upper()
        if moneda not in self.MONEDAS:
            raise ValueError("Moneda no soportada. Use: " + ", ".join(self.MONEDAS))
        if fecha > date.today():
            raise ValueError(f"Tipo de cambio con fecha futura: {fecha.isoformat()}")
        if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                or not math.isfinite(valor) or not 0 < valor <= TIPO_CAMBIO_MAXIMO):
            raise ValueError("Tipo de cambio fuera de rango")
        super().__init__(id)
        self.__moneda = moneda
        self.__fecha = fecha
        self.__valor = float(valor)

    def obtener_valor(self) -> float:
        return self.__valor

    def obtener_resumen(self) -> str:
        return (f"Tipo de cambio {self.__fecha.isoformat()} | 1 {self.__moneda} = "
                f"{self.__valor:,.2f} CLP")

    # --- Persistencia (CRUD) ---------------------------------------
    # C: guardar · R: listar, buscar, ultimo · D: eliminar. Sin U: es evidencia.

    def guardar(self, solicitante: "Usuario") -> bool:
        """C — True si es nuevo; False si ese día ya estaba guardado (UNIQUE)."""
        autorizar(solicitante, "proyectos")
        if self._id is not None:
            raise ValueError(f"El tipo de cambio ya está guardado con id {self._id}")
        with conectar() as con:
            cur = con.execute(
                "INSERT INTO tipo_cambio (moneda, fecha, valor) VALUES (?, ?, ?)"
                " ON CONFLICT (moneda, fecha) DO NOTHING",
                (self.__moneda, self.__fecha.isoformat(), self.__valor))
        if cur.rowcount == 1:
            self._id = cur.lastrowid
        return cur.rowcount == 1

    @classmethod
    def listar(cls) -> list["TipoCambio"]:
        """R — todos, del más reciente al más antiguo."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {cls.COLUMNAS} FROM tipo_cambio"
                " ORDER BY fecha DESC, moneda").fetchall()
        return [cls._desde_fila(fila) for fila in filas]

    @classmethod
    def ultimo(cls, moneda: str) -> "TipoCambio | None":
        """R — el último valor conocido de una moneda: respaldo sin red."""
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM tipo_cambio WHERE moneda = ?"
                " ORDER BY fecha DESC LIMIT 1", (moneda.strip().upper(),)).fetchone()
        return None if fila is None else cls._desde_fila(fila)

    @classmethod
    def buscar(cls, id: int) -> "TipoCambio | None":
        """R — uno por id."""
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM tipo_cambio WHERE id = ?",
                (id,)).fetchone()
        return None if fila is None else cls._desde_fila(fila)

    def eliminar(self, solicitante: "Usuario") -> bool:
        """D"""
        autorizar(solicitante, "proyectos")
        with conectar() as con:
            cur = con.execute("DELETE FROM tipo_cambio WHERE id = ?", (self._id,))
        return cur.rowcount == 1

    @classmethod
    def _desde_fila(cls, fila: sqlite3.Row) -> "TipoCambio":
        return cls(fila["moneda"], date.fromisoformat(fila["fecha"]), fila["valor"],
                   id=fila["id"])


class Usuario:
    """tabla: usuario — credencial de acceso, no es entidad reportable."""

    _PERMISOS = {
        Rol.ADMIN_RRHH: {"empleados", "departamentos", "proyectos", "informes",
                         "usuarios", "tiempo"},
        Rol.GERENTE: {"departamentos", "proyectos", "informes", "tiempo"},
        Rol.EMPLEADO: {"tiempo"},
    }

    COLUMNAS = ("id, nombre_usuario, hash_clave, rol, intentos_fallidos,"
                " bloqueado_hasta, empleado_id")
    MAX_INTENTOS = 5
    BLOQUEO = timedelta(minutes=5)

    def __init__(self, nombre_usuario: str, clave: str, rol: Rol,
                 id: int | None = None, hash_clave: str | None = None,
                 intentos_fallidos: int = 0,
                 bloqueado_hasta: datetime | None = None,
                 empleado_id: int | None = None):
        nombre_usuario = nombre_usuario.strip().lower()
        if not PATRON_USUARIO.fullmatch(nombre_usuario):
            raise ValueError(f"Nombre de usuario inválido: {nombre_usuario!r}")
        if rol is Rol.EMPLEADO and empleado_id is None:
            raise ValueError("Una cuenta EMPLEADO debe estar vinculada a un empleado")
        self._id = id
        self.__empleado_id = empleado_id
        self.__nombre_usuario = nombre_usuario
        self.__rol = rol
        self.__intentos_fallidos = intentos_fallidos
        self.__bloqueado_hasta = bloqueado_hasta
        if hash_clave is not None:
            self.__hash_clave = hash_clave
        else:
            if not self._validar_clave(clave):
                raise ValueError("La clave no cumple la política de seguridad")
            self.__hash_clave = self._hashear(clave, secrets.token_bytes(16))

    COSTO = (2**16, 8, 1)

    @classmethod
    def _hashear(cls, clave: str, sal: bytes, costo=None) -> str:
        n, r, p = costo or cls.COSTO
        h = hashlib.scrypt(clave.encode(), salt=sal, n=n, r=r, p=p, dklen=32,
                           maxmem=256 * 1024 * 1024)
        return f"scrypt${n}${r}${p}${sal.hex()}${h.hex()}"

    def verificar_clave(self, clave: str) -> bool:
        partes = self.__hash_clave.split("$")
        if len(partes) != 6 or partes[0] != "scrypt":
            raise ValueError("El hash almacenado no tiene el formato esperado")
        n, r, p = (int(partes[1]), int(partes[2]), int(partes[3]))
        calculado = self._hashear(clave, bytes.fromhex(partes[4]), (n, r, p))
        return secrets.compare_digest(calculado.split("$")[5], partes[5])

    def cambiar_clave(self, actual: str, nueva: str) -> bool:
        if not self._validar_clave(nueva):
            raise ValueError("La clave no cumple la política de seguridad")
        if not self.verificar_clave(actual):
            return False
        self.__hash_clave = self._hashear(nueva, secrets.token_bytes(16))
        return True

    def _validar_clave(self, clave: str) -> bool:
        if len(clave) < 12:
            return False
        familias = (any(c.islower() for c in clave),
                    any(c.isupper() for c in clave),
                    any(c.isdigit() for c in clave),
                    any(not c.isalnum() for c in clave))
        return sum(familias) >= 3

    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in self._PERMISOS.get(self.__rol, set())

    def obtener_empleado(self) -> "Empleado | None":
        if self.__empleado_id is None:
            return None
        return Empleado.buscar(self.__empleado_id)

    # --- Persistencia y acceso ---------------------------------------

    def guardar(self, solicitante: "Usuario | None" = None) -> int:
        """C — INSERT. Sin solicitante solo entra la primera cuenta, y como ADMIN_RRHH."""
        if self._id is not None:
            raise ValueError(f"El usuario ya está guardado con id {self._id}")
        if solicitante is not None:
            autorizar(solicitante, "usuarios")
        elif self.__rol is not Rol.ADMIN_RRHH:
            raise PermissionError("La cuenta inicial debe ser ADMIN_RRHH")
        # Sin sesión, el INSERT solo ocurre si la tabla está vacía: la
        # comprobación y la escritura son una sola sentencia.
        condicion = "" if solicitante else " WHERE NOT EXISTS (SELECT 1 FROM usuario)"
        with conectar() as con:
            cur = con.execute(
                "INSERT INTO usuario (nombre_usuario, hash_clave, rol, empleado_id)"
                " SELECT ?, ?, ?, ?" + condicion,
                (self.__nombre_usuario, self.__hash_clave, self.__rol.value,
                 self.__empleado_id))
        if cur.rowcount != 1:
            raise PermissionError("Ya existe una cuenta: inicie sesión para crear otra")
        self._id = cur.lastrowid
        return self._id

    @classmethod
    def buscar_por_nombre(cls, nombre_usuario: str) -> "Usuario | None":
        """R — uno por nombre. Un nombre con formato inválido ni llega a la base."""
        nombre_usuario = nombre_usuario.strip().lower()
        if not PATRON_USUARIO.fullmatch(nombre_usuario):
            return None
        with conectar() as con:
            fila = con.execute(
                f"SELECT {cls.COLUMNAS} FROM usuario WHERE nombre_usuario = ?",
                (nombre_usuario,)).fetchone()
        if fila is None:
            return None
        hasta = fila["bloqueado_hasta"]
        return cls(fila["nombre_usuario"], "", Rol(fila["rol"]), id=fila["id"],
                   hash_clave=fila["hash_clave"],
                   intentos_fallidos=fila["intentos_fallidos"],
                   bloqueado_hasta=hasta and datetime.fromisoformat(hasta),
                   empleado_id=fila["empleado_id"])

    @classmethod
    def autenticar(cls, nombre: str, clave: str) -> "Usuario | None":
        """El usuario si la clave es correcta y la cuenta no está bloqueada.

        Siempre calcula un scrypt, exista o no la cuenta: si no, el tiempo
        de respuesta revelaría qué nombres de usuario existen.
        """
        usuario = cls.buscar_por_nombre(nombre)
        if usuario is None:
            cls._hashear(clave, bytes(16))                  # señuelo: misma demora
            return None
        ahora = datetime.now()
        bloqueada = (usuario.__bloqueado_hasta is not None
                     and ahora < usuario.__bloqueado_hasta)
        correcta = usuario.verificar_clave(clave)   # siempre: misma demora
        if bloqueada:
            return None
        # ponytail: contador leído y escrito en dos pasos; basta con un solo
        # usuario a la vez. Con acceso concurrente: UPDATE ... SET n = n + 1.
        intentos = 0 if correcta else usuario.__intentos_fallidos + 1
        hasta = None
        if intentos >= cls.MAX_INTENTOS:
            intentos, hasta = 0, ahora + cls.BLOQUEO
        with conectar() as con:
            con.execute(
                "UPDATE usuario SET intentos_fallidos = ?, bloqueado_hasta = ?"
                " WHERE id = ?",
                (intentos, hasta and hasta.isoformat(), usuario._id))
        usuario.__intentos_fallidos, usuario.__bloqueado_hasta = intentos, hasta
        return usuario if correcta else None


class Informe:
    """Sin tabla: se genera al vuelo desde las entidades reportables."""

    def __init__(self, titulo: str, contenido: list[str]):
        self.__titulo = texto(titulo, "El título del informe")
        self.__fecha_generacion = date.today()
        self.__contenido = contenido

    @staticmethod
    def generar(titulo: str, entidades: list[EntidadReportable],
                solicitante: Usuario) -> "Informe":
        autorizar(solicitante, "informes")
        return Informe(titulo, [e.obtener_resumen() for e in entidades])

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
        except OSError:
            print("   ! No se pudo escribir el archivo del informe.")
            return False

    def obtener_texto(self) -> str:
        return "\n".join(
            [f"{self.__titulo} ({self.__fecha_generacion.isoformat()})",
             *self.__contenido])


# =====================================================================
# 4. AUTOVERIFICACIÓN
# =====================================================================


def _rechaza(accion, excepcion=ValueError) -> bool:
    """Verdadero si la acción falla como se espera. La red del refactor."""
    try:
        accion()
    except excepcion:
        return True
    return False


def _autoverificar() -> None:
    hoy = date.today()
    contrato = date(2024, 3, 1)
    calle, correo = "Calle 1", "j@e.cl"
    admin = Usuario("rrhh.admin", "Clave-RRHH-2026", Rol.ADMIN_RRHH)
    basico = Usuario("j.bravo", "Clave-Bravo-2026", Rol.EMPLEADO, empleado_id=1)

    def nueva(correo: str = "jbravo@ecotech.cl") -> Empleado:
        return Empleado("Juanita Bravo Sepúlveda", "Av. Matta 1234",
                        "+56 9 8765 4321", correo, contrato, 1450000)

    # --- Lo que el dominio debe rechazar
    assert _rechaza(lambda: nueva("sin-arroba")), "correo sin @"
    assert _rechaza(lambda: Empleado("J", calle, "123", correo,
                                     contrato, 1000)), "teléfono corto"
    assert _rechaza(lambda: Empleado("J", calle, "229876543", correo,
                                     contrato, 0)), "salario cero"
    assert _rechaza(lambda: Empleado("J", calle, "229876543", correo,
                                     contrato, 10**25)), "salario desbordado"
    assert _rechaza(lambda: Empleado("J", calle, "229876543", correo,
                                     date(2099, 1, 1), 1000)), "contrato futuro"
    assert _rechaza(lambda: RegistroTiempo(hoy, 25, "x")), "más de 24 horas"
    assert _rechaza(lambda: Departamento("   ")), "nombre en blanco"
    assert _rechaza(lambda: Usuario("ana", "corta", Rol.EMPLEADO, empleado_id=1)), \
        "clave corta"
    assert _rechaza(lambda: Usuario("ana", "Clave-Ana-2026", Rol.EMPLEADO)), \
        "EMPLEADO sin empleado vinculado"
    assert _rechaza(lambda: Departamento("Legal\x1b[2J")), "escape de terminal"
    assert _rechaza(lambda: nueva("j\x1bbravo@ecotech.cl")), "correo con escape"
    assert _rechaza(lambda: nueva("a@" + "b" * 260 + ".cl")), "correo sin tope"
    assert _rechaza(lambda: Departamento("Legal\u202e")), "marca bidi"
    assert _rechaza(lambda: Empleado("J", calle, "\u0669\u0668\u0667\u0666\u0665\u0664\u0663\u0662\u0661", correo,
                                     contrato, 1000)), "dígitos no ASCII"
    assert _rechaza(lambda: nueva().obtener_salario(basico),
                    PermissionError), "salario sin permiso"

    # --- Credenciales
    assert admin.verificar_clave("Clave-RRHH-2026")
    assert not admin.verificar_clave("otra")
    assert "Clave-RRHH-2026" not in str(admin.__dict__), "la clave quedó en claro"
    assert admin.tiene_permiso("informes")
    assert not basico.tiene_permiso("informes")
    assert basico.tiene_permiso("tiempo") and not basico.tiene_permiso("proyectos"), \
        "el EMPLEADO registra horas pero no administra proyectos"
    n, r, p = Usuario.COSTO
    muestra = Usuario._hashear("Clave-Muestra-2026", secrets.token_bytes(16))
    assert muestra.split("$")[:4] == ["scrypt", str(n), str(r), str(p)], \
        "el hash no registra su costo"
    sin_formato = Usuario("ana", "", Rol.EMPLEADO, hash_clave="basura", empleado_id=1)
    assert _rechaza(lambda: sin_formato.verificar_clave("x")), "hash mal formado"

    # --- CRUD sobre las dos clases relacionadas
    crear_tablas()
    assert os.name == "nt" or oct(os.stat(RUTA_ACTIVA).st_mode).endswith("600"), \
        "base legible por otros"

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

    # --- Inicio de sesión y fuerza bruta (Unidad 3)
    rojas = "c.rojas"
    gerente = Usuario(rojas, "Clave-Rojas-2026", Rol.GERENTE)
    assert _rechaza(lambda: gerente.guardar(), PermissionError), \
        "cuenta inicial que no es ADMIN_RRHH"
    assert not hay_usuarios()
    assert admin.guardar() is not None, "alta inicial sin sesión"
    assert hay_usuarios()
    otro_admin = Usuario("intruso", "Clave-Intruso-2026", Rol.ADMIN_RRHH)
    assert _rechaza(lambda: otro_admin.guardar(), PermissionError), \
        "segunda cuenta sin sesión"
    assert _rechaza(lambda: gerente.guardar(Usuario("otro.gerente", "", Rol.GERENTE,
                                                    hash_clave="x")),
                    PermissionError), "un gerente no crea cuentas"
    assert gerente.guardar(admin)
    assert _rechaza(lambda: gerente.guardar(admin)), "doble INSERT de usuario"
    with conectar() as con:
        guardado = con.execute("SELECT hash_clave FROM usuario"
                               " WHERE nombre_usuario = ?", (rojas,)).fetchone()[0]
    assert "Clave-Rojas-2026" not in guardado and guardado.startswith("scrypt$")

    sesion = Usuario.autenticar("  C.Rojas ", "Clave-Rojas-2026")
    assert sesion is not None and sesion.tiene_permiso("informes"), "login válido"
    assert not sesion.tiene_permiso("empleados"), "el rol viene de la base"
    assert Usuario.autenticar(rojas, "otra") is None, "clave equivocada"
    assert Usuario.autenticar("nadie", "Clave-Rojas-2026") is None, "inexistente"
    assert Usuario.autenticar("", "") is None, "credenciales vacías"
    assert Usuario.autenticar("c.rojas\x1b[2J", "x") is None, "nombre con escape"
    assert Usuario.autenticar("c.rojas' OR '1'='1", "x") is None, "inyección"
    for _ in range(Usuario.MAX_INTENTOS - 1):       # ya lleva 1 fallo
        Usuario.autenticar(rojas, "equivocada")
    assert Usuario.autenticar(rojas, "Clave-Rojas-2026") is None, \
        "tras cinco fallos la cuenta se bloquea, aun con la clave correcta"
    with conectar() as con:
        con.execute("UPDATE usuario SET bloqueado_hasta = ?",
                    ((datetime.now() - timedelta(seconds=1)).isoformat(),))
    assert Usuario.autenticar(rojas, "Clave-Rojas-2026") is not None, \
        "el bloqueo es temporal"
    assert Usuario.buscar_por_nombre(rojas)._Usuario__intentos_fallidos == 0

    # --- Usuario → Empleado («identifica a»)
    soto = "b.soto"
    cuenta = Usuario(soto, "Clave-Soto-2026", Rol.EMPLEADO,
                     empleado_id=beto.obtener_id())
    cuenta.guardar(admin)
    vinculado = Usuario.buscar_por_nombre(soto).obtener_empleado()
    assert vinculado.obtener_id() == beto.obtener_id(), "vínculo sin persistir"
    assert admin.obtener_empleado() is None, "ADMIN_RRHH sin empleado"
    assert _rechaza(lambda: Usuario("b.soto.dos", "Clave-Soto-2026", Rol.EMPLEADO,
                                    empleado_id=beto.obtener_id()).guardar(admin),
                    sqlite3.IntegrityError), "dos cuentas para un empleado"
    temporal = nueva("temporal@ecotech.cl")
    temporal.guardar(admin)
    Usuario("t.temporal", "Clave-Temp-2026", Rol.EMPLEADO,
            empleado_id=temporal.obtener_id()).guardar(admin)
    assert temporal.eliminar(admin)
    assert Usuario.buscar_por_nombre("t.temporal") is None, \
        "la cuenta sobrevivió a su empleado"

    # --- Proyecto: CRUD con ciudad y moneda
    valpo = "Valparaíso"
    assert _rechaza(lambda: Proyecto("P", "d", contrato, valpo, "JPY")), \
        "moneda fuera de la lista"
    assert _rechaza(lambda: Proyecto("P", "d", contrato, "   ", "CLP")), "ciudad vacía"
    faena = Proyecto("Parque Eólico Costero", "Montaje de aerogeneradores",
                     contrato, valpo, " clp ")
    assert _rechaza(lambda: faena.guardar(cuenta), PermissionError), \
        "un EMPLEADO no crea proyectos"
    id_faena = faena.guardar(admin)
    leido = Proyecto.buscar(id_faena)
    assert (leido.obtener_ciudad(), leido.obtener_moneda()) == (valpo, "CLP")
    assert [p.obtener_id() for p in Proyecto.listar()] == [id_faena]
    assert Proyecto.buscar(999) is None
    assert _rechaza(lambda: faena.guardar(admin)), "doble INSERT de proyecto"

    # --- Asignación y horas: la relación vive en la base
    otro = nueva("otro@ecotech.cl")
    otro.guardar(admin)
    assert faena.asignar_empleado(beto, admin)
    assert not faena.asignar_empleado(beto, admin), "asignar dos veces"
    assert faena.asignar_empleado(otro, admin)
    assert faena.desasignar_empleado(otro, admin)
    assert not faena.desasignar_empleado(otro, admin), "quitar a quien no estaba"
    assert _rechaza(lambda: faena.asignar_empleado(otro, cuenta), PermissionError)
    assert _rechaza(lambda: Proyecto("P", "d", contrato, "Lima", "USD")
                    .asignar_empleado(beto, admin)), "proyecto sin guardar"
    assert [e.obtener_id() for e in Proyecto.buscar(id_faena).listar_empleados()] \
        == [beto.obtener_id()], "otra instancia no ve la asignación"

    dia = date(2025, 6, 2)
    tardio = Proyecto("Planta Solar Norte", "Obra civil", date(2025, 1, 1),
                      "Madrid", "EUR")
    tardio.guardar(admin)
    tardio.asignar_empleado(beto, admin)
    assert _rechaza(lambda: otro.registrar_tiempo(faena, dia, 8, "x", admin)), \
        "sin asignación"
    assert _rechaza(lambda: beto.registrar_tiempo(faena, date(2024, 1, 2), 8, "x", admin)), \
        "antes del contrato"
    assert _rechaza(lambda: beto.registrar_tiempo(tardio, date(2024, 6, 3), 8, "x", admin)), \
        "antes del inicio del proyecto"
    assert _rechaza(lambda: beto.registrar_tiempo(faena, hoy + timedelta(days=1), 8, "x",
                                                  admin)), "fecha futura"
    assert _rechaza(lambda: beto.registrar_tiempo(faena, dia, 25, "x", admin)), "25 horas"
    registro = beto.registrar_tiempo(faena, dia, 7.5, "Montaje de torres", admin)
    assert registro.obtener_id() is not None
    beto.registrar_tiempo(faena, dia, 1.5, "Informe de avance", cuenta)
    faena.asignar_empleado(otro, admin)             # solo el permiso lo detiene
    assert _rechaza(lambda: otro.registrar_tiempo(faena, dia, 1, "x", cuenta),
                    PermissionError), "un EMPLEADO registrando a nombre de otro"
    faena.desasignar_empleado(otro, admin)
    assert _rechaza(lambda: beto.registrar_tiempo(faena, dia, 1, "x", basico),
                    PermissionError), "un EMPLEADO cuyo empleado ya no existe"
    copia_faena = Proyecto.buscar(id_faena)
    assert math.isclose(copia_faena.horas_consumidas(), 9.0)
    assert [r.obtener_horas() for r in RegistroTiempo.listar(faena)] == [7.5, 1.5]
    assert "Empleados: 1 | Horas consumidas: 9.00" in copia_faena.obtener_resumen()
    assert _rechaza(lambda: faena.eliminar(admin)), "proyecto con horas imputadas"
    assert _rechaza(lambda: faena.eliminar(cuenta), PermissionError)
    assert Proyecto.buscar(id_faena) is not None, "el rechazo no borró nada"

    assert beto.eliminar(admin)
    assert math.isclose(faena.horas_consumidas(), 0.0, abs_tol=1e-9) \
        and faena.listar_empleados() == [], \
        "borrar el empleado arrastra horas y asignaciones"
    assert Usuario.buscar_por_nombre(soto) is None, "y su cuenta"
    assert faena.eliminar(admin) and Proyecto.buscar(id_faena) is None

    # --- Datos de las APIs: se validan otra vez y se guardan (C, R y D, sin U)
    ahora = datetime(2025, 6, 2, 9, 30)

    def clima_de(**cambios) -> RegistroClima:
        datos = {"fecha_consulta": ahora, "ciudad": "Madrid, España",
                 "temperatura": 27.1, "humedad": 20, "viento": 0.8,
                 "estado": "nublado", "apto_terreno": True, **cambios}
        return RegistroClima(**datos)

    for malo in ({"humedad": 101}, {"humedad": -1}, {"temperatura": float("nan")},
                 {"viento": -3}, {"temperatura": True}, {"estado": "x\x1b[2J"},
                 {"ciudad": "  "}):
        assert _rechaza(lambda m=malo: clima_de(**m)), malo
    registro = clima_de()
    assert _rechaza(lambda: registro.guardar(tardio, basico), PermissionError)
    assert _rechaza(lambda: registro.guardar(Proyecto("P", "d", contrato, valpo, "CLP"),
                                             admin)), "proyecto sin guardar"
    id_clima = registro.guardar(tardio, admin)
    clima_de(fecha_consulta=ahora + timedelta(hours=3), temperatura=30.0).guardar(tardio, admin)
    copia_tardio = Proyecto.buscar(tardio.obtener_id())
    assert len(RegistroClima.listar(copia_tardio)) == 2
    assert "30.0 °C" in RegistroClima.ultimo(copia_tardio).obtener_resumen(), \
        "el último valor conocido es el más reciente"
    assert RegistroClima.buscar(id_clima).obtener_resumen() == registro.obtener_resumen()
    assert _rechaza(lambda: RegistroClima.buscar(id_clima).eliminar(basico), PermissionError)
    assert RegistroClima.buscar(id_clima).eliminar(admin)
    assert RegistroClima.buscar(id_clima) is None
    with conectar() as con:                          # la base repite la regla
        assert _rechaza(lambda: con.execute(
            "INSERT INTO registro_clima (proyecto_id, fecha_consulta, ciudad,"
            " temperatura, humedad, viento, estado, apto_terreno)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tardio.obtener_id(), ahora.isoformat(), "X", 20, 150, 1, "x", 1)),
            sqlite3.IntegrityError), "CHECK de humedad"

    for moneda, fecha, valor in (("JPY", hoy, 900), ("USD", hoy + timedelta(days=1), 900),
                                 ("USD", hoy, 0), ("USD", hoy, TIPO_CAMBIO_MAXIMO + 1),
                                 ("USD", hoy, float("inf")), ("CLP", hoy, 1)):
        assert _rechaza(lambda m=moneda, f=fecha, v=valor: TipoCambio(m, f, v)), \
            (moneda, valor)
    dolar = TipoCambio(" usd ", date(2025, 6, 2), 945.87)
    assert _rechaza(lambda: dolar.guardar(basico), PermissionError)
    assert dolar.guardar(admin), "un día nuevo se guarda"
    assert not TipoCambio("USD", date(2025, 6, 2), 950.0).guardar(admin), \
        "el mismo día no se repite (UNIQUE)"
    TipoCambio("USD", date(2025, 6, 3), 948.10).guardar(admin)
    TipoCambio("EUR", date(2025, 6, 3), 1081.49).guardar(admin)
    assert math.isclose(TipoCambio.ultimo("usd").obtener_valor(), 948.10), \
        "el último valor conocido es el de la fecha más reciente"
    assert len(TipoCambio.listar()) == 3
    assert _rechaza(lambda: TipoCambio.buscar(dolar.obtener_id()).eliminar(basico),
                    PermissionError)
    assert TipoCambio.buscar(dolar.obtener_id()).eliminar(admin)
    assert len(TipoCambio.listar()) == 2
    clima_de().guardar(tardio, admin)
    assert tardio.eliminar(admin) and RegistroClima.listar(copia_tardio) == [], \
        "borrar el proyecto borra su historial de clima (composición)"

    # --- El informe depende de la abstracción, no de cada clase concreta
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


if __name__ == "__main__":
    import tempfile

    original = os.getcwd()
    with tempfile.TemporaryDirectory() as carpeta:
        usar_base(os.path.join(carpeta, "autoverificacion.db"))
        os.chdir(carpeta)
        try:
            _autoverificar()
        finally:
            os.chdir(original)
    print("OK · dominio · seguridad · CRUD sobre Empleado y Departamento"
          " · proyectos y horas · historial de las APIs · inicio de sesión y bloqueo")
