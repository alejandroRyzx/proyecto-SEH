"""
============================================================
  DETECTOR DE ESPACIOS — Procesamiento Visual de ROIs
============================================================
  Analiza cada Región de Interés (ROI) del frame capturado
  para determinar si un espacio de parqueo está libre u
  ocupado, basándose en la densidad de píxeles.
============================================================
"""

import cv2
import numpy as np
import config


class ParkingDetector:
    """
    Detecta la ocupación de espacios de parqueo analizando
    regiones específicas del frame de la cámara.
    
    Algoritmo:
    1. Convierte el ROI a escala de grises
    2. Aplica desenfoque gaussiano para reducir ruido
    3. Aplica umbral adaptativo para binarizar
    4. Dilata la imagen para conectar regiones
    5. Cuenta los píxeles blancos (no-cero)
    6. Si el conteo supera el umbral → OCUPADO
    """

    def __init__(self):
        self.spots = config.PARKING_SPOTS
        self.threshold = config.DETECTION_THRESHOLD
        self.binary_thresh = config.BINARY_THRESHOLD
        self.kernel_size = config.DILATE_KERNEL_SIZE
        self.frame_count = 0
        self.detection_interval = config.DETECTION_INTERVAL

        # Estado actual de cada espacio: {id: True/False}
        # True = Ocupado, False = Libre
        self.spot_states = {spot["id"]: False for spot in self.spots}

        # Kernel para dilatación (se crea una sola vez)
        self.kernel = np.ones(
            (self.kernel_size, self.kernel_size), np.uint8
        )

        print(f"[DET] Detector inicializado con {len(self.spots)} espacios.")
        print(f"[DET] Umbral de detección: {self.threshold} píxeles")

    def process_frame(self, frame):
        """
        Procesa un frame completo y actualiza el estado de cada espacio.
        
        Solo ejecuta la detección completa cada N frames (definido por
        DETECTION_INTERVAL) para optimizar rendimiento.

        Args:
            frame (numpy.ndarray): Frame de la cámara en formato BGR.

        Returns:
            dict: {spot_id: is_occupied} — estados actualizados.
        """
        if frame is None:
            return self.spot_states

        self.frame_count += 1

        # Solo procesar cada N frames para no saturar el CPU
        if self.frame_count % self.detection_interval != 0:
            return self.spot_states

        # Convertir a escala de grises una sola vez
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for spot in self.spots:
            spot_id = spot["id"]
            x, y, w, h = spot["rect"]

            # Extraer la Región de Interés (ROI)
            roi = gray[y:y + h, x:x + w]

            # Verificar que el ROI es válido
            if roi.size == 0:
                print(f"[DET] ADVERTENCIA: ROI vacío para espacio {spot['name']}")
                continue

            # Pipeline de procesamiento
            is_occupied = self._analyze_roi(roi)
            self.spot_states[spot_id] = is_occupied

        return self.spot_states

    def _analyze_roi(self, roi):
        """
        Analiza un ROI individual para determinar si está ocupado.

        Pipeline:
        1. Desenfoque Gaussiano (reduce ruido de cámara)
        2. Umbral binario (separa objetos del fondo)
        3. Dilatación (conecta regiones fragmentadas)
        4. Conteo de píxeles no-cero

        Args:
            roi (numpy.ndarray): Subimagen en escala de grises.

        Returns:
            bool: True si el espacio está ocupado.
        """
        # 1. Desenfoque para suavizar ruido
        blurred = cv2.GaussianBlur(roi, (5, 5), 0)

        # 2. Umbral binario: píxeles más oscuros que el umbral → blanco
        _, binary = cv2.threshold(
            blurred, self.binary_thresh, 255, cv2.THRESH_BINARY_INV
        )

        # 3. Dilatación para rellenar huecos
        dilated = cv2.dilate(binary, self.kernel, iterations=1)

        # 4. Contar píxeles blancos (representan presencia de objeto)
        pixel_count = cv2.countNonZero(dilated)

        return pixel_count > self.threshold

    def get_free_count(self):
        """Retorna la cantidad de espacios libres."""
        return sum(1 for occupied in self.spot_states.values() if not occupied)

    def get_occupied_count(self):
        """Retorna la cantidad de espacios ocupados."""
        return sum(1 for occupied in self.spot_states.values() if occupied)

    def get_total_count(self):
        """Retorna el total de espacios."""
        return len(self.spots)

    def get_spot_info(self):
        """
        Retorna información detallada de cada espacio.

        Returns:
            list[dict]: Lista con id, name, rect, is_occupied por espacio.
        """
        info = []
        for spot in self.spots:
            info.append({
                "id": spot["id"],
                "name": spot["name"],
                "rect": spot["rect"],
                "is_occupied": self.spot_states[spot["id"]]
            })
        return info
