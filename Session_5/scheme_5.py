from connection import connect
from signal import set_signal
import math
import time


connection = connect()

if connection is None:
    exit()

i2c, gpio, port = connection

set_signal(port, {})

# ============================================================
# Анимация
# ============================================================

try:
    print("Запуск анимации. Ctrl+C для выхода.")

    speed = 0.1
    phase = 0.0

    while True:
        print(phase)
        brightness_14 = (math.sin(phase) + 1) / 4
        brightness_15 = (math.sin(phase - math.pi / 4) + 1) / 4

        duty_14 = int(brightness_14 * 4095)
        duty_15 = int(brightness_15 * 4095)

        set_signal(port, {14: duty_14, 15: duty_15})

        phase += speed
        if phase > 2 * math.pi:
            phase -= 2 * math.pi

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nОстановка")

finally:
    set_signal(port, {ch: 0 for ch in range(16)})
    gpio.write(0x00)
    i2c.terminate()
    print("Выключено")