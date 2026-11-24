# ============================================
# GRÁFICAS EN TIEMPO REAL - graficas_tiempo_real.py
# Lee las tramas JSON que envía el ESP32 (firmware/main.py) y grafica
# aceleración (X, Y, Z), velocidad angular (X, Y, Z) y temperatura.
# Uso:  python graficas_tiempo_real.py COM7
# ============================================
import sys
import json
import time
from collections import deque

import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "COM7"
BAUDIOS = 115200
VENTANA = 200            # 200 muestras = 10 s a 20 Hz
LSB_G = 16384.0          # acelerómetro en ±2 g
LSB_DPS = 131.0          # giroscopio en ±250 °/s

ser = serial.Serial(PUERTO, BAUDIOS, timeout=0.05)
print(f"Leyendo {PUERTO} a {BAUDIOS} bps... (cierra Thonny antes)")

t = deque(maxlen=VENTANA)
acc = [deque(maxlen=VENTANA) for _ in range(3)]
gir = [deque(maxlen=VENTANA) for _ in range(3)]
tmp = deque(maxlen=VENTANA)
t0 = time.time()

fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
fig.suptitle("MPU6050 en tiempo real")
colores = ("#C0392B", "#0F8B8D", "#1F3A68")
l_acc = [a1.plot([], [], c, label=e)[0] for c, e in zip(colores, "XYZ")]
l_gir = [a2.plot([], [], c, label=e)[0] for c, e in zip(colores, "XYZ")]
l_tmp, = a3.plot([], [], "#E07A1F")
a1.set_ylabel("Aceleración [g]"); a1.set_ylim(-2.1, 2.1); a1.legend(loc="upper left", ncol=3)
a2.set_ylabel("Vel. angular [°/s]"); a2.set_ylim(-260, 260); a2.legend(loc="upper left", ncol=3)
a3.set_ylabel("Temperatura [°C]"); a3.set_xlabel("Tiempo [s]")
for a in (a1, a2, a3):
    a.grid(alpha=0.3)


def leer_tramas():
    """Lee todas las líneas disponibles para no acumular retardo."""
    while ser.in_waiting:
        linea = ser.readline().decode("utf-8", errors="ignore").strip()
        if not (linea.startswith("{") and linea.endswith("}")):
            continue                      # trama cortada o texto del REPL
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        if "error" in d:
            print("Error del sensor:", d["error"])
            continue
        t.append(time.time() - t0)
        for i, k in enumerate(("ax", "ay", "az")):
            acc[i].append(d[k] / LSB_G)
        for i, k in enumerate(("gx", "gy", "gz")):
            gir[i].append(d[k] / LSB_DPS)
        tmp.append(d["t"])


def actualizar(_):
    leer_tramas()
    if len(t) < 2:
        return []
    for linea, datos in zip(l_acc + l_gir, acc + gir):
        linea.set_data(t, datos)
    l_tmp.set_data(t, tmp)
    a1.set_xlim(t[0], max(t[-1], t[0] + 1))
    a3.set_ylim(min(tmp) - 0.5, max(tmp) + 0.5)
    f = (len(t) - 1) / (t[-1] - t[0])     # frecuencia medida en la ventana
    fig.suptitle(f"MPU6050 en tiempo real  |  {f:.1f} Hz medidos")
    return l_acc + l_gir + [l_tmp]


ani = FuncAnimation(fig, actualizar, interval=50, cache_frame_data=False)
try:
    plt.show()
finally:
    ser.close()
