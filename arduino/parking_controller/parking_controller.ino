/*
 * ============================================================
 *   PARQUEO INTELIGENTE — Código Arduino (El Músculo)
 * ============================================================
 *   Microcontrolador esclavo que interactúa con el mundo físico.
 *   
 *   Funciones:
 *   - Leer sensores IR / botones
 *   - Controlar servomotores (barreras de entrada/salida)
 *   - Mostrar información en LCD
 *   - Comunicarse con Python via Serial
 *   
 *   PROTOCOLO SERIAL:
 *   Arduino → Python:
 *     "NUEVO_TICKET"       → Cuando un vehículo llega a la entrada
 *     "SOLICITAR_SALIDA"   → Cuando un vehículo solicita salir
 *   
 *   Python → Arduino:
 *     "ABRIR_ENTRADA"      → Orden de abrir barrera de entrada
 *     "ABRIR_SALIDA"       → Orden de abrir barrera de salida
 *     "PARQUEO_LLENO"      → Informar que no hay espacio
 *     "LCD:N"              → Actualizar LCD con N espacios libres
 * ============================================================
 */

#include <Servo.h>
#include <LiquidCrystal_I2C.h>

// ──────────────────────────────────────────────────────────
// 📌 PINES
// ──────────────────────────────────────────────────────────
#define PIN_SERVO_ENTRADA    9    // Servomotor de la barrera de entrada
#define PIN_SERVO_SALIDA     10   // Servomotor de la barrera de salida
#define PIN_SENSOR_ENTRADA   2    // Sensor IR / Botón de entrada
#define PIN_SENSOR_SALIDA    3    // Sensor IR / Botón de salida
#define PIN_LED_VERDE        4    // LED indicador: hay espacio
#define PIN_LED_ROJO         5    // LED indicador: parqueo lleno
#define PIN_BUZZER           6    // Buzzer para alertas sonoras

// ──────────────────────────────────────────────────────────
// ⚙️ CONFIGURACIÓN
// ──────────────────────────────────────────────────────────
#define ANGULO_CERRADO       0    // Posición de barrera cerrada
#define ANGULO_ABIERTO       90   // Posición de barrera abierta
#define TIEMPO_BARRERA_MS    3000 // Tiempo que la barrera permanece abierta
#define DEBOUNCE_MS          300  // Anti-rebote para sensores

// ──────────────────────────────────────────────────────────
// 📦 OBJETOS GLOBALES
// ──────────────────────────────────────────────────────────
Servo servoEntrada;
Servo servoSalida;
LiquidCrystal_I2C lcd(0x27, 16, 2);  // Dirección I2C, 16 columnas, 2 filas

// ──────────────────────────────────────────────────────────
// 🔄 VARIABLES DE ESTADO
// ──────────────────────────────────────────────────────────
String inputSerial = "";              // Buffer para datos seriales
bool entradaProcessing = false;       // Flag para evitar doble lectura
bool salidaProcessing = false;
unsigned long lastEntradaTime = 0;    // Para anti-rebote
unsigned long lastSalidaTime = 0;
int espaciosLibres = 0;              // Últimos espacios libres recibidos

// Carácter personalizado: carro para LCD
byte carIcon[8] = {
  0b00000,
  0b01110,
  0b11111,
  0b11111,
  0b01010,
  0b00000,
  0b00000,
  0b00000
};


// ══════════════════════════════════════════════════════════
//  SETUP
// ══════════════════════════════════════════════════════════
void setup() {
  // Comunicación serial con Python
  Serial.begin(9600);
  
  // Configurar pines
  pinMode(PIN_SENSOR_ENTRADA, INPUT_PULLUP);
  pinMode(PIN_SENSOR_SALIDA, INPUT_PULLUP);
  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  
  // Configurar servomotores
  servoEntrada.attach(PIN_SERVO_ENTRADA);
  servoSalida.attach(PIN_SERVO_SALIDA);
  servoEntrada.write(ANGULO_CERRADO);
  servoSalida.write(ANGULO_CERRADO);
  
  // Configurar LCD
  lcd.init();
  lcd.backlight();
  lcd.createChar(0, carIcon);
  
  // Pantalla de bienvenida
  lcd.setCursor(0, 0);
  lcd.print("  PARQUEO SEH   ");
  lcd.setCursor(0, 1);
  lcd.print(" Inicializando..");
  
  // LEDs iniciales
  digitalWrite(PIN_LED_VERDE, HIGH);
  digitalWrite(PIN_LED_ROJO, LOW);
  
  // Beep de confirmación
  tone(PIN_BUZZER, 1000, 200);
  delay(300);
  tone(PIN_BUZZER, 1500, 200);
  
  delay(2000);
  
  // Pantalla principal
  updateLCD(6);  // Asumir todos libres al inicio
  
  Serial.println("ARDUINO_READY");
}


// ══════════════════════════════════════════════════════════
//  LOOP PRINCIPAL
// ══════════════════════════════════════════════════════════
void loop() {
  // ── 1. Leer sensores de entrada/salida ──
  checkSensors();
  
  // ── 2. Leer comandos de Python por Serial ──
  readSerialCommands();
}


