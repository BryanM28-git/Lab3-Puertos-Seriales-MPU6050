# ============================================
# CÓDIGO ESP32 - main.py (MicroPython)
# ============================================
from machine import Pin, I2C, Timer
import struct
import json

# --- CONFIGURACIÓN DEL BUS I2C ---
# SDA en GPIO 21 y SCL en GPIO 22 (Pines por defecto en ESP32)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
MPU_ADDR = 0x68

# Despertar el MPU6050 (escribir 0 en el registro de Power Management 0x6B)
i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00')

def leer_sensor(timer):
    """
    Función llamada por la interrupción del temporizador.
    Lee los registros del MPU6050 y los envía por el puerto serial.
    """
    try:
        # Leer 14 bytes continuos desde el registro 0x3B 
        # Esto incluye: Acel(6) + Temp(2) + Gyro(6)
        data = i2c.readfrom_mem(MPU_ADDR, 0x3B, 14)
        
        # Desempaquetar los 14 bytes en 7 enteros de 16 bits con signo (>h)
        vals = struct.unpack('>hhhhhhh', data)
        
        # Estructurar los datos en un diccionario
        # Temperatura: Fórmula del datasheet (Temp_RAW / 340.0 + 36.53)
        paquete = {
            "ax": vals[0], 
            "ay": vals[1], 
            "az": vals[2],
            "t":  round(vals[3] / 340.0 + 36.53, 2), 
            "gx": vals[4], 
            "gy": vals[5], 
            "gz": vals[6]
        }
        
        # Convertir a JSON y enviar por el puerto serial COM
        print(json.dumps(paquete))
        
    except Exception as e:
        # Manejo de errores por si hay fallas en la línea I2C
        print(json.dumps({"error": str(e)}))

# --- TEMPORIZADOR A 20 HZ ---
# Se configura un Timer para llamar a la función leer_sensor cada 50 ms (20 veces por segundo)
tim = Timer(0)
tim.init(period=50, mode=Timer.PERIODIC, callback=leer_sensor)

# Bucle principal vacío, el hardware se encarga de las interrupciones
while True:
    pass