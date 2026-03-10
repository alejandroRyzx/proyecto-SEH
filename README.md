# 🅿️ Parqueo Inteligente — Prototipo SEH

Sistema automatizado de control de acceso y monitoreo de disponibilidad de espacios de parqueo, utilizando **visión artificial** con una sola cámara panorámica y comunicación serial con **Arduino**.

> **Materia:** Sistemas Embebidos y Hardware (SEH)  
> **Tipo:** Proyecto académico — Uso educativo  
> **Lenguaje principal:** Python 3.8+  
> **Hardware:** Arduino Uno/Mega + periféricos

---

## 📑 Tabla de Contenidos

- [Arquitectura](#️-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Paso a Paso](#-instalación-paso-a-paso)
- [Cómo Levantar el Proyecto](#-cómo-levantar-el-proyecto)
- [Modos de Ejecución](#-modos-de-ejecución)
- [Controles del Sistema](#-controles-del-sistema)
- [Ejecutar Tests](#-ejecutar-tests)
- [Conexiones del Arduino](#-conexiones-del-arduino)
- [Protocolo Serial](#-protocolo-serial)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Configuración Avanzada](#️-configuración-avanzada)
- [Solución de Problemas](#-solución-de-problemas)
- [Licencia](#-licencia)

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────┐
│                  EL CEREBRO (Python)                 │
│                                                      │
│   ┌──────────┐  ┌──────────┐  ┌─────────────────┐   │
│   │  Cámara  │→ │ Detector │→ │ Controlador     │   │
│   │  OpenCV  │  │  de ROIs │  │ Principal       │   │
│   └──────────┘  └──────────┘  └────────┬────────┘   │
│                                        │             │
│   ┌──────────┐                ┌────────▼────────┐   │
│   │  SQLite  │◄──────────────►│ Puente Serial   │   │
│   │ Database │                │   (PySerial)    │   │
│   └──────────┘                └────────┬────────┘   │
└────────────────────────────────────────┼─────────────┘
                                         │ USB
┌────────────────────────────────────────┼─────────────┐
│                  EL MÚSCULO (Arduino)  │             │
│                                        │             │
│   ┌──────────┐  ┌──────────┐  ┌────────▼────────┐   │
│   │ Sensores │→ │  Arduino │→ │  Servomotores   │   │
│   │    IR    │  │   Mega   │  │   (Barreras)    │   │
│   └──────────┘  └──────────┘  └─────────────────┘   │
│                      │                               │
│                 ┌────▼─────┐                         │
│                 │   LCD    │                         │
│                 │  Display │                         │
│                 └──────────┘                         │
└──────────────────────────────────────────────────────┘
```

---

## 📋 Requisitos Previos

### Software

| Software        | Versión mínima | Notas                             |
| --------------- | -------------- | --------------------------------- |
| **Python**      | 3.8+           | Verificar con `python3 --version` |
| **pip**         | 21+            | Verificar con `pip3 --version`    |
| **Git**         | 2.30+          | Verificar con `git --version`     |
| **Arduino IDE** | 1.8+ / 2.x     | Solo si se usa hardware real      |

### Hardware (opcional para modo Demo)

- Webcam (1080p recomendada)
- Arduino (Uno, Mega o compatible)
- 2× Servomotores SG90/MG996R
- 2× Sensores IR o botones
- Pantalla LCD 16×2 con módulo I2C
- 2× LEDs (verde y rojo)
- Buzzer pasivo
- Protoboard y cables

---

## 🚀 Instalación Paso a Paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/alejandroRyzx/proyecto-SEH.git
cd proyecto-SEH
```

### 2. Crear un entorno virtual (recomendado)

```bash
# Crear el entorno virtual
python3 -m venv venv

# Activar el entorno virtual
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

> 💡 **Tip:** Sabrás que el entorno está activo cuando veas `(venv)` al inicio de tu terminal.

### 3. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

Esto instala las siguientes librerías:

| Paquete         | Descripción                        |
| --------------- | ---------------------------------- |
| `opencv-python` | Visión artificial y GUI            |
| `pyserial`      | Comunicación serial con Arduino    |
| `numpy`         | Procesamiento numérico de imágenes |

### 4. (Opcional) Subir código al Arduino

Solo si vas a usar hardware real:

1. Abrir `arduino/parking_controller/parking_controller.ino` en el **Arduino IDE**
2. Instalar librerías necesarias desde el Library Manager:
   - `Servo` (incluida por defecto)
   - `LiquidCrystal_I2C`
3. Seleccionar tu placa y puerto correctos
4. Click en **Upload** (→)

---

## ▶️ Cómo Levantar el Proyecto

### Opción A: Modo Demo (sin cámara ni Arduino) — Recomendado para probar

```bash
python main.py --demo
```

Este modo **no requiere ningún hardware**. Simula la cámara, los sensores y los vehículos automáticamente.

### Opción B: Modo Simulador (con cámara, sin Arduino)

```bash
python main.py
```

Usa la cámara de tu computadora pero simula los sensores del Arduino por software.

### Opción C: Modo Serial (con Arduino conectado)

```bash
# Detectar automáticamente el puerto
python main.py --serial

# Especificar el puerto manualmente
python main.py --serial --port /dev/cu.usbmodem14201   # macOS
python main.py --serial --port COM3                     # Windows
python main.py --serial --port /dev/ttyUSB0             # Linux
```

### Ver todas las opciones disponibles

```bash
python main.py --help
```

---

## 🎮 Modos de Ejecución

| Modo          | Comando                   | Cámara | Arduino | Ideal para                     |
| ------------- | ------------------------- | ------ | ------- | ------------------------------ |
| **Demo**      | `python main.py --demo`   | ❌     | ❌      | Probar el software sin nada    |
| **Simulador** | `python main.py`          | ✅     | ❌      | Probar visión sin Arduino      |
| **Serial**    | `python main.py --serial` | ✅     | ✅      | Sistema completo en producción |

---

## 🕹️ Controles del Sistema

Durante la ejecución (en modo Simulador o Demo):

| Acción                      | Control                              |
| --------------------------- | ------------------------------------ |
| Simular llegada de vehículo | Botón **Nuevo Ticket** en GUI        |
| Simular solicitud de salida | Botón **Solicitar Salida** en GUI    |
| Salir del sistema           | Botón **Salir** en GUI / `q` / `ESC` |

---

## 🧪 Ejecutar Tests

El proyecto incluye tests unitarios que verifican los módulos principales **sin necesidad de hardware**:

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# O usando unittest directamente
python -m unittest tests/test_system.py -v

# O ejecutar el archivo directamente
python tests/test_system.py
```

**Tests incluidos:**

- `TestDatabaseManager` — CRUD de tickets, conteo, estadísticas
- `TestParkingDetector` — Inicialización y formato de datos
- `TestArduinoSimulator` — Conexión, comandos, simulación de entradas

---

## 🔌 Conexiones del Arduino

| Componente        | Pin Arduino |
| ----------------- | ----------- |
| Servo Entrada     | D9          |
| Servo Salida      | D10         |
| Sensor IR Entrada | D2          |
| Sensor IR Salida  | D3          |
| LED Verde         | D4          |
| LED Rojo          | D5          |
| Buzzer            | D6          |
| LCD SDA           | A4          |
| LCD SCL           | A5          |

---

## 📡 Protocolo Serial

Comunicación bidireccional a **9600 baudios**:

| Dirección        | Comando            | Descripción                   |
| ---------------- | ------------------ | ----------------------------- |
| Arduino → Python | `NUEVO_TICKET`     | Vehículo detectado en entrada |
| Arduino → Python | `SOLICITAR_SALIDA` | Vehículo solicita salir       |
| Python → Arduino | `ABRIR_ENTRADA`    | Abrir barrera de entrada      |
| Python → Arduino | `ABRIR_SALIDA`     | Abrir barrera de salida       |
| Python → Arduino | `PARQUEO_LLENO`    | No hay espacios disponibles   |
| Python → Arduino | `LCD:N`            | Actualizar LCD (N = libres)   |

---

## 📂 Estructura del Proyecto

```
proyecto-SEH/
├── main.py                          # 🚀 Punto de entrada principal
├── config.py                        # ⚙️ Configuración centralizada
├── requirements.txt                 # 📦 Dependencias Python
├── README.md                        # 📖 Este archivo
├── .gitignore                       # 🚫 Archivos excluidos de Git
│
├── src/                             # 📁 Código fuente
│   ├── __init__.py
│   ├── vision/                      # 👁️ Módulo de visión artificial
│   │   ├── __init__.py
│   │   ├── camera.py                #    Captura de cámara
│   │   ├── detector.py              #    Detección de espacios
│   │   └── calibrator.py            #    Herramienta de calibración
│   ├── database/                    # 🗄️ Módulo de base de datos
│   │   ├── __init__.py
│   │   └── db_manager.py            #    CRUD SQLite (tickets)
│   ├── serial_comm/                 # 🔌 Módulo de comunicación serial
│   │   ├── __init__.py
│   │   └── arduino_bridge.py        #    Puente PySerial / Simulador
│   ├── core/                        # 🧠 Módulo de lógica principal
│   │   ├── __init__.py
│   │   └── parking_controller.py    #    Controlador de parqueo
│   └── ui/                          # 🖥️ Módulo de interfaz visual
│       ├── __init__.py
│       └── display.py               #    GUI con OpenCV
│
├── arduino/                         # 🤖 Código del microcontrolador
│   └── parking_controller/
│       └── parking_controller.ino   #    Sketch de Arduino
│
├── tests/                           # 🧪 Tests unitarios
│   └── test_system.py               #    Tests del sistema completo
│
└── data/                            # 💾 Datos (auto-generado)
    └── parking.db                   #    BD SQLite (no versionada)
```

---

## ⚙️ Configuración Avanzada

Todos los parámetros se encuentran en `config.py`:

### Cámara

```python
CAMERA_INDEX = 0       # Índice de la webcam (0 = por defecto)
CAMERA_WIDTH = 1280    # Resolución horizontal
CAMERA_HEIGHT = 720    # Resolución vertical
CAMERA_FPS = 30        # Frames por segundo
```

### Detección

```python
DETECTION_THRESHOLD = 900   # Sensibilidad (800-3000)
BINARY_THRESHOLD = 45       # Binarización (0-255)
DILATE_KERNEL_SIZE = 3      # Limpieza de ruido
DETECTION_INTERVAL = 5      # Procesar cada N frames
```

### Puerto Serial

```python
SERIAL_PORT = "/dev/cu.usbmodem14201"  # macOS
# SERIAL_PORT = "COM3"                 # Windows
# SERIAL_PORT = "/dev/ttyUSB0"         # Linux
SERIAL_BAUDRATE = 9600
```

### Tarifas

```python
TARIFA_POR_HORA = 25.00   # Precio por hora
TARIFA_MINIMA = 10.00     # Cobro mínimo
MONEDA = "L"              # Símbolo de moneda
```

### Calibrar las Regiones de Interés (ROIs)

Para ajustar los espacios de parqueo a tu maqueta:

```bash
python -m src.vision.calibrator
```

1. Dibuja rectángulos sobre cada espacio de parqueo
2. Presiona **`s`** para guardar
3. Copia las coordenadas generadas a `config.py → PARKING_SPOTS`

---

## 🔧 Solución de Problemas

| Problema                                | Solución                                                             |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModuleNotFoundError`                   | Asegúrate de que el `venv` está activado: `source venv/bin/activate` |
| La cámara no abre                       | Usa `--demo` para probar sin cámara. Verifica otra app no la use     |
| `Serial port not found`                 | Verifica el puerto en `config.py` o usa `--port`                     |
| La detección es muy sensible/insensible | Ajusta `DETECTION_THRESHOLD` en `config.py`                          |
| `Permission denied` en el puerto        | macOS/Linux: `sudo chmod 666 /dev/cu.usbmodem*`                      |
| La BD se corrompe                       | Borra `data/parking.db`, se regenera automáticamente                 |

---

## 👥 Equipo

Proyecto desarrollado para la clase de **Sistemas Embebidos y Hardware (SEH)**.

---

## 📄 Licencia

Proyecto académico — Uso educativo.
