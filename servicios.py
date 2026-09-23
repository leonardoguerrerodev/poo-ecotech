"""EcoTech Solutions — servicios externos (Unidad 3).

Frontera del sistema con la red: el clima de una ciudad (Open-Meteo) y el
tipo de cambio del día (mindicador.cl). Ninguna de las dos APIs pide llave.
Las direcciones y el tiempo de espera se pueden cambiar por variables de
entorno o con un archivo .env junto a este (ver .env.example).
No importa nada de `ecotech.py`: es `main.py` quien une los datos de la base
con los de la red, así que este archivo cambia solo cuando cambia una API.

Uso:
    python3 servicios.py   → autoverificación sin red, con respuestas simuladas
"""

import math                                 # rechaza un tipo de cambio infinito o NaN
import os                                   # configuración por variables de entorno
import re                                   # patrón de nombres de ciudad
from pathlib import Path                    # ubica el .env junto a este archivo

import requests                             # HTTP: timeouts, códigos de estado y JSON


class ServicioNoDisponible(Exception):
    """Falla de un servicio externo, con un mensaje apto para el usuario."""


PATRON_CIUDAD = re.compile(r"[^\W\d_]+(?:[ '.-][^\W\d_]+)*")

URL_GEOCODIFICACION = "https://geocoding-api.open-meteo.com/v1/search"
URL_CLIMA = "https://api.open-meteo.com/v1/forecast"
URL_INDICADORES = "https://mindicador.cl/api"
TIEMPO_CONEXION = 3.05                      # segundos para conectar
TIEMPO_LECTURA = 10                         # segundos para leer; ECOTECH_TIEMPO_ESPERA lo cambia
TIEMPO_LECTURA_MAXIMO = 60
RUTA_ENV = Path(__file__).with_name(".env")

# Códigos WMO del clima: cada tramo termina en el código indicado.
ESTADOS = ((0, "despejado"), (3, "nublado"), (48, "niebla"), (57, "llovizna"),
           (67, "lluvia"), (77, "nieve"), (82, "chubascos"),
           (86, "chubascos de nieve"), (99, "tormenta"))
PRIMERA_PRECIPITACION = 51
VIENTO_MAXIMO_TERRENO = 40                  # km/h
TIPO_CAMBIO_MAXIMO = 1_000_000             # CLP por unidad: más que eso es un dato roto

FORMATO_INESPERADO = "El servicio externo respondió con un formato inesperado."
CONFIGURACION_INVALIDA = ("La configuración del servicio externo no es válida: se exige "
                          "https y un tiempo de espera de 0 a 60 segundos. Revise el .env.")
MENSAJES_HTTP = {
    400: "El servicio externo rechazó la consulta (400).",
    404: "El servicio externo no encontró el recurso pedido (404).",
    429: "Demasiadas consultas al servicio externo: espere un momento (429).",
}


