"""
============================================================
  CALIBRADOR DE ROIs — Herramienta Visual Interactiva
============================================================
  Permite definir visualmente las posiciones exactas de cada
  espacio de parqueo en el frame de la cámara.
  
  USO:
    python -m src.vision.calibrator
  
  CONTROLES:
    - Click izquierdo: Iniciar/finalizar selección de ROI
    - 'r': Reiniciar selección actual
    - 's': Guardar todas las ROIs y salir
    - 'q': Salir sin guardar
    - 'u': Deshacer última ROI
============================================================
"""

import cv2
import json
import config
from src.vision.camera import Camera


class ROICalibrator:
    """
    Herramienta interactiva para marcar las regiones de los
    espacios de parqueo directamente sobre la imagen de la cámara.
    """

    def __init__(self):
        self.camera = Camera()
        self.rois = []
        self.current_roi = None
        self.drawing = False
        self.start_point = None
        self.frame = None
        self.spot_counter = 1

    def _mouse_callback(self, event, x, y, flags, param):
        """Callback del mouse para dibujar rectángulos."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.current_roi = (
                self.start_point[0], self.start_point[1],
                x - self.start_point[0], y - self.start_point[1]
            )

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.start_point:
                # Normalizar para que x,y sea siempre la esquina sup-izquierda
                x1 = min(self.start_point[0], x)
                y1 = min(self.start_point[1], y)
                w = abs(x - self.start_point[0])
                h = abs(y - self.start_point[1])

                if w > 10 and h > 10:  # Filtrar clicks accidentales
                    roi_data = {
                        "id": self.spot_counter,
                        "name": f"P{self.spot_counter}",
                        "rect": (x1, y1, w, h)
                    }
                    self.rois.append(roi_data)
                    print(f"[CAL] ROI {roi_data['name']} definida: ({x1}, {y1}, {w}, {h})")
                    self.spot_counter += 1
                
                self.current_roi = None
                self.start_point = None

    def run(self):
        """Ejecuta la herramienta de calibración."""
        print("=" * 60)
        print("  🔧 CALIBRADOR DE REGIONES DE INTERÉS (ROIs)")
        print("=" * 60)
        print("  Dibuja rectángulos sobre cada espacio de parqueo.")
        print("  Controles:")
        print("    Click + arrastrar → Dibujar ROI")
        print("    'u' → Deshacer última ROI")
        print("    's' → Guardar y salir")
        print("    'q' → Salir sin guardar")
        print("=" * 60)

        self.camera.open()
        cv2.namedWindow("Calibrador")
        cv2.setMouseCallback("Calibrador", self._mouse_callback)

        while True:
            frame = self.camera.read_frame()
            if frame is None:
                continue

            self.frame = frame.copy()
            display = frame.copy()

            # Dibujar ROIs ya definidas
            for roi in self.rois:
                x, y, w, h = roi["rect"]
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    display, roi["name"],
                    (x + 5, y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )

            # Dibujar ROI en progreso
            if self.current_roi and self.drawing:
                x, y, w, h = self.current_roi
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 255), 2)

            # Barra de información
            info_text = f"Espacios definidos: {len(self.rois)} | " \
                        f"[s]Guardar [u]Deshacer [q]Salir"
            cv2.putText(
                display, info_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )

            cv2.imshow("Calibrador", display)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("[CAL] Saliendo sin guardar.")
                break

            elif key == ord('u') and self.rois:
                removed = self.rois.pop()
                self.spot_counter -= 1
                print(f"[CAL] Deshecho: {removed['name']}")

            elif key == ord('s'):
                self._save_rois()
                break

        self.camera.release()
        cv2.destroyAllWindows()

    def _save_rois(self):
        """Guarda las ROIs en formato listo para config.py."""
        if not self.rois:
            print("[CAL] No hay ROIs para guardar.")
            return

        print("\n" + "=" * 60)
        print("  📋 COPIA ESTO EN tu config.py → PARKING_SPOTS")
        print("=" * 60)
        print("PARKING_SPOTS = [")
        for roi in self.rois:
            x, y, w, h = roi["rect"]
            print(f'    {{"id": {roi["id"]}, "name": "{roi["name"]}", '
                  f'"rect": ({x}, {y}, {w}, {h})}},')
        print("]")
        print("=" * 60)

        # También guardar en JSON como respaldo
        json_path = "data/calibration.json"
        import os
        os.makedirs("data", exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(self.rois, f, indent=2)
        print(f"[CAL] Respaldo guardado en: {json_path}")


# ──────────────────────────────────────────────────────────
# Punto de entrada directo
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    calibrator = ROICalibrator()
    calibrator.run()
