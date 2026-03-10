"""
============================================================
  MÓDULO DE CÁMARA — Captura de Video en Tiempo Real
============================================================
  Encapsula la lógica de OpenCV para abrir, leer y liberar
  la webcam. Proporciona frames individuales al detector.
============================================================
"""

import cv2
import numpy as np
import random
import time
import config


class Camera:
    """
    Wrapper sobre cv2.VideoCapture para manejar la webcam
    con los parámetros definidos en config.
    """

    def __init__(self):
        self.cap = None
        self.is_open = False

    def open(self):
        """Abre la cámara con la configuración definida."""
        print(f"[CAM] Abriendo cámara en índice {config.CAMERA_INDEX}...")
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"[CAM] ERROR: No se pudo abrir la cámara {config.CAMERA_INDEX}. "
                "Verifica que esté conectada y no esté siendo usada por otra app."
            )

        # Configurar resolución y FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        # Leer resolución real (puede diferir de la solicitada)
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        print(f"[CAM] Cámara abierta: {actual_w}x{actual_h} @ {actual_fps} FPS")
        self.is_open = True
        return True

    def read_frame(self):
        """
        Lee un frame de la cámara.
        
        Returns:
            frame (numpy.ndarray | None): El frame capturado, o None si falla.
        """
        if not self.is_open or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("[CAM] ADVERTENCIA: No se pudo leer el frame.")
            return None

        return frame

    def release(self):
        """Libera la cámara de manera segura."""
        if self.cap is not None:
            self.cap.release()
            self.is_open = False
            print("[CAM] Cámara liberada.")

    def __del__(self):
        self.release()


