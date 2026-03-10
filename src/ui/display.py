"""
============================================================
  INTERFAZ VISUAL — Display OpenCV del Monitor
============================================================
  Renderiza la información del sistema directamente sobre
  el frame de la cámara: estados de los espacios, estadísticas,
  botones clickeables para acciones, etc.
============================================================
"""

import cv2
import numpy as np
import time
import config


class Button:
    """Botón clickeable dibujado sobre el frame de OpenCV."""

    def __init__(self, x, y, w, h, label, color, hover_color=None, text_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.color = color
        self.hover_color = hover_color or tuple(min(c + 40, 255) for c in color)
        self.text_color = text_color
        self.is_hovered = False
        self.is_pressed = False
        self._press_time = 0

    def contains(self, mx, my):
        """Verifica si el punto (mx, my) está dentro del botón."""
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def draw(self, frame):
        """Dibuja el botón sobre el frame."""
        # Efecto de "pressed" por 300ms
        if self.is_pressed and (time.time() - self._press_time) < 0.3:
            current_color = tuple(max(c - 60, 0) for c in self.color)
        elif self.is_hovered:
            current_color = self.hover_color
        else:
            current_color = self.color

        # Sombra
        cv2.rectangle(
            frame,
            (self.x + 2, self.y + 2),
            (self.x + self.w + 2, self.y + self.h + 2),
            (20, 20, 20), -1
        )

        # Fondo del botón
        cv2.rectangle(
            frame,
            (self.x, self.y),
            (self.x + self.w, self.y + self.h),
            current_color, -1
        )

        # Borde
        border_color = (255, 255, 255) if self.is_hovered else tuple(min(c + 80, 255) for c in self.color)
        cv2.rectangle(
            frame,
            (self.x, self.y),
            (self.x + self.w, self.y + self.h),
            border_color, 2
        )

        # Texto centrado
        text_size = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]
        text_x = self.x + (self.w - text_size[0]) // 2
        text_y = self.y + (self.h + text_size[1]) // 2
        cv2.putText(
            frame, self.label,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.text_color, 2
        )

    def press(self):
        """Marca el botón como presionado."""
        self.is_pressed = True
        self._press_time = time.time()


