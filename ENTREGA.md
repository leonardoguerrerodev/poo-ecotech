### ENTREGA - CASO ECOTECH ###

Asignatura: TI3V21 Programación Orientada a Objeto Seguro (INACAP)
Evaluación: Sumativa 2 (Unidades 2 y 3)
Docente: Rubén Schnettler Lucero

Integrantes:
- Claudio Medina
- Lucas Espinoza
- Leonardo Guerrero

Repositorio: https://github.com/leonardoguerrerodev/poo-ecotech

Versión entregada: el último commit de main hasta el 23-09-2026 a las 23:59 (hora de Chile).


### REQUISITOS ###

- Python 3.11 o superior
- Git
- Internet (solo para las opciones de clima y tipo de cambio)


### LINUX Y MAC ###

    git clone https://github.com/leonardoguerrerodev/poo-ecotech.git
    cd poo-ecotech
    git checkout $(git rev-list -n 1 --before="2026-09-23 23:59:59 -0300" main)
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python3 ecotech.py
    python3 servicios.py
    python3 main.py


### WINDOWS (PowerShell) ###

    git clone https://github.com/leonardoguerrerodev/poo-ecotech.git
    cd poo-ecotech
    git checkout (git rev-list -n 1 --before="2026-09-23 23:59:59 -0300" main)
    py -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    py ecotech.py
    py servicios.py
    py main.py

Si PowerShell no deja activar el entorno, ejecutar antes:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass


### QUÉ HACE CADA COMANDO ###

- git checkout ...  : deja el código en la versión entregada.
- ecotech.py        : prueba automática del sistema. Debe terminar en OK.
- servicios.py      : prueba automática de las APIs, sin internet. Debe terminar en OK.
- main.py           : abre el programa.


### PRIMER USO ###

- No hay usuarios ni claves en el código.
- La primera vez, el programa pide crear la cuenta de administrador.
  La clave debe tener 12 o más caracteres y tres de estos: minúscula, mayúscula, número, símbolo.
- Opción 1: carga datos de ejemplo.
- Opción 14: crea usuarios gerente o empleado para probar los permisos.
- Escribir x cancela la acción. 0 sale del programa.


### DÓNDE ESTÁ CADA COSA ###

- ecotech.py              : clases, base de datos, CRUD e inicio de sesión
- servicios.py            : consumo de las APIs (clima y tipo de cambio)
- main.py                 : menú
- diagramas/EcoTech_UML_VIGENTE.drawio : diagrama de clases vigente (y su imagen .png)
- docs/SALIDA_TERMINAL.md : ejecuciones reales, incluidos fallos provocados
- docs/AUDITORIA.md       : revisión de seguridad
- docs/ANALISIS_IA.md     : uso de inteligencia artificial
- README.md               : descripción completa
