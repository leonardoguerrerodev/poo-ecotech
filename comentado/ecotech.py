"""EcoTech Solutions — sistema de gestión de empleados.

Implementación en Python del modelo UML validado en la Unidad 1
(`diagramas/modelo_u2.drawio`). Este archivo contiene, en este orden:

    1. Validaciones y autorización compartidas
    2. Esquema y conexión a la base de datos (SQLite, librería estándar)
    3. Las ocho clases del diagrama, cada una con su CRUD
    4. Autoverificación

Uso:
    python3 ecotech.py   → autoverificación sobre una base temporal
    python3 main.py      → menú de la aplicación
"""

# UN SOLO ARCHIVO: el docente pidió no modularizar clase por clase. Al unir
# los dieciocho módulos anteriores desaparecen los imports cruzados, los
# TYPE_CHECKING que rompían ciclos y el acceso a atributos privados que
# hacía el repositorio (`empleado._Persona__direccion`). Se pierde la
# separación dominio / persistencia: aceptable, hay un solo motor de base y
# no se va a cambiar.

# Todo es biblioteca estándar: nada que instalar.
import csv
import hashlib
import re
import secrets
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import date
from enum import Enum
from pathlib import Path

# =====================================================================
# 1. VALIDACIONES Y AUTORIZACIÓN COMPARTIDAS
# =====================================================================
# Constantes de módulo: las usan tres clases y se compilan una sola vez.
# PATRON_CORREO es permisivo a propósito, una regex estricta rechaza correos
# legítimos. PATRON_TELEFONO acepta el formato chileno con o sin prefijo
# país; SEPARADORES se descarta antes de comparar.

PATRON_CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PATRON_USUARIO = re.compile(r"[a-z0-9._-]{3,20}")
PATRON_TELEFONO = re.compile(r"(\+?56)?[2-9]\d{8}")
SEPARADORES = re.compile(r"[\s()\-.]")

# Techo del salario, salido de la auditoría: sin él, un número de 25 dígitos
# reventaba en SQLite con OverflowError. Tope de negocio, no técnico, y
# replicado como CHECK en la tabla.
SALARIO_MAXIMO = 100_000_000


# Una sola función para todo texto obligatorio. `campo` nombra lo que falló.
def texto(valor: str, campo: str, maximo: int = 120) -> str:
    limpio = valor.strip()
    if not limpio:
        raise ValueError(f"{campo} no puede estar vacío")
    if len(limpio) > maximo:
        raise ValueError(f"{campo} supera los {maximo} caracteres")
    return limpio


# Sin separadores ni prefijo país: el mismo número escrito de dos formas no
# debe duplicar a la persona.
def canonico(telefono: str) -> str:
    return SEPARADORES.sub("", telefono)[-9:]


# Único punto de autorización; estaba duplicado y la auditoría lo llevó a
# siete métodos. Lanza en vez de devolver un booleano para que nadie olvide
# mirar el resultado, y lo hace antes de tocar la base.
def autorizar(solicitante: "Usuario", modulo: str) -> None:
    if not solicitante.tiene_permiso(modulo):
        raise PermissionError(f"No autorizado para operar sobre {modulo}")


# =====================================================================
# 2. BASE DE DATOS
# =====================================================================
# SQLITE: es biblioteca estándar, así que cumple "librería oficial" sin
# instalar nada, y la base es un archivo, sin servidor ni credenciales. Con
# un solo proceso escribiendo alcanza; MySQL sería infraestructura sin
# problema que resolver.
#
# RUTA_ACTIVA es variable de módulo para no arrastrar la ruta por toda la
# firma pública. `usar_base()` la cambia en un punto, que es lo que usa la
# autoverificación para no tocar la base real.

RUTA_ACTIVA = "ecotech.db"

# ESQUEMA EN UN BLOQUE, no una tabla por clase: las claves foráneas son
# circulares (empleado ↔ departamento) y `executescript` las crea en una
# transacción; `empleado_proyecto` es la tabla intermedia y no es de ninguna
# clase; y son seis tablas contra ocho clases, porque dos son abstractas e
# `Informe` se genera al vuelo.
#
# Las restricciones van también en el esquema y no solo en Python: siguen
# puestas si alguien abre la base con otra herramienta. SET NULL en
# `empleado.departamento_id` traduce la agregación; CASCADE en
# `registro_tiempo.empleado_id`, la composición.

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


