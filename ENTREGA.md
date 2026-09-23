# Entrega — Caso EcoTech · Evaluación Sumativa 2 (Unidades 2 y 3)

**INACAP · TI3V21 Programación Orientada a Objeto Seguro**
**Docente:** Rubén Schnettler Lucero

| Integrantes |
|---|
| Claudio Medina |
| Lucas Espinoza |
| Leonardo Guerrero |

**Repositorio:** https://github.com/leonardoguerrerodev/poo-ecotech

---

## 1. Versión que se entrega

La versión evaluada es **el último commit de la rama `main` hasta el 23 de septiembre de 2026 a las
23:59, hora de Chile**. El comando del paso 2 deja el repositorio exactamente en esa versión, aunque
después se agreguen commits.

## 2. Cómo clonarlo y ejecutarlo

Requiere **Python 3.11 o superior** y conexión a internet para las opciones que consultan servicios
externos (11, 12 y 21). Probado con Python 3.14.

```bash
git clone https://github.com/leonardoguerrerodev/poo-ecotech.git
cd poo-ecotech

# Deja el repositorio en la versión entregada (último commit hasta el 23-09-2026 23:59, hora de Chile)
git checkout $(git rev-list -n 1 --before="2026-09-23 23:59:59 -0300" main)

python3 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt    # requests y sus dependencias, con versión exacta

python3 ecotech.py                 # autoverificación del sistema (base temporal): termina en OK
python3 servicios.py               # autoverificación de las APIs, sin conectarse: termina en OK
python3 main.py                    # el programa
```

En Windows, si `python3` no existe, se usa `python` o `py`.

## 3. Primer uso del programa

- **No hay usuarios ni claves escritos en el código.** La primera vez que se ejecuta `main.py`, el
  programa pide **crear la cuenta de administrador** (RRHH): usuario de 3 a 20 caracteres y clave de
  12 o más, con tres de estos cuatro tipos: minúscula, mayúscula, número y símbolo. Después pide
  iniciar sesión con esa cuenta.
- **Opción 1** del menú: carga datos de ejemplo (dos departamentos, tres empleados y dos proyectos, uno
  en Valparaíso pagado en pesos y otro en Madrid pagado en euros).
- **Opción 14**: crea cuentas de **gerente** o de **empleado** para probar los permisos. Una cuenta de
  empleado se vincula a su ficha y solo puede registrar sus propias horas.
- Escribir **`x`** en cualquier dato cancela la acción sin guardar nada. **`0`** sale.
- Las APIs (Open-Meteo y mindicador.cl) **no piden llave**. La configuración opcional va en un `.env`
  a partir de `.env.example`; sin ese archivo se usan valores seguros por defecto.
- Si no hay internet, el programa **no se detiene**: avisa y, si tiene un dato anterior, lo usa marcado
  como «valor referencial».

El menú tiene 25 opciones, agrupadas en crear, leer, actualizar y eliminar (1-10), servicios
externos (11-12), administración (13-14), proyectos (15-20) e historial de las APIs (21-25). Está
descrito completo en el `README.md`.

## 4. Dónde está cada cosa

| Archivo | Qué es |
|---|---|
| `ecotech.py` | Las clases del diagrama, la base de datos SQLite, su CRUD y el inicio de sesión |
| `servicios.py` | El cliente de los servicios externos (clima y tipo de cambio) |
| `main.py` | El menú de terminal: no contiene SQL ni HTTP |
| `diagramas/EcoTech_UML_VIGENTE.drawio` | **El diagrama de clases vigente**, igual al código miembro por miembro; con su imagen en `EcoTech_UML_VIGENTE.png` (y versión oscura). Los diagramas de unidades anteriores están en `diagramas/historico/` |
| `README.md` | Descripción completa: diseño, seguridad y menú |
| `docs/ANALISIS_IA.md` | Uso de inteligencia artificial: qué se adoptó, modificó o descartó y por qué |
| `docs/AUDITORIA.md` | Auditorías de seguridad del código, con cada hallazgo y su corrección |
| `docs/SALIDA_TERMINAL.md` | Sesiones reales del programa, incluidos los fallos provocados |
| `.env.example` | Variables de configuración, sin valores secretos |

## 5. Lo que pide la Unidad 3 y dónde verlo

| Se pide | Dónde está |
|---|---|
| Consumo de servicios externos con librerías oficiales (3.1.1) | `servicios.py`, clase `ServicioExterno` con `requests`; el dato se valida, se guarda y se usa por proyecto (opciones 11, 12 y 21) |
| Seguridad: autenticación, validación y variables de entorno (3.1.2) | Inicio de sesión con clave cifrada (scrypt) y bloqueo tras 5 intentos; permisos por rol; `.env.example` y `.gitignore` |
| Manejo de errores de red, tiempos de espera y códigos HTTP (3.1.3) | `servicios.py`, método `__consultar`; el menú sigue funcionando sin red (`docs/SALIDA_TERMINAL.md`, sección 6) |
| Revisión del código con IA (3.1.4) | `docs/ANALISIS_IA.md`, sección 7: la tabla de los cinco aspectos (credenciales, protocolo, tiempo de espera, manejo de errores, uso de la respuesta) |
| La salida, incluida la de un fallo provocado | `docs/SALIDA_TERMINAL.md`, secciones 4 a 6 |

## 6. Uso de inteligencia artificial

Se usó Claude (Anthropic) como apoyo en el desarrollo, además de sugerencias de GitHub Copilot. Cada
fragmento sugerido se revisó, se probó y se decidió si adoptarlo, modificarlo o descartarlo, con su
fundamento técnico. El registro completo está en `docs/ANALISIS_IA.md`.
