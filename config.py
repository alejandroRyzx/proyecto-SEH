"""
============================================================
  CONFIGURACIÓN CENTRALIZADA — PARQUEO INTELIGENTE
============================================================
  Todos los parámetros ajustables del sistema se definen aquí.
  Modifica estos valores según tu maqueta y hardware.
============================================================
"""

import os

# ──────────────────────────────────────────────────────────
# 📂 RUTAS
# ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "parking.db")

# ──────────────────────────────────────────────────────────
# 📷 CÁMARA
# ──────────────────────────────────────────────────────────
CAMERA_INDEX = 0                # Índice de la webcam (0 = por defecto)
CAMERA_WIDTH = 1280             # Resolución horizontal
CAMERA_HEIGHT = 720             # Resolución vertical
CAMERA_FPS = 30                 # Frames por segundo deseados

# ──────────────────────────────────────────────────────────
# 🅿️ ESPACIOS DE PARQUEO — Regiones de Interés (ROIs)
# ──────────────────────────────────────────────────────────
# Cada ROI es un diccionario con:
#   - "id":   Identificador del espacio
#   - "name": Nombre legible
#   - "rect": (x, y, ancho, alto) — coordenadas en píxeles
#
# ⚠️ IMPORTANTE: Usa la herramienta de calibración para obtener
# las coordenadas exactas de tu maqueta:
#   python -m src.vision.calibrator
# ──────────────────────────────────────────────────────────
PARKING_SPOTS = [
    {"id": 1, "name": "A1", "rect": (50,  200, 150, 120)},
    {"id": 2, "name": "A2", "rect": (220, 200, 150, 120)},
    {"id": 3, "name": "A3", "rect": (390, 200, 150, 120)},
    {"id": 4, "name": "A4", "rect": (560, 200, 150, 120)},
    {"id": 5, "name": "B1", "rect": (50,  400, 150, 120)},
    {"id": 6, "name": "B2", "rect": (220, 400, 150, 120)},
]

# ──────────────────────────────────────────────────────────
# 🔍 DETECCIÓN — Parámetros del Procesamiento Visual
# ──────────────────────────────────────────────────────────
# Umbral de píxeles blancos para considerar un espacio OCUPADO.
# Un valor más alto = menos sensibilidad.
# Rango típico: 800 - 3000 (depende del tamaño del ROI y la iluminación)
DETECTION_THRESHOLD = 900

# Valor umbral para la binarización adaptativa (0-255)
BINARY_THRESHOLD = 45

# Cantidad de dilatación para limpiar ruido (kernel size)
DILATE_KERNEL_SIZE = 3

# Cada cuántos frames se ejecuta la detección completa
# (para no saturar el CPU; 1 = cada frame)
DETECTION_INTERVAL = 5

# ──────────────────────────────────────────────────────────
# 🔌 COMUNICACIÓN SERIAL (Arduino)
# ──────────────────────────────────────────────────────────
SERIAL_PORT = "/dev/cu.usbmodem14201"   # macOS: /dev/cu.usbmodemXXXX
                                         # Windows: "COM3", "COM4", etc.
                                         # Linux: "/dev/ttyUSB0"
SERIAL_BAUDRATE = 9600                   # Debe coincidir con el Arduino
SERIAL_TIMEOUT = 1                       # Timeout de lectura en segundos

# ──────────────────────────────────────────────────────────
# 📡 COMANDOS DEL PROTOCOLO SERIAL
# ──────────────────────────────────────────────────────────
# Comandos que ENVÍA Arduino → Python
CMD_NUEVO_TICKET = "NUEVO_TICKET"
CMD_SOLICITAR_SALIDA = "SOLICITAR_SALIDA"

# Comandos que ENVÍA Python → Arduino
CMD_ABRIR_ENTRADA = "ABRIR_ENTRADA"
CMD_ABRIR_SALIDA = "ABRIR_SALIDA"
CMD_PARQUEO_LLENO = "PARQUEO_LLENO"
CMD_ACTUALIZAR_LCD = "LCD:"           # Prefijo: "LCD:3" = 3 espacios libres

# ──────────────────────────────────────────────────────────
# 💰 TARIFAS
# ──────────────────────────────────────────────────────────
TARIFA_POR_HORA = 25.00        # Precio por hora (en tu moneda local)
TARIFA_MINIMA = 10.00          # Cobro mínimo
MONEDA = "L"                   # Símbolo de moneda (Lempiras, $, €, etc.)

# ──────────────────────────────────────────────────────────
# 🖥️ INTERFAZ VISUAL
# ──────────────────────────────────────────────────────────
WINDOW_NAME = "Parqueo Inteligente — Monitor"
COLOR_LIBRE = (0, 255, 0)         # Verde — espacio libre
COLOR_OCUPADO = (0, 0, 255)       # Rojo — espacio ocupado
COLOR_TEXTO = (255, 255, 255)     # Blanco — texto
COLOR_FONDO_INFO = (40, 40, 40)   # Gris oscuro — barra de info
FONT_SCALE = 0.6
FONT_THICKNESS = 2
