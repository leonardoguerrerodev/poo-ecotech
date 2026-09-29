"""
Prueba de la apelación de la ES2.

Cada bloque toma una afirmación de la corrección, intenta hacer justo lo que
dice que se puede hacer, y muestra lo que pasa de verdad.

No modifica el código evaluado: solo lo importa. No usa internet (las APIs se
simulan) y no toca ecotech.db (usa una base temporal que se borra al final).

    python3 apelacion/prueba_apelacion.py
"""

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import requests                                         # noqa: E402
import ecotech                                          # noqa: E402
import main                                             # noqa: E402
from ecotech import (Empleado, Proyecto, RegistroClima, Rol,  # noqa: E402
                     TipoCambio, Usuario)
from servicios import ServicioExterno, ServicioNoDisponible  # noqa: E402

COMMIT_EVALUADO = "36f94ac5b6292a9c20a2957217c5226a90ca4eb9"
ARCHIVOS_EVALUADOS = ["ecotech.py", "main.py", "servicios.py", "docs/ANALISIS_IA.md"]
CONTRATO = date(2024, 1, 1)


def afirmacion(indicador: str, texto: str) -> None:
    print(f"\n{indicador} · \"{texto}\"")


def resultado(ok: bool, detalle: str) -> None:
    print(f"   {'OK' if ok else 'FALLA'}  {detalle}")
    assert ok, detalle


def lanza(tipo, accion) -> str:
    """El mensaje del error si la acción lanza `tipo`; si no lanza, falla."""
    try:
        accion()
    except tipo as error:
        return str(error)
    raise AssertionError(f"se esperaba {tipo.__name__} y no hubo error")


def respuesta(estado: int, cuerpo=None) -> mock.Mock:
    return mock.Mock(status_code=estado, json=mock.Mock(return_value=cuerpo or {}))


def codigo_evaluado() -> str:
    """Compara los archivos citados con el commit evaluado, si git está a mano."""
    try:
        subprocess.run(["git", "cat-file", "-e", COMMIT_EVALUADO], cwd=RAIZ,
                       check=True, capture_output=True)
        igual = subprocess.run(["git", "diff", "--quiet", COMMIT_EVALUADO, "--",
                                *ARCHIVOS_EVALUADOS], cwd=RAIZ).returncode == 0
    except (OSError, subprocess.CalledProcessError):
        return "no comprobado (sin git o sin el historial)"
    assert igual, "los archivos citados no son los del commit evaluado"
    return "idéntico al commit evaluado 36f94ac"


def probar_g14() -> None:
    afirmacion("2.1.4.G.14", "un objeto construido por código puede quedar en estado inválido")
    casos = [
        ("teléfono '123'", lambda: Empleado("Juan", "Calle 1", "123", "juan@eco.cl", CONTRATO, 1000)),
        ("correo sin @", lambda: Empleado("Juan", "Calle 1", "229876543", "juan.eco.cl", CONTRATO, 1000)),
        ("nombre vacío", lambda: Empleado("", "Calle 1", "229876543", "juan@eco.cl", CONTRATO, 1000)),
        ("salario 0", lambda: Empleado("Juan", "Calle 1", "229876543", "juan@eco.cl", CONTRATO, 0)),
        ("contrato en 2099", lambda: Empleado("Juan", "Calle 1", "229876543", "juan@eco.cl", date(2099, 1, 1), 1000)),
        ("departamento sin nombre", lambda: ecotech.Departamento("   ")),
        ("proyecto con moneda inventada", lambda: Proyecto("P", "D", CONTRATO, "Santiago", "BTC")),
    ]
    for nombre, crear in casos:
        mensaje = lanza(ValueError, crear)
        resultado(True, f"{nombre}, sin menú: la clase lanza ValueError ({mensaje}) y el objeto no se crea")

    afirmacion("2.1.4.G.14", "y la base de datos lo acepta")
    with ecotech.conectar() as con:
        mensaje = lanza(sqlite3.IntegrityError, lambda: con.execute(
            "INSERT INTO empleado (nombre, direccion, telefono, correo,"
            " fecha_inicio_contrato, salario) VALUES (?, ?, ?, ?, ?, ?)",
            ("Juan", "Calle 1", "229876543", "juan@eco.cl", "2024-01-01", 0)))
    resultado(True, f"INSERT directo con salario 0, sin pasar por la clase: la base lo rechaza ({mensaje})")


