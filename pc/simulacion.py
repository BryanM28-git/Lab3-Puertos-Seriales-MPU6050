# ============================================
# SIMULACIÓN Y LECTURA EN VS CODE - simulacion.py
# ============================================
import pybullet as p
import pybullet_data
import time
import serial
import json
import math

# --- CONFIGURACIÓN DEL PUERTO SERIE ---
try:
    print("🔌 Conectando a ESP32 en COM7...")
    # Asegúrate de cerrar cualquier otra terminal o programa (como el monitor de MicroPython)
    ser = serial.Serial('COM7', 115200, timeout=0.1)
    print("✅ ESP32 conectada exitosamente en COM7")
    esp_conectado = True
except Exception as e:
    print(f"❌ Error al conectar: {e}")
    esp_conectado = False
    ser = None

# --- INICIALIZAR PYBULLET ---
print("🔄 Iniciando entorno 3D...")
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)

# Crear un suelo y un modelo 3D que representará el sensor (más plano)
plane_id = p.loadURDF("plane.urdf")
cube_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.5, 0.5, 0.1])
cube_id = p.createMultiBody(1.0, cube_shape, basePosition=[0, 0, 1])

print("\n" + "="*50)
print("🎯 SISTEMA DE ADQUISICIÓN Y VISUALIZACIÓN EN TIEMPO REAL")
print("="*50 + "\n")

try:
    while True:
        # 1. LEER DATOS ESTRUCTURADOS DEL ESP32
        if esp_conectado and ser and ser.in_waiting > 0:
            try:
                linea = ser.readline().decode('utf-8').strip()
                
                # Validar que sea una trama JSON
                if linea.startswith("{") and linea.endswith("}"):
                    datos = json.loads(linea)
                    
                    if "error" in datos:
                        print(f"Error en el sensor: {datos['error']}")
                        continue

                    # Extraer variables
                    ax, ay, az = datos["ax"], datos["ay"], datos["az"]
                    gx, gy, gz = datos["gx"], datos["gy"], datos["gz"]
                    temp = datos["t"]
                    
                    # Mostrar las variables en consola según el requerimiento
                    print(f"Temp: {temp}°C | Acel: ({ax}, {ay}, {az}) | Giro: ({gx}, {gy}, {gz})")

                    # 2. CÁLCULO DE ORIENTACIÓN TRIDIMENSIONAL
                    # Evitar divisiones por cero en caídas libres
                    if az == 0: az = 0.001 
                    
                    # Calcular ángulos Roll (Alabeo) y Pitch (Cabeceo) usando el acelerómetro
                    roll = math.atan2(ay, az)
                    pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2))
                    yaw = 0  # Requiere magnetómetro para guiñada real
                    
                    # Convertir ángulos de Euler a Cuaternión para PyBullet
                    quaternion = p.getQuaternionFromEuler([roll, pitch, yaw])
                    
                    # 3. ACTUALIZAR POSICIÓN EN LA INTERFAZ
                    p.resetBasePositionAndOrientation(
                        cube_id, 
                        [0, 0, 1],       # Mantiene el objeto flotando a 1 metro
                        quaternion       # Aplica la rotación física del sensor
                    )
            except json.JSONDecodeError:
                pass # Se ignora si un paquete llega cortado o con ruido serial
            except Exception as e:
                pass 

        # Avanzar el motor de la simulación gráfica
        p.stepSimulation()
        time.sleep(1/240)

except KeyboardInterrupt:
    print("\n🛑 Ejecución detenida por el usuario")
finally:
    if ser:
        ser.close()
        print("🔌 Conexión serial liberada")
    p.disconnect()
    print("👋 Simulación finalizada")