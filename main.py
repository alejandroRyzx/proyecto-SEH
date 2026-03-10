"""
============================================================
  MAIN.PY — Punto de Entrada del Parqueo Inteligente
============================================================
  Ejecuta el bucle principal del sistema integrando:
  - Visión artificial (cámara + detección de espacios)
  - Base de datos (SQLite para tickets)
  - Comunicación serial (Arduino para barreras/sensores)
  - Interfaz visual (monitor en tiempo real)

  USO:
    python main.py              → Modo simulador (sin Arduino)
    python main.py --demo       → Modo DEMO (sin cámara ni Arduino)
    python main.py --serial     → Modo con Arduino real
    python main.py --help       → Ver opciones

  CONTROLES (en modo simulador/demo):
    [n] → Simular nuevo ticket (vehículo en entrada)
    [x] → Simular solicitud de salida
    [q] → Salir del sistema
============================================================
"""

import sys
import argparse
import cv2

from src.core.parking_controller import ParkingController
from src.ui.display import ParkingDisplay


def parse_arguments():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="🅿️ Parqueo Inteligente — Sistema de Monitoreo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                    Modo simulador (sin Arduino)
  python main.py --demo             Modo DEMO (sin cámara ni Arduino)
  python main.py --serial           Con Arduino conectado
  python main.py --serial --port COM3  Especificar puerto serial

Controles durante ejecución:
  [n]  Simular nuevo ticket (en modo simulador/demo)
  [x]  Simular solicitud de salida (en modo simulador/demo)
  [q]  Cerrar el sistema
  [ESC]  Cerrar el sistema
        """
    )

    parser.add_argument(
        "--serial",
        action="store_true",
        help="Usar comunicación serial real con Arduino (por defecto: simulador)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Modo DEMO: sin cámara ni Arduino, todo simulado visualmente"
    )
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="Puerto serial del Arduino (ej: COM3, /dev/cu.usbmodem14201)"
    )

    return parser.parse_args()


def main():
    """Función principal del sistema."""
    args = parse_arguments()

    # Sobreescribir puerto serial si se especificó
    if args.port:
        import config
        config.SERIAL_PORT = args.port

    # Determinar modo de operación
    use_simulator = not args.serial
    use_demo = args.demo

    # En modo demo, forzar simulador de Arduino también
    if use_demo:
        use_simulator = True

    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           🅿️  PARQUEO INTELIGENTE v1.0                  ║")
    print("║           Sistema de Monitoreo Automático               ║")
    print("╠══════════════════════════════════════════════════════════╣")
    if use_demo:
        print("║  🎬 Modo: DEMO (sin cámara ni Arduino)                 ║")
        print("║  🎮 Usa [n] y [x] para simular sensores                ║")
        print("║  🚗 Los carritos cambian automáticamente cada 8s        ║")
    elif use_simulator:
        print("║  📡 Modo: SIMULADOR (sin Arduino)                      ║")
        print("║  🎮 Usa [n] y [x] para simular sensores                ║")
    else:
        print(f"║  📡 Modo: SERIAL (Arduino conectado)                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # ── Inicializar sistema ──
    controller = ParkingController(use_simulator=use_simulator, use_demo=use_demo)
    display = ParkingDisplay()

    if not controller.start():
        print("\n❌ Error: No se pudo iniciar el sistema.")
        print("   Verifica que la cámara esté conectada.")
        sys.exit(1)

    display.setup()

    print("\n🟢 Sistema operativo. Usa los BOTONES en la ventana.\n")

    # ══════════════════════════════════════════════════════
    # BUCLE PRINCIPAL
    # ══════════════════════════════════════════════════════
    try:
        while True:
            # 1. Ejecutar un ciclo de procesamiento
            frame, spot_info, stats = controller.process_cycle()

            if frame is not None and spot_info is not None:
                # 2. Renderizar la información sobre el frame
                rendered_frame = display.render(frame, spot_info, stats)

                # 3. Mostrar en pantalla
                display.show(rendered_frame)
            else:
                cv2.waitKey(30) & 0xFF

            # 4. Procesar clicks en botones
            action = display.get_pending_action()
            if action == "NUEVO_TICKET":
                controller.simulate_new_ticket()
            elif action == "SOLICITAR_SALIDA":
                controller.simulate_exit_request()
            elif action == "SALIR":
                print("\n[MAIN] 🔴 Botón SALIR presionado.")
                break

            # 5. También permitir cerrar con ESC o 'q' como respaldo
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        print("\n\n[MAIN] ⚡ Interrupción detectada (Ctrl+C)")

    finally:
        # ── Limpieza segura ──
        controller.stop()
        display.destroy()
        print("\n👋 ¡Hasta pronto!\n")


# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