def probar_i6() -> None:
    afirmacion("3.1.2.I.6", "sin saneamiento explícito de los parámetros que viajan a las APIs")
    for etiqueta, ciudad in (("'Santiago<script>'", "Santiago<script>"),
                             ("\"'; DROP TABLE x;--\"", "'; DROP TABLE x;--"),
                             ("con escape de terminal", "Santiago\x1b[2J"),
                             ("de 81 letras", "a" * 81), ("'123'", "123")):
        with mock.patch.object(requests, "get") as api:
            lanza(ValueError, lambda: ServicioExterno().obtener_clima(ciudad))
        resultado(not api.called, f"ciudad {etiqueta}: ValueError antes de la red; la API se llamó {api.call_count} veces")

    with mock.patch.object(requests, "get", return_value=respuesta(200, {"results": []})) as api:
        lanza(ValueError, lambda: ServicioExterno().obtener_clima("  Puerto Montt  "))
    enviado = api.call_args.kwargs["params"]["name"]
    resultado(enviado == "Puerto Montt",
              f"ciudad '  Puerto Montt  ': viaja limpia ({enviado!r}) y dentro de params, que requests codifica")

    with mock.patch.object(requests, "get") as api:
        lanza(ValueError, lambda: ServicioExterno().obtener_tipo_cambio("BTC"))
    resultado(not api.called, "moneda 'BTC': ValueError antes de la red; la API no se llamó")

    with mock.patch.object(requests, "get", return_value=respuesta(404)) as api:
        lanza(ServicioNoDisponible, lambda: ServicioExterno().obtener_tipo_cambio(" usd "))
    url = api.call_args.args[0]
    resultado(url.endswith("/dolar"),
              f"moneda ' usd ': lo que escribió el usuario no viaja; a la API va un código fijo ({url})")

    falsa = respuesta(200, {"results": [{"latitude": 999, "longitude": 0}]})
    with mock.patch.object(requests, "get", return_value=falsa) as api:
        lanza(ServicioNoDisponible, lambda: ServicioExterno().obtener_clima("Santiago"))
    resultado(api.call_count == 1,
              "latitud 999 recibida de la primera API: se rechaza y no viaja a la segunda "
              f"(llamadas: {api.call_count})")

    with mock.patch.dict(os.environ, {"ECOTECH_URL_INDICADORES": "http://mindicador.cl/api"}), \
            mock.patch.object(requests, "get") as api:
        mensaje = lanza(ServicioNoDisponible, lambda: ServicioExterno().obtener_tipo_cambio("USD"))
    resultado(not api.called, f"URL http en el .env: se rechaza sin conectarse ({mensaje[:55]}...)")

    mensaje = lanza(ValueError, lambda: Proyecto("P", "D", CONTRATO, "", "CLP"))
    resultado(True, f"ciudad vacía en Proyecto: la clase la rechaza antes de guardarla ({mensaje})")


