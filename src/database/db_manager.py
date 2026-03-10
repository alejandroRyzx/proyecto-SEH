"""
============================================================
  GESTOR DE BASE DE DATOS — SQLite para Parqueo
============================================================
  Maneja las tablas de tickets (entradas/salidas) y el
  registro histórico del sistema. Calcula tiempos de estadía
  y costos automáticamente.
============================================================
"""

import sqlite3
import os
from datetime import datetime
import config


class DatabaseManager:
    """
    Gestor de base de datos SQLite para el sistema de parqueo.
    
    Tablas:
    - tickets: Registro de entradas y salidas con timestamps.
    - parking_log: Histórico de estados de los espacios.
    """

    def __init__(self):
        # Crear directorio data/ si no existe
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        self.db_path = config.DB_PATH
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establece conexión con la base de datos."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            print(f"[DB] Conectado a: {self.db_path}")
        except sqlite3.Error as e:
            raise RuntimeError(f"[DB] Error de conexión: {e}")

    def _create_tables(self):
        """Crea las tablas si no existen."""
        cursor = self.conn.cursor()

        # Tabla de tickets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_code TEXT UNIQUE NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                spot_name TEXT,
                duration_minutes REAL,
                cost REAL,
                status TEXT DEFAULT 'ACTIVO'
            )
        """)

        # Tabla de log de estados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                spot_id INTEGER NOT NULL,
                spot_name TEXT NOT NULL,
                is_occupied INTEGER NOT NULL,
                free_spots INTEGER NOT NULL
            )
        """)

        # Tabla de configuración del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_entries INTEGER DEFAULT 0,
                total_exits INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0.0,
                peak_occupancy INTEGER DEFAULT 0
            )
        """)

        self.conn.commit()
        print("[DB] Tablas verificadas/creadas correctamente.")

    # ──────────────────────────────────────────────────────
    # 📥 ENTRADAS (Tickets)
    # ──────────────────────────────────────────────────────

    def register_entry(self, ticket_code, spot_name=None):
        """
        Registra la entrada de un vehículo.

        Args:
            ticket_code (str): Código único del ticket.
            spot_name (str): Nombre del espacio asignado (opcional).

        Returns:
            dict: Información del ticket creado.
        """
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO tickets (ticket_code, entry_time, spot_name, status)
                   VALUES (?, ?, ?, 'ACTIVO')""",
                (ticket_code, entry_time, spot_name)
            )
            self.conn.commit()

            ticket_info = {
                "id": cursor.lastrowid,
                "ticket_code": ticket_code,
                "entry_time": entry_time,
                "spot_name": spot_name,
                "status": "ACTIVO"
            }

            print(f"[DB] ✅ Entrada registrada: Ticket #{ticket_code} "
                  f"| Espacio: {spot_name} | Hora: {entry_time}")
            
            return ticket_info

        except sqlite3.IntegrityError:
            print(f"[DB] ⚠️ Ticket {ticket_code} ya existe.")
            return None
        except sqlite3.Error as e:
            print(f"[DB] ❌ Error al registrar entrada: {e}")
            return None

    # ──────────────────────────────────────────────────────
    # 📤 SALIDAS
    # ──────────────────────────────────────────────────────

    def register_exit(self, ticket_code):
        """
        Registra la salida de un vehículo, calcula duración y costo.

        Args:
            ticket_code (str): Código del ticket.

        Returns:
            dict: Información del ticket con duración y costo, o None.
        """
        try:
            cursor = self.conn.cursor()

            # Buscar el ticket activo
            cursor.execute(
                """SELECT * FROM tickets 
                   WHERE ticket_code = ? AND status = 'ACTIVO'""",
                (ticket_code,)
            )
            ticket = cursor.fetchone()

            if not ticket:
                print(f"[DB] ⚠️ No se encontró ticket activo: {ticket_code}")
                return None

            # Calcular tiempo de estadía
            entry_time = datetime.strptime(ticket["entry_time"], "%Y-%m-%d %H:%M:%S")
            exit_time = datetime.now()
            duration = (exit_time - entry_time).total_seconds() / 60  # En minutos

            # Calcular costo
            hours = max(duration / 60, 0.0)
            cost = max(hours * config.TARIFA_POR_HORA, config.TARIFA_MINIMA)
            cost = round(cost, 2)

            # Actualizar el ticket
            exit_time_str = exit_time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """UPDATE tickets 
                   SET exit_time = ?, duration_minutes = ?, cost = ?, status = 'COMPLETADO'
                   WHERE ticket_code = ? AND status = 'ACTIVO'""",
                (exit_time_str, round(duration, 2), cost, ticket_code)
            )
            self.conn.commit()

            ticket_info = {
                "ticket_code": ticket_code,
                "entry_time": ticket["entry_time"],
                "exit_time": exit_time_str,
                "spot_name": ticket["spot_name"],
                "duration_minutes": round(duration, 2),
                "cost": cost,
                "status": "COMPLETADO"
            }

            print(f"[DB] ✅ Salida registrada: Ticket #{ticket_code} "
                  f"| Duración: {duration:.1f} min "
                  f"| Costo: {config.MONEDA}{cost}")

            return ticket_info

        except sqlite3.Error as e:
            print(f"[DB] ❌ Error al registrar salida: {e}")
            return None

    # ──────────────────────────────────────────────────────
    # 📊 CONSULTAS
    # ──────────────────────────────────────────────────────

    def get_active_tickets(self):
        """Retorna todos los tickets activos (vehículos dentro)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE status = 'ACTIVO' ORDER BY entry_time DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_active_ticket_count(self):
        """Retorna la cantidad de tickets activos."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'ACTIVO'")
        return cursor.fetchone()[0]

    def get_today_stats(self):
        """Retorna estadísticas del día actual."""
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()

        # Total de entradas hoy
        cursor.execute(
            "SELECT COUNT(*) FROM tickets WHERE entry_time LIKE ?",
            (f"{today}%",)
        )
        total_entries = cursor.fetchone()[0]

        # Total de salidas hoy
        cursor.execute(
            "SELECT COUNT(*) FROM tickets WHERE exit_time LIKE ? AND status = 'COMPLETADO'",
            (f"{today}%",)
        )
        total_exits = cursor.fetchone()[0]

        # Ingresos del día
        cursor.execute(
            "SELECT COALESCE(SUM(cost), 0) FROM tickets "
            "WHERE exit_time LIKE ? AND status = 'COMPLETADO'",
            (f"{today}%",)
        )
        total_revenue = cursor.fetchone()[0]

        return {
            "date": today,
            "total_entries": total_entries,
            "total_exits": total_exits,
            "total_revenue": round(total_revenue, 2),
            "active_vehicles": total_entries - total_exits
        }

    def log_parking_state(self, spot_id, spot_name, is_occupied, free_spots):
        """Registra un cambio de estado en el log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO parking_log 
                   (timestamp, spot_id, spot_name, is_occupied, free_spots)
                   VALUES (?, ?, ?, ?, ?)""",
                (timestamp, spot_id, spot_name, int(is_occupied), free_spots)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DB] Error en log: {e}")

    def close(self):
        """Cierra la conexión de manera segura."""
        if self.conn:
            self.conn.close()
            print("[DB] Conexión cerrada.")

    def __del__(self):
        self.close()