// ──────────────────────────────────────────────────────────
// 🔍 LECTURA DE SENSORES
// ──────────────────────────────────────────────────────────
void checkSensors() {
  unsigned long currentTime = millis();
  
  // ── Sensor de ENTRADA ──
  // El sensor IR lee LOW cuando detecta un objeto (active-low)
  // O el botón se presiona (INPUT_PULLUP → LOW al presionar)
  if (digitalRead(PIN_SENSOR_ENTRADA) == LOW) {
    if (!entradaProcessing && (currentTime - lastEntradaTime > DEBOUNCE_MS)) {
      entradaProcessing = true;
      lastEntradaTime = currentTime;
      
      // Notificar a Python que hay un vehículo esperando
      Serial.println("NUEVO_TICKET");
      
      // Feedback visual
      blinkLED(PIN_LED_VERDE, 2);
    }
  } else {
    entradaProcessing = false;
  }
  
  // ── Sensor de SALIDA ──
  if (digitalRead(PIN_SENSOR_SALIDA) == LOW) {
    if (!salidaProcessing && (currentTime - lastSalidaTime > DEBOUNCE_MS)) {
      salidaProcessing = true;
      lastSalidaTime = currentTime;
      
      // Notificar a Python que un vehículo quiere salir
      Serial.println("SOLICITAR_SALIDA");
      
      // Feedback visual
      blinkLED(PIN_LED_ROJO, 2);
    }
  } else {
    salidaProcessing = false;
  }
}


// ──────────────────────────────────────────────────────────
// 📡 LECTURA DE COMANDOS SERIALES
// ──────────────────────────────────────────────────────────
void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n') {
      // Comando completo recibido
      inputSerial.trim();
      processCommand(inputSerial);
      inputSerial = "";
    } else {
      inputSerial += c;
    }
  }
}


// ──────────────────────────────────────────────────────────
// ⚡ PROCESAMIENTO DE COMANDOS
// ──────────────────────────────────────────────────────────
void processCommand(String command) {
  
  if (command == "ABRIR_ENTRADA") {
    // ── Abrir barrera de entrada ──
    Serial.println("ACK:ENTRADA");
    openGate(servoEntrada, "ENTRADA");
    tone(PIN_BUZZER, 2000, 150);  // Beep de autorización
    
  } else if (command == "ABRIR_SALIDA") {
    // ── Abrir barrera de salida ──
    Serial.println("ACK:SALIDA");
    openGate(servoSalida, "SALIDA");
    tone(PIN_BUZZER, 2000, 150);
    
  } else if (command == "PARQUEO_LLENO") {
    // ── Indicar que no hay espacio ──
    Serial.println("ACK:LLENO");
    digitalWrite(PIN_LED_VERDE, LOW);
    digitalWrite(PIN_LED_ROJO, HIGH);
    
    // Alarma sonora (3 beeps rápidos)
    for (int i = 0; i < 3; i++) {
      tone(PIN_BUZZER, 800, 100);
      delay(150);
    }
    
    // Mostrar en LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("  PARQUEO LLENO ");
    lcd.setCursor(0, 1);
    lcd.print("  Sin espacios  ");
    
    delay(2000);
    updateLCD(0);
    
  } else if (command.startsWith("LCD:")) {
    // ── Actualizar cantidad de espacios en LCD ──
    String numStr = command.substring(4);
    int freeSpots = numStr.toInt();
    espaciosLibres = freeSpots;
    updateLCD(freeSpots);
    
    // Actualizar LEDs según disponibilidad
    if (freeSpots > 0) {
      digitalWrite(PIN_LED_VERDE, HIGH);
      digitalWrite(PIN_LED_ROJO, LOW);
    } else {
      digitalWrite(PIN_LED_VERDE, LOW);
      digitalWrite(PIN_LED_ROJO, HIGH);
    }
  }
}


// ──────────────────────────────────────────────────────────
// 🚧 CONTROL DE BARRERAS (SERVOMOTORES)
// ──────────────────────────────────────────────────────────
void openGate(Servo &servo, String gateName) {
  // Abrir barrera (mover a 90°)
  servo.write(ANGULO_ABIERTO);
  
  // Actualizar LCD temporalmente
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(gateName + " ABIERTA");
  lcd.setCursor(0, 1);
  lcd.print("  Pase por favor");
  
  // Mantener abierta por el tiempo configurado
  delay(TIEMPO_BARRERA_MS);
  
  // Cerrar barrera (regresar a 0°)
  servo.write(ANGULO_CERRADO);
  
  // Restaurar LCD
  delay(500);
  updateLCD(espaciosLibres);
}


// ──────────────────────────────────────────────────────────
// 📺 ACTUALIZACIÓN DEL LCD
// ──────────────────────────────────────────────────────────
void updateLCD(int freeSpots) {
  lcd.clear();
  
  // Línea 1: Nombre del sistema
  lcd.setCursor(0, 0);
  lcd.write(byte(0));  // Ícono de carro
  lcd.print(" PARQUEO SEH");
  
  // Línea 2: Espacios disponibles
  lcd.setCursor(0, 1);
  lcd.print("Libres: ");
  lcd.print(freeSpots);
  lcd.print(" de 6");  // Ajustar según total de espacios
}


// ──────────────────────────────────────────────────────────
// 💡 UTILIDADES LED
// ──────────────────────────────────────────────────────────
void blinkLED(int pin, int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, LOW);
    delay(80);
    digitalWrite(pin, HIGH);
    delay(80);
  }
}