def probar_i8() -> None:
    empleado = Usuario("empleado1", "", Rol.EMPLEADO, hash_clave="x", empleado_id=1)
    gerente = Usuario("gerente1", "", Rol.GERENTE, hash_clave="x")

    afirmacion("3.1.2.I.8", "El consumo de las APIs no restringe por rol")
    for opcion, quien, rol in (("11", empleado, "EMPLEADO"), ("21", empleado, "EMPLEADO"),
                               ("12", gerente, "GERENTE")):
        with mock.patch.object(requests, "get") as api, \
                mock.patch("builtins.input") as teclado:
            mensaje = lanza(PermissionError, lambda: main.ejecutar(opcion, quien))
        resultado(not api.called and not teclado.called,
                  f"opción {opcion} con rol {rol}: PermissionError ({mensaje}); "
                  f"datos pedidos: {teclado.call_count}, llamadas a la API: {api.call_count}")

    registro = RegistroClima(datetime.now(), "Santiago", 18.0, 50, 10.0, "despejado", True)
    mensaje = lanza(PermissionError, lambda: registro.guardar(None, empleado))
    resultado(True, f"RegistroClima.guardar() con rol EMPLEADO: la clase lo rechaza ({mensaje})")
    mensaje = lanza(PermissionError, lambda: TipoCambio("USD", CONTRATO, 950.0).guardar(empleado))
    resultado(True, f"TipoCambio.guardar() con rol EMPLEADO: la clase lo rechaza ({mensaje})")

    afirmacion("3.1.2.I.8", "ni por sesión")
    Usuario("admin", "Clave.Segura.2026", Rol.ADMIN_RRHH).guardar()
    resultado(Usuario.autenticar("admin", "otra-clave") is None,
              "login con clave equivocada: autenticar() devuelve None, no hay sesión")
    resultado(Usuario.autenticar("admin", "Clave.Segura.2026") is not None,
              "login con la clave correcta: autenticar() entrega el usuario de la sesión")
    print("   (que el menú solo se abre con ese usuario y se cierra por inactividad se ve en "
          "main.py L704 y L681; no se simula aquí)")


def probar_i11() -> None:
    afirmacion("3.1.3.I.11", "no distingue 404 de 500 ni informa el código al usuario")
    mensajes = {}
    for estado in (400, 404, 429, 500, 503, 418):
        with mock.patch.object(requests, "get", return_value=respuesta(estado)):
            mensajes[estado] = lanza(ServicioNoDisponible,
                                     lambda: ServicioExterno().obtener_tipo_cambio("USD"))
        resultado(f"({estado})" in mensajes[estado], f"respuesta {estado}: \"{mensajes[estado]}\"")
    resultado(len({mensajes[400], mensajes[404], mensajes[429], mensajes[500]}) == 4,
              "400, 404, 429 y 500 dan cuatro mensajes distintos, y cada uno trae su código")


def probar_i16() -> None:
    afirmacion("3.1.4.I.16", "no se declara ningún fragmento descartado")
    lineas = (RAIZ / "docs" / "ANALISIS_IA.md").read_text(encoding="utf-8").splitlines()
    inicio_u3 = next(i for i, linea in enumerate(lineas) if linea.startswith("## 4."))
    filas = [(i, re.match(r"\| (\d+) \|", linea).group(1)) for i, linea in enumerate(lineas)
             if re.match(r"\| \d+ \|.*\| \*\*Descartar", linea)]
    u2 = [n for i, n in filas if i < inicio_u3]
    u3 = [n for i, n in filas if i > inicio_u3]
    resultado(len(u3) > 0, f"Unidad 3: {len(u3)} fragmentos marcados Descartar (filas {', '.join(u3)})")
    resultado(len(u2) > 0, f"Unidad 2: {len(u2)} fragmentos marcados Descartar (filas {', '.join(u2)})")


def main_prueba() -> None:
    print("Prueba de la apelación")
    print(f"Código probado: {codigo_evaluado()}")
    with tempfile.TemporaryDirectory() as carpeta:
        ecotech.usar_base(str(Path(carpeta) / "apelacion.db"))
        ecotech.crear_tablas()
        probar_g14()
        probar_i6()
        probar_i8()
        probar_i11()
        probar_i16()
    print("\nLas cinco afirmaciones revisadas: en ninguna el código se comporta como dice la corrección.")


if __name__ == "__main__":
    main_prueba()