def _cargar_env(ruta: Path = RUTA_ENV) -> None:
    """Carga CLAVE=VALOR desde un .env, si existe. Las variables reales ganan."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


_cargar_env()


class ServicioExterno:
    """«boundary» — única puerta del sistema hacia la red."""

    MONEDAS = {"USD": "dolar", "EUR": "euro", "UF": "uf"}

    def __init__(self):
        entorno = os.environ.get
        self.__url_geocodificacion = entorno("ECOTECH_URL_GEOCODIFICACION",
                                             URL_GEOCODIFICACION)
        self.__url_clima = entorno("ECOTECH_URL_CLIMA", URL_CLIMA)
        self.__url_indicadores = entorno("ECOTECH_URL_INDICADORES",
                                         URL_INDICADORES).rstrip("/")
        try:
            self.__tiempo_espera = float(entorno("ECOTECH_TIEMPO_ESPERA",
                                                 TIEMPO_LECTURA))
        except ValueError:
            self.__tiempo_espera = None     # se rechaza al consultar: falla cerrado

    def obtener_clima(self, ciudad: str) -> dict:
        if not self._validar_ciudad(ciudad):
            raise ValueError("Ciudad inválida: de 2 a 80 letras, con espacios, "
                             "guion, punto o apóstrofo")
        ciudad = ciudad.strip()
        lugares = self.__consultar(self.__url_geocodificacion, {
            "name": ciudad, "count": 1, "language": "es"}).get("results")
        if not lugares:
            raise ValueError(f"No se encontró la ciudad {ciudad!r}")
        try:
            lugar = lugares[0]
            actual = self.__consultar(self.__url_clima, {
                "latitude": lugar["latitude"], "longitude": lugar["longitude"],
                "current": "temperature_2m,relative_humidity_2m,"
                           "weather_code,wind_speed_10m",
                "timezone": "auto"})["current"]
            medidas = {clave: actual[clave] for clave in (
                "temperature_2m", "relative_humidity_2m", "weather_code",
                "wind_speed_10m")}
        except (KeyError, TypeError, IndexError):
            raise ServicioNoDisponible(FORMATO_INESPERADO) from None
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   for v in medidas.values()):
            raise ServicioNoDisponible(FORMATO_INESPERADO)

        # El nombre viene de la red y se va a imprimir en la terminal: si
        # trae caracteres de control, se usa el que escribió el usuario.
        nombre = f"{lugar.get('name')}, {lugar.get('country')}"
        if len(nombre) > 120 or not nombre.isprintable():
            nombre = ciudad
        codigo = medidas["weather_code"]
        viento = medidas["wind_speed_10m"]
        return {
            "ciudad": nombre,
            "temperatura": medidas["temperature_2m"],
            "humedad": medidas["relative_humidity_2m"],
            "viento": viento,
            "estado": next((texto for tope, texto in ESTADOS if codigo <= tope),
                           "desconocido"),
            "apto_terreno": (codigo < PRIMERA_PRECIPITACION
                             and viento < VIENTO_MAXIMO_TERRENO),
        }

    def obtener_tipo_cambio(self, moneda: str) -> float:
        """Pesos chilenos por unidad de la moneda. Solo monedas de la lista."""
        codigo = self.MONEDAS.get(moneda.strip().upper())
        if codigo is None:
            raise ValueError("Moneda no soportada. Use: "
                             + ", ".join(self.MONEDAS))
        return self.__extraer_valor(
            self.__consultar(f"{self.__url_indicadores}/{codigo}"))

    def __extraer_valor(self, datos: dict) -> float:
        """Valida la respuesta del indicador antes de usarla: presencia, tipo y rango."""
        try:
            valor = datos["serie"][0]["valor"]
        except (KeyError, TypeError, IndexError):
            raise ServicioNoDisponible(FORMATO_INESPERADO) from None
        if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                or not math.isfinite(valor) or not 0 < valor <= TIPO_CAMBIO_MAXIMO):
            raise ServicioNoDisponible(FORMATO_INESPERADO)
        return float(valor)

    def __consultar(self, url: str, params: dict | None = None) -> dict:
        """GET con tiempo de espera. Toda falla sale como ServicioNoDisponible,
        con un mensaje que no muestra la URL, la traza ni el detalle interno."""
        if (not url.startswith("https://") or self.__tiempo_espera is None
                or not 0 < self.__tiempo_espera <= TIEMPO_LECTURA_MAXIMO):
            raise ServicioNoDisponible(CONFIGURACION_INVALIDA)
        try:
            respuesta = requests.get(url, params=params,
                                     timeout=(TIEMPO_CONEXION, self.__tiempo_espera))
        except requests.Timeout:
            raise ServicioNoDisponible(
                "El servicio externo no respondió a tiempo. Intente más tarde."
            ) from None
        except requests.ConnectionError:
            raise ServicioNoDisponible(
                "No hay conexión con el servicio externo. Revise la red."
            ) from None
        except requests.RequestException:
            raise ServicioNoDisponible(
                "No se pudo completar la consulta al servicio externo.") from None

        estado = respuesta.status_code
        if estado != 200:
            if estado >= 500:
                raise ServicioNoDisponible(
                    f"El servicio externo tiene una falla interna ({estado}). "
                    "Intente más tarde.")
            raise ServicioNoDisponible(MENSAJES_HTTP.get(
                estado, f"Respuesta inesperada del servicio externo ({estado})."))
        try:
            datos = respuesta.json()
        except ValueError:                  # requests.JSONDecodeError hereda de ValueError
            raise ServicioNoDisponible(
                "El servicio externo respondió algo que no es JSON válido."
            ) from None
        if not isinstance(datos, dict):
            raise ServicioNoDisponible(FORMATO_INESPERADO)
        return datos

    def _validar_ciudad(self, ciudad: str) -> bool:
        limpia = ciudad.strip()
        return 2 <= len(limpia) <= 80 and bool(PATRON_CIUDAD.fullmatch(limpia))


# =====================================================================
# AUTOVERIFICACIÓN — sin red: requests.get se reemplaza por respuestas falsas
# =====================================================================


def _autoverificar() -> None:
    import tempfile
    from unittest import mock

    limpio = {k: v for k, v in os.environ.items() if not k.startswith("ECOTECH_")}

    def configurado(**variables):
        with mock.patch.dict(os.environ, {**limpio, **variables}, clear=True):
            return ServicioExterno()

    servicio = configurado()
    valpo = "Valparaíso"
    geo = {"results": [{"name": valpo, "country": "Chile",
                        "latitude": -33.04, "longitude": -71.63}]}

    def clima(codigo=0, viento=10.0, temperatura=18.4):
        return {"current": {"temperature_2m": temperatura,
                            "relative_humidity_2m": 54,
                            "weather_code": codigo, "wind_speed_10m": viento}}

    def responde(*cuerpos, estado=200):
        falsas = [mock.Mock(status_code=estado, json=mock.Mock(return_value=c))
                  for c in cuerpos]
        return mock.patch.object(requests, "get", side_effect=falsas)

    def falla(accion, excepcion=ServicioNoDisponible, contiene=""):
        try:
            accion()
        except excepcion as error:
            return contiene in str(error)
        return False

    # --- Respuestas correctas: se extrae solo lo que el sistema usa
    with responde(geo, clima()) as get:
        datos = servicio.obtener_clima("  Valparaíso ")
    assert datos["ciudad"] == "Valparaíso, Chile" and math.isclose(datos["temperatura"], 18.4)
    assert datos["estado"] == "despejado" and datos["apto_terreno"]
    assert get.call_args.kwargs["timeout"] == (TIEMPO_CONEXION, TIEMPO_LECTURA), \
        "toda solicitud lleva tiempo de espera"
    assert all(llamada.args[0].startswith("https://")
               for llamada in get.call_args_list), "solo HTTPS"
    with responde(geo, clima(codigo=63)):
        assert not servicio.obtener_clima(valpo)["apto_terreno"], "lluvia"
    with responde(geo, clima(viento=55.0)):
        assert not servicio.obtener_clima(valpo)["apto_terreno"], "viento"
    with responde({"serie": [{"fecha": "2026-09-21", "valor": 958.42}]}) as get:
        assert math.isclose(servicio.obtener_tipo_cambio("usd"), 958.42)
    assert get.call_args.args[0] == "https://mindicador.cl/api/dolar"

    # --- Entradas que no deben salir a la red
    with mock.patch.object(requests, "get") as get:
        for ciudad in ("", "   ", "a", "Santiago\x1b[2J", "x" * 500,
                       "Santiago; DROP", "../../etc", "Santiago\u202e"):
            assert falla(lambda c=ciudad: servicio.obtener_clima(c), ValueError), ciudad
        for moneda in ("JPY", "../dolar", "", "dolar"):
            assert falla(lambda m=moneda: servicio.obtener_tipo_cambio(m),
                         ValueError), moneda
        get.assert_not_called()
    assert servicio._validar_ciudad("San Pedro de Atacama")
    assert servicio._validar_ciudad("Viña del Mar")

    # --- Red: tiempo de espera, sin conexión y otros errores de requests
    for excepcion, texto in ((requests.ConnectTimeout, "a tiempo"),
                             (requests.ReadTimeout, "a tiempo"),
                             (requests.ConnectionError, "conexión"),
                             (requests.TooManyRedirects, "No se pudo")):
        with mock.patch.object(requests, "get", side_effect=excepcion("detalle")):
            assert falla(lambda: servicio.obtener_tipo_cambio("USD"),
                         contiene=texto), excepcion
            assert not falla(lambda: servicio.obtener_tipo_cambio("USD"),
                             contiene="detalle"), "el detalle interno no se muestra"

    # --- Códigos HTTP distintos de 200
    for estado, texto in ((400, "400"), (404, "404"), (429, "429"),
                          (500, "falla interna"), (503, "503"), (302, "302")):
        with responde({}, estado=estado):
            assert falla(lambda: servicio.obtener_tipo_cambio("EUR"),
                         contiene=texto), estado

    # --- Cuerpos que no son lo que se esperaba
    no_json = mock.Mock(status_code=200, json=mock.Mock(
        side_effect=requests.JSONDecodeError("x", "<html>", 0)))
    with mock.patch.object(requests, "get", return_value=no_json):
        assert falla(lambda: servicio.obtener_tipo_cambio("UF"), contiene="JSON")
    for cuerpo in ([1, 2], {"serie": []}, {"serie": [{"valor": "958"}]},
                   {"serie": [{"valor": 0}]}, {"serie": [{"valor": float("inf")}]},
                   {"serie": [{"valor": True}]}, {"serie": [{"valor": -1}]},
                   {"serie": [{"valor": TIPO_CAMBIO_MAXIMO + 1}]},
                   {"serie": [{"valor": None}]}, {"serie": [{"valor": float("nan")}]}):
        with responde(cuerpo):
            assert falla(lambda: servicio.obtener_tipo_cambio("UF")), cuerpo
    with responde({"serie": [{"valor": TIPO_CAMBIO_MAXIMO}]}):
        assert math.isclose(servicio.obtener_tipo_cambio("UF"), TIPO_CAMBIO_MAXIMO), \
            "el tope es inclusivo"
    with responde({"generationtime_ms": 0.2}):
        assert falla(lambda: servicio.obtener_clima("Xyzzy"), ValueError,
                     "No se encontró"), "ciudad inexistente: 200 sin results"
    for actual in ({}, {"current": {"temperature_2m": "18"}},
                   clima(temperatura=None)):
        with responde(geo, actual):
            assert falla(lambda: servicio.obtener_clima(valpo)), actual
    # --- Configuración por entorno: falla cerrado, sin salir a la red ni tumbar nada
    for variables in ({"ECOTECH_URL_INDICADORES": "http://mindicador.cl/api"},
                      {"ECOTECH_TIEMPO_ESPERA": "abc"}, {"ECOTECH_TIEMPO_ESPERA": "0"},
                      {"ECOTECH_TIEMPO_ESPERA": "61"}, {"ECOTECH_TIEMPO_ESPERA": "nan"}):
        inseguro = configurado(**variables)
        with mock.patch.object(requests, "get", side_effect=AssertionError(
                "salió a la red con una configuración insegura")) as get:
            assert falla(lambda s=inseguro: s.obtener_tipo_cambio("USD"),
                         contiene="configuración"), variables
            get.assert_not_called()
    fuga = configurado(ECOTECH_URL_INDICADORES="http://interno.ecotech.cl")
    assert not falla(lambda: fuga.obtener_tipo_cambio("USD"), contiene="interno"), \
        "el mensaje no repite la dirección configurada"
    propio = configurado(ECOTECH_URL_INDICADORES="https://espejo.ejemplo.cl/api/",
                         ECOTECH_TIEMPO_ESPERA="4")
    with responde({"serie": [{"valor": 958.42}]}) as get:
        propio.obtener_tipo_cambio("usd")
    assert get.call_args.args[0] == "https://espejo.ejemplo.cl/api/dolar"
    assert math.isclose(get.call_args.kwargs["timeout"][1], 4)
    with tempfile.TemporaryDirectory() as carpeta:
        env = Path(carpeta) / ".env"
        env.write_text("# comentario\nECOTECH_TIEMPO_ESPERA=7\n"
                       "ECOTECH_URL_CLIMA=https://desde-env\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {**limpio, "ECOTECH_URL_CLIMA": "https://real"},
                             clear=True):
            _cargar_env(env)
            assert os.environ["ECOTECH_TIEMPO_ESPERA"] == "7", ".env no cargado"
            assert os.environ["ECOTECH_URL_CLIMA"] == "https://real", \
                "una variable real del entorno le gana al .env"

    trampa = {"results": [{"name": "Valpo\x1b[2J", "country": "Chile",
                           "latitude": 0, "longitude": 0}]}
    with responde(trampa, clima()):
        assert servicio.obtener_clima(valpo)["ciudad"] == valpo, \
            "nombre con escape de terminal que venía de la red"


if __name__ == "__main__":
    _autoverificar()
    print("OK · APIs · códigos HTTP · errores de red · entradas y respuestas validadas")