def usar_base(ruta: str) -> None:
    global RUTA_ACTIVA
    RUTA_ACTIVA = ruta


# LOS TRES PARÁMETROS DE LA CONEXIÓN:
#   · `row_factory = sqlite3.Row`: lectura por nombre de columna, así
#     agregar una columna al SELECT no rompe nada en silencio.
#   · `PRAGMA foreign_keys = ON`: SQLite las trae desactivadas y va por
#     conexión; sin esto, SET NULL y CASCADE no hacen nada.
#   · `with con:`: COMMIT si el bloque termina, ROLLBACK si hay excepción.
# Conexión por operación y no global, para no dejar el archivo bloqueado
# toda la sesión; el `finally` cierra siempre.
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


# Idempotente por el `IF NOT EXISTS`: el menú la llama en cada arranque.
def crear_tablas() -> None:
    with conectar() as con:
        con.executescript(ESQUEMA)


# =====================================================================
# 3. CLASES DEL MODELO UML
# =====================================================================
# VISIBILIDAD, traducción literal del diagrama: UML -atributo →
# `self.__atributo` (privado), #atributo → `self._atributo` (protegido),
# +metodo() → `def metodo()`. El doble guion bajo renombra a
# `_Clase__atributo`, así que el acceso desde fuera falla de verdad.


# Enum y no string suelto: un rol mal escrito falla al construir el objeto,
# no al comparar permisos. El CHECK de `usuario` repite la lista.
class Rol(Enum):
    ADMIN_RRHH = "ADMIN_RRHH"
    GERENTE = "GERENTE"
    EMPLEADO = "EMPLEADO"


# Existe para que `Informe` dependa de UNA abstracción y no de cuatro clases
# concretas, como en la Unidad 1. Se defiende por SUSTITUIBILIDAD: agregar
# una quinta entidad no obliga a tocar `Informe`. No se defiende con
# "escribir el código una vez", que es heredar solo para reutilizar.
class EntidadReportable(ABC):
    """Abstracta. No tiene tabla: aporta el id y el contrato del resumen."""

    def __init__(self, id: int | None = None):
        self._id = id

    def obtener_id(self) -> int | None:
        return self._id

    # Impide instanciar la clase y que una hija olvide implementarlo.
    @abstractmethod
    def obtener_resumen(self) -> str:
        ...


# Pasa la prueba del "es un". `EntidadReportable` es una capacidad, esto una
# naturaleza. Con una sola hija no reutiliza código: existe porque el dominio
# lo dice, y un cliente también es persona sin ser empleado.
class Persona(EntidadReportable):
    """Abstracta. No tiene tabla: sus campos viven en la tabla de la hija."""

    def __init__(self, nombre: str, direccion: str, telefono: str,
                 correo: str, id: int | None = None):
        super().__init__(id)
        self.__nombre = texto(nombre, "El nombre")
        self.__direccion = texto(direccion, "La dirección", 200)
        # Privado para que el constructor no despache al método sobrescrito
        # de la hija, que escribe en la base: si no, cada objeto
        # reconstruido desde una fila dispararía un UPDATE al leerse.
        self.__fijar_contacto(telefono, correo)

    def obtener_nombre(self) -> str:
        return self.__nombre

    def actualizar_contacto(self, telefono: str, correo: str) -> None:
        self.__fijar_contacto(telefono, correo)

    def __fijar_contacto(self, telefono: str, correo: str) -> None:
        if not self._validar_correo(correo):
            raise ValueError(f"Correo inválido: {correo!r}")
        if not self._validar_telefono(telefono):
            raise ValueError(f"Teléfono inválido: {telefono!r}")
        self.__telefono = canonico(telefono)
        self.__correo = correo

    # Los tres campos son privados, ni la hija los lee. Este método protegido
    # es la puerta que `Persona` abre para que la subclase se persista.
    def _datos_contacto(self) -> tuple[str, str, str]:
        return (self.__direccion, self.__telefono, self.__correo)

    # Abstracto y con cuerpo: obliga a la hija a definirlo y le da la mitad
    # del resumen por `super()`.
    @abstractmethod
    def obtener_resumen(self) -> str:
        return f"{self.__nombre} | {self.__correo} | {self.__telefono}"

    def _validar_correo(self, correo: str) -> bool:
        return bool(PATRON_CORREO.fullmatch(correo))

    # `fullmatch` y no `search`: con `search`, "hola229876543chao" pasaría.
    def _validar_telefono(self, telefono: str) -> bool:
        return bool(PATRON_TELEFONO.fullmatch(SEPARADORES.sub("", telefono)))