class ParkingDisplay:
    """
    Renderiza la interfaz visual del sistema de monitoreo
    usando OpenCV con botones clickeables.
    """

    def __init__(self):
        self.window_name = config.WINDOW_NAME
        self._last_events = []

        # ── Definir botones ──
        # Se posicionan en la parte inferior de la ventana
        btn_y = config.CAMERA_HEIGHT - 70
        btn_h = 50
        btn_w = 200
        margin = 20

        self.btn_nuevo_ticket = Button(
            x=margin, y=btn_y, w=btn_w, h=btn_h,
            label="NUEVO TICKET",
            color=(0, 140, 0),           # Verde oscuro
            hover_color=(0, 200, 0),     # Verde claro al hover
        )

        self.btn_salida = Button(
            x=margin + btn_w + margin, y=btn_y, w=btn_w, h=btn_h,
            label="SOLICITAR SALIDA",
            color=(180, 100, 0),         # Naranja
            hover_color=(230, 140, 0),
        )

        self.btn_salir = Button(
            x=config.CAMERA_WIDTH - btn_w - margin, y=btn_y, w=btn_w, h=btn_h,
            label="SALIR",
            color=(0, 0, 160),           # Rojo
            hover_color=(0, 0, 220),
        )

        self.buttons = [self.btn_nuevo_ticket, self.btn_salida, self.btn_salir]

        # ── Acción pendiente ──
        # Se usa para comunicar clicks al main loop
        self._pending_action = None

    def setup(self):
        """Configura la ventana de OpenCV con mouse callback."""
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)

    def _mouse_callback(self, event, x, y, flags, param):
        """Callback del mouse para detectar clicks y hover."""

        # ── Hover: actualizar estado visual ──
        for btn in self.buttons:
            btn.is_hovered = btn.contains(x, y)

        # ── Click ──
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.btn_nuevo_ticket.contains(x, y):
                self.btn_nuevo_ticket.press()
                self._pending_action = "NUEVO_TICKET"
                print("[UI] 🖱️ Click: NUEVO TICKET")

            elif self.btn_salida.contains(x, y):
                self.btn_salida.press()
                self._pending_action = "SOLICITAR_SALIDA"
                print("[UI] 🖱️ Click: SOLICITAR SALIDA")

            elif self.btn_salir.contains(x, y):
                self.btn_salir.press()
                self._pending_action = "SALIR"
                print("[UI] 🖱️ Click: SALIR")

    def get_pending_action(self):
        """
        Obtiene y limpia la acción pendiente del usuario.

        Returns:
            str | None: "NUEVO_TICKET", "SOLICITAR_SALIDA", "SALIR", o None.
        """
        action = self._pending_action
        self._pending_action = None
        return action

    def render(self, frame, spot_info, stats):
        """
        Renderiza toda la información sobre el frame.

        Args:
            frame (numpy.ndarray): Frame original de la cámara.
            spot_info (list[dict]): Información de cada espacio.
            stats (dict): Estadísticas del sistema.

        Returns:
            numpy.ndarray: Frame con la información renderizada.
        """
        if frame is None:
            return None

        display = frame.copy()

        # 1. Dibujar rectangulos de los espacios
        self._draw_spots(display, spot_info)

        # 2. Dibujar barra de información superior
        self._draw_top_bar(display, stats)

        # 3. Dibujar panel de estadísticas lateral
        self._draw_stats_panel(display, stats)

        # 4. Dibujar barra de botones inferior
        self._draw_button_bar(display)

        # 5. Dibujar los botones
        for btn in self.buttons:
            btn.draw(display)

        return display

    def show(self, frame):
        """
        Muestra el frame en la ventana.

        Args:
            frame (numpy.ndarray): Frame a mostrar.

        Returns:
            int: Código de la tecla presionada (255 si ninguna).
        """
        if frame is not None:
            cv2.imshow(self.window_name, frame)
        return cv2.waitKey(30) & 0xFF

    def _draw_spots(self, frame, spot_info):
        """Dibuja rectángulos con colores según el estado de cada espacio."""
        for spot in spot_info:
            x, y, w, h = spot["rect"]
            is_occupied = spot["is_occupied"]

            color = config.COLOR_OCUPADO if is_occupied else config.COLOR_LIBRE
            status_text = "OCUPADO" if is_occupied else "LIBRE"

            # Rectángulo semi-transparente
            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            # Borde del rectángulo
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            # Nombre del espacio
            cv2.putText(
                frame, spot["name"],
                (x + 5, y + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.FONT_SCALE + 0.2, config.COLOR_TEXTO, 2
            )

            # Estado
            cv2.putText(
                frame, status_text,
                (x + 5, y + h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.FONT_SCALE - 0.1, color, 2
            )

    def _draw_top_bar(self, frame, stats):
        """Dibuja la barra de información en la parte superior."""
        h, w = frame.shape[:2]
        bar_height = 50

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, bar_height), config.COLOR_FONDO_INFO, -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Título
        cv2.putText(
            frame, "PARQUEO INTELIGENTE",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1
        )

        free = stats.get("free", 0)
        total = stats.get("total", 0)
        occupied = stats.get("occupied", 0)

        status_text = f"LIBRES: {free}/{total}"
        color = (0, 255, 0) if free > 0 else (0, 0, 255)
        cv2.putText(
            frame, status_text,
            (10, 42),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )

        cv2.putText(
            frame, f"OCUPADOS: {occupied}",
            (250, 42),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
        )

        # Barra de llenado
        if total > 0:
            fill_x = 500
            fill_w = 200
            fill_ratio = occupied / total
            cv2.rectangle(frame, (fill_x, 15), (fill_x + fill_w, 40), (80, 80, 80), -1)
            fill_color = (0, 255, 0) if fill_ratio < 0.7 else (0, 165, 255) if fill_ratio < 0.9 else (0, 0, 255)
            cv2.rectangle(frame, (fill_x, 15), (fill_x + int(fill_w * fill_ratio), 40), fill_color, -1)
            cv2.rectangle(frame, (fill_x, 15), (fill_x + fill_w, 40), (200, 200, 200), 1)
            cv2.putText(
                frame, f"{int(fill_ratio * 100)}%",
                (fill_x + fill_w + 10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1
            )

    def _draw_stats_panel(self, frame, stats):
        """Dibuja un panel con estadísticas del día."""
        h, w = frame.shape[:2]
        panel_w = 220
        panel_x = w - panel_w - 10
        panel_y = 60

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + 140),
            config.COLOR_FONDO_INFO, -1
        )
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        cv2.putText(
            frame, "ESTADISTICAS HOY",
            (panel_x + 10, panel_y + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1
        )

        today = stats.get("today", {})
        y_offset = panel_y + 45

        lines = [
            f"Entradas: {today.get('total_entries', 0)}",
            f"Salidas:  {today.get('total_exits', 0)}",
            f"Activos:  {today.get('active_vehicles', 0)}",
            f"Ingresos: {config.MONEDA}{today.get('total_revenue', 0):.2f}",
        ]

        for line in lines:
            cv2.putText(
                frame, line,
                (panel_x + 15, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1
            )
            y_offset += 25

    def _draw_button_bar(self, frame):
        """Dibuja el fondo de la barra de botones."""
        h, w = frame.shape[:2]
        bar_y = h - 85

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, bar_y), (w, h), (25, 25, 25), -1)
        cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)

        # Línea separadora
        cv2.line(frame, (0, bar_y), (w, bar_y), (60, 60, 60), 1)

    def add_event(self, event_text):
        """Agrega un evento al historial."""
        self._last_events.insert(0, event_text)
        if len(self._last_events) > 5:
            self._last_events.pop()

    def destroy(self):
        """Cierra todas las ventanas de OpenCV."""
        cv2.destroyAllWindows()
