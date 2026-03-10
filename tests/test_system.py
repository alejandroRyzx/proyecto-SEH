"""
============================================================
  TESTS BÁSICOS — Verificación del Sistema
============================================================
  Tests para verificar que los módulos del sistema funcionan
  correctamente sin necesidad de hardware físico.
============================================================
"""

import os
import sys
import unittest
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseManager(unittest.TestCase):
    """Tests para el gestor de base de datos."""

    def setUp(self):
        """Configurar DB temporal para cada test."""
        import config
        config.DB_PATH = "/tmp/test_parking.db"
        config.DATA_DIR = "/tmp"
        
        from src.database.db_manager import DatabaseManager
        self.db = DatabaseManager()

    def tearDown(self):
        """Limpiar después de cada test."""
        self.db.close()
        if os.path.exists("/tmp/test_parking.db"):
            os.remove("/tmp/test_parking.db")

    def test_register_entry(self):
        """Test: Registrar una entrada crea un ticket."""
        result = self.db.register_entry("TEST001", "A1")
        self.assertIsNotNone(result)
        self.assertEqual(result["ticket_code"], "TEST001")
        self.assertEqual(result["spot_name"], "A1")
        self.assertEqual(result["status"], "ACTIVO")

    def test_register_exit(self):
        """Test: Registrar una salida calcula duración y costo."""
        self.db.register_entry("TEST002", "B1")
        result = self.db.register_exit("TEST002")
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "COMPLETADO")
        self.assertGreaterEqual(result["cost"], 0)

    def test_duplicate_ticket(self):
        """Test: No se pueden crear tickets duplicados."""
        self.db.register_entry("DUP001", "A1")
        result = self.db.register_entry("DUP001", "A2")
        self.assertIsNone(result)

    def test_active_ticket_count(self):
        """Test: El conteo de tickets activos es correcto."""
        self.db.register_entry("COUNT001", "A1")
        self.db.register_entry("COUNT002", "A2")
        self.assertEqual(self.db.get_active_ticket_count(), 2)

        self.db.register_exit("COUNT001")
        self.assertEqual(self.db.get_active_ticket_count(), 1)

    def test_today_stats(self):
        """Test: Las estadísticas del día son correctas."""
        self.db.register_entry("STAT001", "A1")
        self.db.register_entry("STAT002", "A2")
        self.db.register_exit("STAT001")

        stats = self.db.get_today_stats()
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["total_exits"], 1)


class TestParkingDetector(unittest.TestCase):
    """Tests para el detector de espacios."""

    def test_initialization(self):
        """Test: El detector se inicializa con los espacios de config."""
        import config
        from src.vision.detector import ParkingDetector
        
        detector = ParkingDetector()
        self.assertEqual(detector.get_total_count(), len(config.PARKING_SPOTS))
        self.assertEqual(detector.get_free_count(), len(config.PARKING_SPOTS))
        self.assertEqual(detector.get_occupied_count(), 0)

    def test_spot_info(self):
        """Test: La información de espacios tiene el formato correcto."""
        from src.vision.detector import ParkingDetector
        
        detector = ParkingDetector()
        info = detector.get_spot_info()
        
        self.assertIsInstance(info, list)
        for spot in info:
            self.assertIn("id", spot)
            self.assertIn("name", spot)
            self.assertIn("rect", spot)
            self.assertIn("is_occupied", spot)


class TestArduinoSimulator(unittest.TestCase):
    """Tests para el simulador de Arduino."""

    def test_connect(self):
        """Test: El simulador siempre conecta exitosamente."""
        from src.serial_comm.arduino_bridge import ArduinoSimulator
        
        sim = ArduinoSimulator()
        self.assertTrue(sim.connect())
        self.assertTrue(sim.is_connected)

    def test_send_command(self):
        """Test: El simulador acepta comandos sin error."""
        from src.serial_comm.arduino_bridge import ArduinoSimulator
        
        sim = ArduinoSimulator()
        self.assertTrue(sim.send_command("ABRIR_ENTRADA"))

    def test_simulate_input(self):
        """Test: El simulador genera mensajes correctos."""
        from src.serial_comm.arduino_bridge import ArduinoSimulator
        import config
        
        sim = ArduinoSimulator()
        sim.simulate_input(ord('n'))
        
        messages = sim.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], config.CMD_NUEVO_TICKET)


if __name__ == "__main__":
    print("=" * 60)
    print("  🧪 EJECUTANDO TESTS DEL PARQUEO INTELIGENTE")
    print("=" * 60)
    unittest.main(verbosity=2)
