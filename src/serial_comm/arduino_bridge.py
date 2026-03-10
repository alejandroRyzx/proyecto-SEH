"""
============================================================
  PUENTE ARDUINO — Comunicación Serial Bidireccional
============================================================
  Establece y gestiona la comunicación PySerial entre Python
  (maestro) y Arduino (esclavo). Maneja el envío/recepción
  de comandos con reconexión automática.
============================================================
"""

import serial
import time
import threading
import config


class ArduinoBridge:
    """
    Puente de comunicación bidireccional con Arduino.
    
    Flujo:
    - Python ESCUCHA comandos del Arduino (ej: NUEVO_TICKET)
    - Python ENVÍA instrucciones al Arduino (ej: ABRIR_ENTRADA)
    
    Se ejecuta en un hilo separado para no bloquear el bucle
    principal de visión.
    """

    def __init__(self):
        self.serial_port = None
        self.is_connected = False
        self.port = config.SERIAL_PORT
        self.baudrate = config.SERIAL_BAUDRATE
        self.timeout = config.SERIAL_TIMEOUT

        # Cola de mensajes recibidos (thread-safe)
        self._received_messages = []
        self._lock = threading.Lock()

        # Hilo de lectura continua
        self._read_thread = None
        self._running = False

    def connect(self):
        """
        Intenta conectar con el Arduino por puerto serial.
        
        Returns:
            bool: True si la conexión fue exitosa.
        """
        try:
            print(f"[SER] Conectando a {self.port} @ {self.baudrate} baud...")
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )

            # Esperar a que Arduino se reinicie tras la conexión serial
            time.sleep(2)

            # Limpiar el buffer
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            self.is_connected = True
            print(f"[SER] ✅ Conectado a Arduino en {self.port}")

            # Iniciar hilo de lectura
            self._start_read_thread()

            return True

        except serial.SerialException as e:
            print(f"[SER] ❌ Error de conexión: {e}")
            print(f"[SER] Verifica que el Arduino esté conectado y el "
                  f"puerto '{self.port}' sea correcto.")
            self.is_connected = False
            return False

    def _start_read_thread(self):
        """Inicia el hilo de lectura en segundo plano."""
        self._running = True
        self._read_thread = threading.Thread(
            target=self._read_loop,
            daemon=True,
            name="Arduino-Reader"
        )
        self._read_thread.start()
        print("[SER] Hilo de lectura iniciado.")

    def _read_loop(self):
        """
        Bucle de lectura continua del puerto serial.
        Se ejecuta en un hilo separado (daemon).
        """
        while self._running and self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    raw = self.serial_port.readline()
                    message = raw.decode("utf-8", errors="ignore").strip()
                    
                    if message:
                        print(f"[SER] 📥 Recibido de Arduino: '{message}'")
                        with self._lock:
                            self._received_messages.append(message)

            except serial.SerialException as e:
                print(f"[SER] ⚠️ Error de lectura: {e}")
                self.is_connected = False
                break
            except Exception as e:
                print(f"[SER] ⚠️ Error inesperado en lectura: {e}")

            time.sleep(0.01)  # Pequeña pausa para no saturar CPU

    def send_command(self, command):
        """
        Envía un comando al Arduino.

        Args:
            command (str): El comando a enviar (ej: "ABRIR_ENTRADA").

        Returns:
            bool: True si se envió correctamente.
        """
        if not self.is_connected or self.serial_port is None:
            print(f"[SER] ⚠️ No conectado. No se puede enviar: {command}")
            return False

        try:
            message = f"{command}\n"
            self.serial_port.write(message.encode("utf-8"))
            self.serial_port.flush()
            print(f"[SER] 📤 Enviado a Arduino: '{command}'")
            return True

        except serial.SerialException as e:
            print(f"[SER] ❌ Error al enviar '{command}': {e}")
            self.is_connected = False
            return False

    def get_messages(self):
        """
        Obtiene y limpia todos los mensajes recibidos.

        Returns:
            list[str]: Lista de mensajes pendientes.
        """
        with self._lock:
            messages = self._received_messages.copy()
            self._received_messages.clear()
        return messages

    def has_messages(self):
        """Verifica si hay mensajes pendientes sin consumirlos."""
        with self._lock:
            return len(self._received_messages) > 0

    def send_lcd_update(self, free_spots):
        """
        Envía actualización de espacios libres para el LCD.
        
        Args:
            free_spots (int): Cantidad de espacios libres.
        """
        self.send_command(f"{config.CMD_ACTUALIZAR_LCD}{free_spots}")

    def disconnect(self):
        """Cierra la conexión serial de manera segura."""
        self._running = False
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2)

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("[SER] Conexión serial cerrada.")

        self.is_connected = False

    def __del__(self):
        self.disconnect()


class ArduinoSimulator:
    """
    Simulador de Arduino para pruebas sin hardware físico.
    Simula los comandos del Arduino usando el teclado.
    
    Teclas:
    - 'n': Simular NUEVO_TICKET
    - 'x': Simular SOLICITAR_SALIDA
    """

    def __init__(self):
        self.is_connected = True
        self._received_messages = []
        self._lock = threading.Lock()
        print("[SIM] 🎮 Modo SIMULADOR activado (sin Arduino físico)")
        print("[SIM] Teclas: [n] = Nuevo ticket | [x] = Solicitar salida")

    def connect(self):
        """Simula conexión exitosa."""
        print("[SIM] ✅ Simulador conectado.")
        return True

    def send_command(self, command):
        """Simula envío de comando."""
        print(f"[SIM] 📤 Comando simulado: '{command}'")
        return True

    def simulate_input(self, key):
        """
        Simula un comando del Arduino basado en tecla presionada.
        
        Args:
            key (int): Código de tecla de cv2.waitKey().
        """
        if key == ord('n'):
            with self._lock:
                self._received_messages.append(config.CMD_NUEVO_TICKET)
            print(f"[SIM] 📥 Simulado: {config.CMD_NUEVO_TICKET}")

        elif key == ord('x'):
            with self._lock:
                self._received_messages.append(config.CMD_SOLICITAR_SALIDA)
            print(f"[SIM] 📥 Simulado: {config.CMD_SOLICITAR_SALIDA}")

    def get_messages(self):
        """Obtiene mensajes simulados."""
        with self._lock:
            messages = self._received_messages.copy()
            self._received_messages.clear()
        return messages

    def has_messages(self):
        """Verifica mensajes pendientes."""
        with self._lock:
            return len(self._received_messages) > 0

    def send_lcd_update(self, free_spots):
        """Simula actualización del LCD."""
        print(f"[SIM] 📺 LCD mostraría: {free_spots} espacios libres")

    def disconnect(self):
        """Simula desconexión."""
        self.is_connected = False
        print("[SIM] Simulador desconectado.")
