"""
============================================================
  CONTROLADOR PRINCIPAL — Lógica del Parqueo Inteligente
============================================================
  Orquesta todos los módulos: Visión, Base de Datos, Serial.
  Implementa el bucle principal del sistema y la toma de
  decisiones (autorizar entradas, procesar salidas, etc.)
============================================================
"""

import uuid
import time
import config
from src.vision.camera import Camera, DemoCamera
from src.vision.detector import ParkingDetector
from src.database.db_manager import DatabaseManager
from src.serial_comm.arduino_bridge import ArduinoBridge, ArduinoSimulator


class ParkingController:
    """
    Controlador maestro del sistema de parqueo inteligente.
    
    Responsabilidades:
    1. Coordinar cámara + detector para monitoreo visual
    2. Escuchar comandos del Arduino y responder
    3. Registrar entradas/salidas en la base de datos
    4. Mantener la cuenta de espacios libres actualizada
    """

    def __init__(self, use_simulator=False, use_demo=False):
        """
        Args:
            use_simulator (bool): Si True, usa el simulador de Arduino
                                  en vez de comunicación serial real.
            use_demo (bool): Si True, usa cámara simulada (sin webcam).
        """
        print("=" * 60)
        print("  🅿️  PARQUEO INTELIGENTE — Inicializando Sistema")
        print("=" * 60)

        # ── Inicializar componentes ──
        # Cámara real o demo
        if use_demo:
            self.camera = DemoCamera()
        else:
            self.camera = Camera()

        self.detector = ParkingDetector()
        self.db = DatabaseManager()

        # Arduino real o simulador
        if use_simulator:
            self.arduino = ArduinoSimulator()
        else:
            self.arduino = ArduinoBridge()

        # Estado interno
        self.is_running = False
        self.ticket_counter = int(time.time()) % 100000  # Único por sesión
        self._previous_free_count = -1  # Para detectar cambios

        print("=" * 60)
        print("  ✅ Sistema inicializado correctamente")
        print("=" * 60)

    def start(self):
        """
        Inicia todos los componentes del sistema.
        
        Returns:
            bool: True si todos los componentes arrancaron bien.
        """
        print("\n[CTRL] Iniciando componentes...")

        # 1. Abrir cámara
        try:
            self.camera.open()
        except RuntimeError as e:
            print(f"[CTRL] ❌ {e}")
            return False

        # 2. Conectar Arduino
        if not self.arduino.connect():
            print("[CTRL] ⚠️ Arduino no conectado. "
                  "Continuando solo con visión y simulador...")

        self.is_running = True
        print("[CTRL] 🟢 Sistema en marcha.\n")
        return True

    def process_cycle(self):
        """
        Ejecuta UN ciclo del bucle principal.
        Diseñado para ser llamado repetidamente desde main.py.
        
        Returns:
            tuple: (frame, spot_info, stats) o (None, None, None) si falla.
        """
        if not self.is_running:
            return None, None, None

        # ── 1. CAPTURAR FRAME ──
        frame = self.camera.read_frame()
        if frame is None:
            return None, None, None

        # ── 2. PROCESAR VISIÓN ──
        self.detector.process_frame(frame)
        spot_info = self.detector.get_spot_info()
        free_count = self.detector.get_free_count()

        # ── 3. ACTUALIZAR LCD si cambió la disponibilidad ──
        if free_count != self._previous_free_count:
            self._previous_free_count = free_count
            self.arduino.send_lcd_update(free_count)
            print(f"[CTRL] 📊 Espacios: {free_count} libres / "
                  f"{self.detector.get_occupied_count()} ocupados")

        # ── 4. PROCESAR COMANDOS DEL ARDUINO ──
        messages = self.arduino.get_messages()
        for msg in messages:
            self._handle_arduino_message(msg)

        # ── 5. OBTENER ESTADÍSTICAS ──
        stats = {
            "free": free_count,
            "occupied": self.detector.get_occupied_count(),
            "total": self.detector.get_total_count(),
            "active_tickets": self.db.get_active_ticket_count(),
            "today": self.db.get_today_stats()
        }

        return frame, spot_info, stats

    def _handle_arduino_message(self, message):
        """
        Procesa un mensaje recibido del Arduino.

        Args:
            message (str): El mensaje recibido (ej: "NUEVO_TICKET").
        """
        print(f"\n[CTRL] 🔔 Procesando mensaje: '{message}'")

        if message == config.CMD_NUEVO_TICKET:
            self._process_new_ticket()

        elif message == config.CMD_SOLICITAR_SALIDA:
            self._process_exit_request()

        else:
            print(f"[CTRL] ⚠️ Mensaje desconocido: '{message}'")

    def _process_new_ticket(self):
        """
        Procesa una solicitud de nuevo ticket (vehículo en la entrada).
        
        Flujo:
        1. Verificar si hay espacios libres
        2. Si hay → Generar ticket, abrir barrera, registrar en DB
        3. Si no hay → Notificar al Arduino (PARQUEO_LLENO)
        """
        free_count = self.detector.get_free_count()

        if free_count > 0:
            # Generar código de ticket único
            self.ticket_counter += 1
            ticket_code = f"T{self.ticket_counter:04d}"

            # Encontrar un espacio libre para asignar
            spot_name = self._find_free_spot_name()

            # Registrar en base de datos
            ticket = self.db.register_entry(ticket_code, spot_name)

            if ticket:
                # Ordenar al Arduino abrir la barrera de entrada
                self.arduino.send_command(config.CMD_ABRIR_ENTRADA)
                print(f"[CTRL] ✅ ENTRADA AUTORIZADA: Ticket {ticket_code} "
                      f"→ Espacio {spot_name}")
            else:
                print("[CTRL] ❌ Error al crear ticket.")
        else:
            # Parqueo lleno
            self.arduino.send_command(config.CMD_PARQUEO_LLENO)
            print("[CTRL] 🚫 PARQUEO LLENO — Entrada denegada.")

    def _process_exit_request(self):
        """
        Procesa una solicitud de salida (vehículo en la salida).
        
        Flujo:
        1. Buscar el ticket activo más antiguo
        2. Calcular tiempo y costo
        3. Abrir barrera de salida
        4. Registrar salida en DB
        """
        active_tickets = self.db.get_active_tickets()

        if active_tickets:
            # Tomar el ticket más antiguo (FIFO)
            oldest_ticket = active_tickets[-1]  # El último es el más viejo
            ticket_code = oldest_ticket["ticket_code"]

            # Registrar salida (calcula duración y costo automáticamente)
            result = self.db.register_exit(ticket_code)

            if result:
                # Abrir barrera de salida
                self.arduino.send_command(config.CMD_ABRIR_SALIDA)
                print(f"[CTRL] ✅ SALIDA AUTORIZADA: Ticket {ticket_code} "
                      f"| Duración: {result['duration_minutes']:.1f} min "
                      f"| Costo: {config.MONEDA}{result['cost']}")
            else:
                print("[CTRL] ❌ Error al procesar salida.")
        else:
            print("[CTRL] ⚠️ No hay tickets activos para procesar salida.")

    def _find_free_spot_name(self):
        """Encuentra el nombre del primer espacio libre."""
        for spot in self.detector.get_spot_info():
            if not spot["is_occupied"]:
                return spot["name"]
        return "N/A"

    def simulate_new_ticket(self):
        """Simula la llegada de un nuevo vehículo (por botón del UI)."""
        print("\n[CTRL] 🖱️ Botón NUEVO TICKET presionado")
        self._process_new_ticket()

    def simulate_exit_request(self):
        """Simula una solicitud de salida (por botón del UI)."""
        print("\n[CTRL] 🖱️ Botón SOLICITAR SALIDA presionado")
        self._process_exit_request()

    def handle_keyboard(self, key):
        """
        Procesa teclas presionadas (para el simulador y controles).

        Args:
            key (int): Código de tecla de cv2.waitKey().
            
        Returns:
            bool: False si se debe cerrar el sistema.
        """
        if key == ord('q') or key == 27:  # 'q' o ESC
            print("\n[CTRL] 🔴 Solicitud de cierre recibida.")
            return False

        # Si es simulador, pasar la tecla
        if isinstance(self.arduino, ArduinoSimulator):
            self.arduino.simulate_input(key)

        return True


    def stop(self):
        """Detiene todos los componentes de manera segura."""
        print("\n[CTRL] Deteniendo sistema...")
        self.is_running = False

        self.camera.release()
        self.arduino.disconnect()
        self.db.close()

        # Mostrar resumen final
        print("\n" + "=" * 60)
        print("  📊 RESUMEN DE SESIÓN")
        print("=" * 60)
        try:
            stats = self.db.get_today_stats()
            print(f"  Entradas totales: {stats['total_entries']}")
            print(f"  Salidas totales:  {stats['total_exits']}")
            print(f"  Ingresos:         {config.MONEDA}{stats['total_revenue']}")
        except Exception:
            pass
        print("=" * 60)
        print("  🅿️  Sistema detenido. ¡Hasta luego!")
        print("=" * 60)