class DemoCamera:
    """
    Cámara simulada para modo DEMO (sin webcam física).
    Genera frames sintéticos de un estacionamiento con
    "carritos" que aparecen y desaparecen aleatoriamente.
    
    Controles extra en modo demo:
    - Los carritos cambian de posición cada ciertos segundos
    - Simula condiciones reales de detección
    """

    def __init__(self):
        self.is_open = False
        self.width = config.CAMERA_WIDTH
        self.height = config.CAMERA_HEIGHT

        # Estado de cada espacio: True = hay carrito dibujado
        self.occupied_spots = {}
        for spot in config.PARKING_SPOTS:
            # Iniciar con algunos espacios ocupados aleatorios
            self.occupied_spots[spot["id"]] = random.choice([True, False])

        # Temporizador para cambios automáticos
        self._last_change_time = time.time()
        self._change_interval = 8  # Cambiar algo cada 8 segundos

        # Colores para los carritos simulados (OSCUROS para que el detector los vea)
        # El detector busca píxeles < 45 en escala de grises
        self._car_colors = [
            (40, 15, 15),     # Azul muy oscuro
            (10, 10, 35),     # Rojo oscuro
            (15, 30, 15),     # Verde oscuro
            (10, 25, 40),     # Naranja oscuro
            (35, 15, 35),     # Morado oscuro
            (25, 25, 25),     # Gris oscuro
        ]

    def open(self):
        """Simula la apertura de la cámara."""
        self.is_open = True
        occupied_count = sum(1 for v in self.occupied_spots.values() if v)
        total = len(self.occupied_spots)
        print(f"[DEMO] 🎬 Cámara DEMO abierta: {self.width}x{self.height}")
        print(f"[DEMO] Estado inicial: {occupied_count}/{total} espacios ocupados")
        print(f"[DEMO] Los carritos cambian cada {self._change_interval}s automáticamente")
        return True

    def read_frame(self):
        """
        Genera un frame sintético simulando un estacionamiento.
        
        Returns:
            frame (numpy.ndarray): Imagen BGR del estacionamiento simulado.
        """
        if not self.is_open:
            return None

        # Cambiar un espacio aleatoriamente cada N segundos
        current_time = time.time()
        if current_time - self._last_change_time > self._change_interval:
            self._toggle_random_spot()
            self._last_change_time = current_time

        # Crear el frame base (gris CLARO = piso de concreto)
        # Debe ser > 45 (umbral del detector) para que se vea como "vacío"
        frame = np.full(
            (self.height, self.width, 3),
            (180, 180, 180),  # Gris claro (concreto)
            dtype=np.uint8
        )

        # Dibujar líneas del piso
        self._draw_parking_lot(frame)

        # Dibujar carritos en los espacios ocupados
        self._draw_cars(frame)

        # Agregar texto "MODO DEMO"
        cv2.putText(
            frame, "MODO DEMO - Sin Camara",
            (self.width - 320, self.height - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1
        )

        return frame

    def _draw_parking_lot(self, frame):
        """Dibuja el fondo del estacionamiento con líneas de parqueo."""
        # Título
        cv2.putText(
            frame, "ESTACIONAMIENTO SEH",
            (self.width // 2 - 180, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2
        )

        # Dibujar líneas de cada espacio de parqueo
        for spot in config.PARKING_SPOTS:
            x, y, w, h = spot["rect"]

            # Líneas blancas delimitando el espacio
            cv2.rectangle(frame, (x, y), (x + w, y + h), (140, 140, 140), 2)

            # Número del espacio en el suelo
            text_x = x + w // 2 - 15
            text_y = y + h // 2 + 5
            cv2.putText(
                frame, spot["name"],
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1
            )

    def _draw_cars(self, frame):
        """Dibuja carritos en los espacios ocupados."""
        for spot in config.PARKING_SPOTS:
            if self.occupied_spots.get(spot["id"], False):
                x, y, w, h = spot["rect"]

                # Elegir color del carrito (consistente por ID)
                color = self._car_colors[spot["id"] % len(self._car_colors)]

                # Márgenes para que el carrito no llene todo el espacio
                margin_x = int(w * 0.15)
                margin_y = int(h * 0.1)

                car_x = x + margin_x
                car_y = y + margin_y
                car_w = w - 2 * margin_x
                car_h = h - 2 * margin_y

                # Cuerpo del carrito (rectángulo relleno)
                cv2.rectangle(
                    frame,
                    (car_x, car_y),
                    (car_x + car_w, car_y + car_h),
                    color, -1
                )

                # Ventanas (ligeramente menos oscuro)
                win_y = car_y + int(car_h * 0.2)
                win_h = int(car_h * 0.3)
                win_color = tuple(min(c + 15, 40) for c in color)
                cv2.rectangle(
                    frame,
                    (car_x + 5, win_y),
                    (car_x + car_w - 5, win_y + win_h),
                    win_color, -1
                )

                # Ruedas (círculos negros)
                wheel_y = car_y + car_h - 5
                cv2.circle(frame, (car_x + 15, wheel_y), 6, (5, 5, 5), -1)
                cv2.circle(frame, (car_x + car_w - 15, wheel_y), 6, (5, 5, 5), -1)

    def _toggle_random_spot(self):
        """Cambia el estado de un espacio aleatorio."""
        spot_ids = list(self.occupied_spots.keys())
        random_id = random.choice(spot_ids)
        old_state = self.occupied_spots[random_id]
        self.occupied_spots[random_id] = not old_state

        # Encontrar nombre del espacio
        spot_name = "?"
        for s in config.PARKING_SPOTS:
            if s["id"] == random_id:
                spot_name = s["name"]
                break

        action = "🚗 Carrito llegó a" if not old_state else "🚗 Carrito salió de"
        print(f"[DEMO] {action} espacio {spot_name}")

    def toggle_spot(self, spot_id):
        """Cambia manualmente el estado de un espacio específico."""
        if spot_id in self.occupied_spots:
            self.occupied_spots[spot_id] = not self.occupied_spots[spot_id]

    def release(self):
        """Simula liberación de la cámara."""
        self.is_open = False
        print("[DEMO] Cámara demo cerrada.")

    def __del__(self):
        self.release()