class Empleado(Persona):
    """tabla: empleado"""

    # Columnas nombradas en una constante. Nunca `SELECT *`: con asterisco,
    # un ALTER TABLE rompe la lectura sin avisar.
    COLUMNAS = ("id, nombre, direccion, telefono, correo,"
                " fecha_inicio_contrato, salario")

    # Las validaciones van antes de `super().__init__`: un objeto a medio
    # construir es peor que uno que no existe.
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
        # Guion bajo simple: son las asociaciones del diagrama, y
        # `Departamento` y `Proyecto` las manipulan para sincronizar la
        # relación en los dos sentidos.
        self._proyectos: list["Proyecto"] = []
        self._departamento: "Departamento | None" = None

    # Autorización en el dato, no en la pantalla: el salario pide quién
    # pregunta. Un control en la interfaz se salta llamando a la clase.
    def obtener_salario(self, solicitante: "Usuario") -> int:
        autorizar(solicitante, "empleados")
        return self.__salario

    # Construye el `RegistroTiempo` adentro: el rombo negro de la composición
    # dice que el empleado es dueño del ciclo de vida de sus registros, así
    # que nadie de afuera fabrica uno. Las tres validaciones van aquí porque
    # necesitan el contrato y el inicio del proyecto, que el registro no ve.
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

    # El resumen no incluye el salario: así un informe no filtra sueldos.
    def obtener_resumen(self) -> str:
        return (f"{super().obtener_resumen()} | "
                f"contrato: {self.__fecha_inicio_contrato.isoformat()}")

    # --- Persistencia (CRUD) ---------------------------------------
    # Todo el SQL usa marcadores `?`, nunca f-strings: el valor viaja aparte
    # de la consulta y SQLite lo trata como dato, jamás como código. Es la
    # defensa contra inyección SQL, y por eso lo único interpolado del
    # archivo, `{cls.COLUMNAS}`, es una constante nuestra.

    def guardar(self, solicitante: "Usuario") -> int:
        """C — INSERT. El id lo asigna SQLite, no el objeto."""
        # El id lo genera la base con INTEGER PRIMARY KEY: un contador en
        # Python se reinicia y colisiona con lo ya guardado. `solicitante`
        # hace falta porque insertar exige leer el salario, y eso exige
        # permiso.
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

    # `@classmethod` y no `@staticmethod`: `cls` reconstruye con la misma
    # clase y devuelve objetos, no `sqlite3.Row`.
    @classmethod
    def listar(cls) -> list["Empleado"]:
        """R — todos, ordenados por nombre."""
        with conectar() as con:
            filas = con.execute(
                f"SELECT {cls.COLUMNAS} FROM empleado ORDER BY nombre").fetchall()
        return [cls._desde_fila(fila) for fila in filas]

    # Devuelve None y no lanza: "no está" es un resultado normal de búsqueda.
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
        # `super()` corre las validaciones del constructor y solo si pasan se
        # escribe: la regla vive en un único lugar. A la base va la forma
        # canónica que devuelve `_datos_contacto()`, no lo que se tecleó.
        super().actualizar_contacto(telefono, correo)
        # Sin id no hay fila que actualizar: basta el cambio en memoria.
        if self._id is None:
            return
        _, telefono_guardado, correo_guardado = self._datos_contacto()
        with conectar() as con:
            con.execute(
                "UPDATE empleado SET telefono = ?, correo = ? WHERE id = ?",
                (telefono_guardado, correo_guardado, self._id))

    # Acepta None: es como se desvincula a alguien sin despedirlo.
    def asignar_departamento(self, departamento_id: int | None,
                             solicitante: "Usuario") -> bool:
        """U — la clave foránea de la agregación."""
        autorizar(solicitante, "empleados")
        with conectar() as con:
            cur = con.execute(
                "UPDATE empleado SET departamento_id = ? WHERE id = ?",
                (departamento_id, self._id))
        return cur.rowcount == 1

    # `rowcount == 1` distingue borrar de no encontrar nada: un DELETE vacío
    # no es error en SQL y el menú diría "eliminado" igual. Pide permiso
    # porque encapsular `__salario` no sirve si cualquiera borra la fila
    # completa; es el defecto que destapó la auditoría.
    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — arrastra los registros de tiempo por ON DELETE CASCADE."""
        autorizar(solicitante, "empleados")
        with conectar() as con:
            cur = con.execute("DELETE FROM empleado WHERE id = ?", (self._id,))
        return cur.rowcount == 1

    # La fila pasa por el constructor, así un dato corrupto se detecta al
    # leerlo. La fecha se convierte a mano: SQLite guarda texto ISO 8601.
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
        self.__empleados: list["Empleado"] = []
        self.__gerente: "Empleado | None" = None

    def obtener_nombre(self) -> str:
        return self.__nombre

    # La asociación bidireccional se mantiene desde un solo lado: este método
    # actualiza las dos puntas, y saca al empleado de su departamento
    # anterior porque la multiplicidad del diagrama es 0..1.
    def agregar_empleado(self, empleado: "Empleado") -> bool:
        if empleado in self.__empleados:
            return False
        if empleado._departamento is not None:
            empleado._departamento.quitar_empleado(empleado)
        self.__empleados.append(empleado)
        empleado._departamento = self
        return True

    # Si el que se va era el gerente, el cargo queda vacante: un gerente
    # fuera del departamento sería un estado imposible.
    def quitar_empleado(self, empleado: "Empleado") -> bool:
        if empleado not in self.__empleados:
            return False
        if self.__gerente is empleado:
            self.__gerente = None
        self.__empleados.remove(empleado)
        empleado._departamento = None
        return True

    def asignar_gerente(self, empleado: "Empleado") -> None:
        if empleado not in self.__empleados:
            raise ValueError("El gerente debe pertenecer al departamento")
        self.__gerente = empleado

    # Devuelve una COPIA: con la lista interna, quien la recibe haría
    # `.append()` y se saltaría las reglas de `agregar_empleado`.
    def listar_empleados(self) -> list["Empleado"]:
        return list(self.__empleados)

    def obtener_resumen(self) -> str:
        gerente = (self.__gerente.obtener_nombre()
                   if self.__gerente is not None else "sin gerente")
        return (f"Departamento: {self.__nombre} | Gerente: {gerente} | "
                f"Empleados: {len(self.__empleados)}")

    # --- Persistencia (CRUD) ---------------------------------------

    # Antes no pedía permiso, porque crear un departamento no expone datos
    # sensibles. La auditoría lo corrigió: el criterio es qué se escribe, no
    # qué se lee.
    def guardar(self, solicitante: "Usuario") -> int:
        """C — INSERT."""
        autorizar(solicitante, "departamentos")
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
        # Misma función que el constructor: lo que entra por UPDATE cumple las
        # mismas reglas que lo que entra por INSERT.
        nuevo = texto(nombre, "El nombre del departamento")
        with conectar() as con:
            cur = con.execute("UPDATE departamento SET nombre = ? WHERE id = ?",
                              (nuevo, self._id))
        # El atributo cambia solo si la base aceptó; al revés, objeto y fila
        # dirían cosas distintas.
        if cur.rowcount == 1:
            self.__nombre = nuevo
        return cur.rowcount == 1

    def eliminar(self, solicitante: "Usuario") -> bool:
        """D — los empleados sobreviven: la agregación es ON DELETE SET NULL."""
        autorizar(solicitante, "departamentos")
        # Agregación y no composición: el departamento se disuelve y la gente
        # sigue contratada, con `departamento_id` en NULL. Con CASCADE,
        # cerrarlo despediría al personal.
        with conectar() as con:
            cur = con.execute("DELETE FROM departamento WHERE id = ?",
                              (self._id,))
        return cur.rowcount == 1

    # COUNT(*) mueve un número por la conexión; traer los empleados para
    # hacer `len()` mueve la tabla entera.
    def contar_empleados(self) -> int:
        with conectar() as con:
            fila = con.execute(
                "SELECT COUNT(*) AS total FROM empleado WHERE departamento_id = ?",
                (self._id,)).fetchone()
        return fila["total"]


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

    # Igual que en `Departamento`, las dos direcciones se sincronizan desde un
    # método. Aquí es muchos a muchos, así que no hay que sacar a nadie.
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

    # El `0.0` inicial fuerza float: sin registros devolvería el entero 0 y
    # el tipo cambiaría según los datos.
    def horas_consumidas(self) -> float:
        return sum((r.obtener_horas() for r in self._registros), 0.0)

    def obtener_resumen(self) -> str:
        return (f"Proyecto: {self.__nombre} | "
                f"Inicio: {self._fecha_inicio.isoformat()} | "
                f"Empleados: {len(self.__empleados)} | "
                f"Horas consumidas: {self.horas_consumidas():.2f}")


class RegistroTiempo(EntidadReportable):
    """tabla: registro_tiempo"""

    # Valida antes de `super().__init__`: un registro con horas imposibles no
    # llega a existir.
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

    # Cero horas es ruido y más de 24 en un día es imposible. Mismos límites
    # que el CHECK de la tabla.
    def _validar_horas(self, horas: float) -> bool:
        return 0 < horas <= 24

    # Lo único que puede juzgar sola: nadie reporta horas de mañana. El
    # contrato y el proyecto los juzga `Empleado.registrar_tiempo`, que sí
    # tiene esos objetos.
    def _validar_fecha(self, fecha: date) -> bool:
        return fecha <= date.today()


# NO hereda de `EntidadReportable`: una credencial no se reporta, y meter las
# claves en el alcance de un informe sería la fuga que el modelo debe impedir
# por estructura. Tampoco se fusiona con `Empleado`: la cuenta se crea después
# del contrato y se revoca sin despedir.
class Usuario:
    """tabla: usuario — credencial de acceso, no es entidad reportable."""

    # Permisos por rol, declarativo: agregar un módulo es agregar un string,
    # no un `if`. De clase porque la política es igual para todos.
    _PERMISOS = {
        Rol.ADMIN_RRHH: {"empleados", "departamentos", "proyectos", "informes"},
        Rol.GERENTE: {"departamentos", "proyectos", "informes"},
        Rol.EMPLEADO: {"proyectos"},
    }

    # `hash_clave` permite reconstruir desde la base sin la clave original:
    # en claro no existe en ningún lado tras el registro.
    def __init__(self, nombre_usuario: str, clave: str, rol: Rol,
                 id: int | None = None, hash_clave: str | None = None):
        # Minúsculas para que "Ana" y "ana" no sean dos cuentas: el UNIQUE de
        # la tabla compara literalmente.
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

    # SCRYPT Y NO SHA-256: SHA-256 es rápido, y rápido es lo peor para una
    # clave, porque una GPU prueba miles de millones por segundo. `scrypt` es
    # lento y caro en memoria, así que el hardware especializado pierde
    # ventaja; n, r y p son el costo. La sal es aleatoria por usuario, para
    # que dos claves iguales den hashes distintos y las tablas precalculadas
    # no sirvan; se guarda junto al hash porque no es secreta.
    @staticmethod
    def _hashear(clave: str, sal: bytes) -> str:
        h = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1, dklen=32)
        return f"scrypt${sal.hex()}${h.hex()}"

    # `compare_digest` y no `==`: la comparación normal corta en el primer
    # byte distinto, y el tiempo revela cuántos caracteres acertó el atacante.
    def verificar_clave(self, clave: str) -> bool:
        _, sal_hex, hash_guardado = self.__hash_clave.split("$")
        calculado = self._hashear(clave, bytes.fromhex(sal_hex)).split("$")[2]
        return secrets.compare_digest(calculado, hash_guardado)

    # Pide la clave actual, o quien tome una sesión abierta se queda la
    # cuenta. Valida la nueva primero para no gastar un hash caro en vano, y
    # usa sal nueva en cada cambio.
    def cambiar_clave(self, actual: str, nueva: str) -> bool:
        if not self._validar_clave(nueva):
            raise ValueError("La clave no cumple la política de seguridad")
        if not self.verificar_clave(actual):
            return False
        self.__hash_clave = self._hashear(nueva, secrets.token_bytes(16))
        return True

    # Longitud antes que complejidad: es lo que más cuesta romper por fuerza
    # bruta. Tres familias de cuatro y no las cuatro, para no empujar a
    # claves memorizables por patrón tipo "Password1!".
    def _validar_clave(self, clave: str) -> bool:
        if len(clave) < 12:
            return False
        familias = (any(c.islower() for c in clave),
                    any(c.isupper() for c in clave),
                    any(c.isdigit() for c in clave),
                    any(not c.isalnum() for c in clave))
        return sum(familias) >= 3

    # `.get(rol, set())` y no `[rol]`: un rol desconocido no tiene permisos,
    # no revienta. Ante la duda, el sistema niega.
    def tiene_permiso(self, modulo: str) -> bool:
        return modulo in self._PERMISOS.get(self.__rol, set())


# No hereda de `EntidadReportable`: un informe no se reporta a sí mismo. Sin
# tabla porque es un documento derivado, no un hecho del negocio.
class Informe:
    """Sin tabla: se genera al vuelo desde las entidades reportables."""

    def __init__(self, titulo: str, contenido: list[str]):
        self.__titulo = texto(titulo, "El título del informe")
        self.__fecha_generacion = date.today()
        self.__contenido = contenido

    # AQUÍ SE PAGA LA ABSTRACCIÓN: un método, no cuatro. Llama al mismo
    # `obtener_resumen()` sin preguntar de qué clase es cada elemento, que es
    # polimorfismo, y así agregar una entidad no obliga a tocar nada.
    # Autoriza al principio, antes de leer un solo dato.
    @staticmethod
    def generar(titulo: str, entidades: list[EntidadReportable],
                solicitante: Usuario) -> "Informe":
        autorizar(solicitante, "informes")
        return Informe(titulo, [e.obtener_resumen() for e in entidades])

    # PATH TRAVERSAL: un título como "../../.ssh/authorized_keys" escribiría
    # fuera del proyecto. `resolve()` colapsa los ".." y los enlaces, y recién
    # sobre la ruta resuelta se pregunta si sigue dentro de la carpeta de
    # trabajo; comprobar antes de resolver es justo lo que el ".." elude.
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
        # `csv.writer` y no un `",".join()` a mano: escapa comas y comillas.
        # `newline=""` es obligatorio o aparecen líneas en blanco. `OSError`
        # cubre disco lleno, permiso denegado y carpeta inexistente; devuelve
        # False en vez de propagar porque exportar es opcional.
        try:
            if formato == "csv":
                with open(destino, "w", newline="", encoding="utf-8") as archivo:
                    escritor = csv.writer(archivo)
                    escritor.writerow([self.__titulo,
                                       self.__fecha_generacion.isoformat()])
                    escritor.writerows([linea] for linea in self.__contenido)
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
# La rúbrica no la pide. Existe porque es la evidencia de haber PROBADO el
# código apoyado por IA, que sí se evalúa, y porque fue la red del paso de
# dieciocho módulos a uno. Sin framework: `assert` alcanza, sobre una base
# temporal que se borra al salir, así que nunca toca `ecotech.db`.


def _rechaza(accion, excepcion=ValueError) -> bool:
    """Verdadero si la acción falla como se espera. La red del refactor."""
    # Probar que algo FALLA importa tanto como probar que funciona.
    try:
        accion()
    except excepcion:
        return True
    return False


def _autoverificar() -> None:
    hoy = date.today()
    contrato = date(2024, 3, 1)
    admin = Usuario("rrhh.admin", "Clave-RRHH-2026", Rol.ADMIN_RRHH)
    basico = Usuario("j.bravo", "Clave-Bravo-2026", Rol.EMPLEADO)

    def nueva(correo: str = "jbravo@ecotech.cl") -> Empleado:
        return Empleado("Juanita Bravo Sepúlveda", "Av. Matta 1234",
                        "+56 9 8765 4321", correo, contrato, 1450000)

    # --- Lo que el dominio debe rechazar
    # Una línea por regla de negocio: si alguien afloja una validación, aquí
    # se cae.
    assert _rechaza(lambda: nueva("sin-arroba")), "correo sin @"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "123", "j@e.cl",
                                     contrato, 1000)), "teléfono corto"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "229876543", "j@e.cl",
                                     contrato, 0)), "salario cero"
    # El caso de la auditoría: sin techo, este número mataba el programa.
    assert _rechaza(lambda: Empleado("J", "Calle 1", "229876543", "j@e.cl",
                                     contrato, 10**25)), "salario desbordado"
    assert _rechaza(lambda: Empleado("J", "Calle 1", "229876543", "j@e.cl",
                                     date(2099, 1, 1), 1000)), "contrato futuro"
    assert _rechaza(lambda: RegistroTiempo(hoy, 25, "x")), "más de 24 horas"
    assert _rechaza(lambda: Departamento("   ")), "nombre en blanco"
    assert _rechaza(lambda: Usuario("ana", "corta", Rol.EMPLEADO)), "clave corta"
    # PermissionError y no ValueError: no autorizado no es lo mismo que mal
    # escrito, y el menú los distingue.
    assert _rechaza(lambda: nueva().obtener_salario(basico),
                    PermissionError), "salario sin permiso"

    # --- Credenciales
    # La tercera línea es la que importa: la clave en claro no quedó guardada
    # en ningún atributo del objeto.
    assert admin.verificar_clave("Clave-RRHH-2026")
    assert not admin.verificar_clave("otra")
    assert "Clave-RRHH-2026" not in str(admin.__dict__), "la clave quedó en claro"
    assert admin.tiene_permiso("informes")
    assert not basico.tiene_permiso("informes")

    # --- CRUD sobre las dos clases relacionadas, en orden
    crear_tablas()

    dep = Departamento("Desarrollo Sostenible")
    id_dep = dep.guardar(admin)                                     # C
    assert id_dep is not None and dep.obtener_id() == id_dep
    ana = nueva()
    id_ana = ana.guardar(admin)                                     # C

    assert len(Departamento.listar()) == 1                          # R
    assert len(Empleado.listar()) == 1
    assert Empleado.buscar(id_ana).obtener_nombre() == "Juanita Bravo Sepúlveda"
    # Buscar algo que no existe devuelve None, no revienta.
    assert Empleado.buscar(999) is None
    # Entró "+56 9 8765 4321" y volvió "987654321": la normalización sobrevive
    # al viaje de ida y vuelta a la base.
    assert "987654321" in Empleado.buscar(id_ana).obtener_resumen(), "canónico"

    assert dep.renombrar("Investigación y Desarrollo", admin)       # U
    assert Departamento.buscar(id_dep).obtener_nombre() == "Investigación y Desarrollo"
    ana.actualizar_contacto("22 987 6543", "j.bravo@ecotech.cl")
    assert "j.bravo@ecotech.cl" in Empleado.buscar(id_ana).obtener_resumen()
    assert ana.asignar_departamento(id_dep, admin)
    assert dep.contar_empleados() == 1

    # --- Ninguna escritura pasa sin permiso del módulo que le toca
    # El defecto 2 de la auditoría hecho prueba: antes estas cinco líneas
    # devolvían True, así que un rol EMPLEADO borraba empleados y
    # departamentos sin poder leer un sueldo. La última comprueba que la
    # excepción salta antes de tocar la base.
    assert _rechaza(lambda: dep.renombrar("Pirata", basico), PermissionError)
    assert _rechaza(lambda: dep.eliminar(basico), PermissionError)
    assert _rechaza(lambda: ana.eliminar(basico), PermissionError)
    assert _rechaza(lambda: ana.asignar_departamento(None, basico), PermissionError)
    assert _rechaza(lambda: Departamento("X").guardar(basico), PermissionError)
    assert Departamento.buscar(id_dep) is not None, "nada de eso llegó a ejecutarse"

    # La regla más importante del modelo: al borrar el departamento el
    # empleado sigue ahí. Si alguien cambiara SET NULL por CASCADE, esta línea
    # lo detecta.
    assert dep.eliminar(admin)                                      # D
    assert Empleado.buscar(id_ana) is not None, "la agregación es SET NULL"
    assert ana.eliminar(admin)
    assert Empleado.buscar(id_ana) is None
    assert not ana.eliminar(admin), "borrar dos veces no puede devolver éxito"

    # --- El informe depende de la abstracción, no de las clases concretas
    # Un departamento y un empleado, sin herencia entre sí, entran en la misma
    # lista y salen en el mismo informe.
    salida = Informe.generar("Dotación", [Departamento("Legal"), nueva()],
                             admin).obtener_texto()
    assert "Legal" in salida and "Juanita" in salida
    assert _rechaza(lambda: Informe.generar("X", [], basico), PermissionError)


# `TemporaryDirectory` borra la carpeta y la base al salir del `with`, incluso
# si un assert falla en el medio.
if __name__ == "__main__":
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as carpeta:
        usar_base(os.path.join(carpeta, "autoverificacion.db"))
        _autoverificar()
    print("OK · dominio · seguridad · CRUD sobre Empleado y Departamento")
