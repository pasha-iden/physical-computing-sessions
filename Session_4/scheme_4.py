from pyftdi.i2c import I2cController, I2cNackError
from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools
import math
import time

# --- Поиск чипа ---
devices = False
while not devices:
    try:
        UsbTools.flush_cache()
        devices = Ftdi.list_devices()
    except KeyboardInterrupt:
        exit()

# --- Подключение к чипу ---
if devices:
    descriptor, interface = devices[0]
    url = f"ftdi://ftdi:232h:{descriptor.sn}/{interface}"
    print(f"Подключаюсь к {url}\n")

    i2c = I2cController()
    i2c.configure(url)   # AD7 = выход

    # --- Поднимаем AD7 в HIGH (питание) ---
    gpio = i2c.get_gpio()
    gpio.set_direction(0x80, 0x80)       # принудительно: AD7 = выход
    gpio.write(0x80)                     # AD7 = HIGH
    print("AD7 = HIGH (питание)\n")
    time.sleep(0.1)
else:
    print("Устройство не найдено!")
    exit()


# --- Поиск ШИМ устройства ---
print("Сканирую I2C...")
found = []
for addr in range(0x03, 0x78):
    try:
        port = i2c.get_port(addr)
        port.read(0)
        found.append(addr)
        print(f"  ✓ 0x{addr:02X}")
    except I2cNackError:
        pass


# --- Подключение ШИМ устройства ---
if found:
    print(f"\nНайдены: {[hex(a) for a in found]}")
    addr = 0x40 if 0x40 in found else found[0]
    port = i2c.get_port(addr)
else:
    print("\nНичего не найдено.")
    exit()


# --- ДО ЭТОГО МОМЕНТА - ПОЛНОСТЬЮ АНАЛОГИЧНО SCHEME_3 ---


def write_reg(reg, value):
    port.write_to(reg, bytes([value]))


MODE1 = 0x00
MODE2 = 0x01
PRESCALE = 0xFE

mode1 = port.read_from(MODE1, 1)[0]
write_reg(MODE1, (mode1 & 0x7F) | 0x10)  # MODE1 = SLEEP
write_reg(PRESCALE, 50)  # PRESCALE
write_reg(MODE1, mode1 & ~0x90)  # MODE1 = WAKE
mode2 = port.read_from(MODE2, 1)[0]
write_reg(MODE2, (mode2 & ~0x04) | 0x04)  # MODE2 = totem-pole (push - pull)

# --- ДО ЭТОГО МОМЕНТА - БОЛЕЕ-МЕНЕЕ ТАК ЖЕ, ТОЛЬКО ЧУТЬ УЛУЧШЕНО И БЕЗ КОММЕНТАРИЕВ


print("PCA9685 инициализирован\n")

# ============================================================
# Явные адреса для каналов 14 и 15
# ============================================================

# Канал 14: base = 0x06 + 4*14 = 0x3E
CH14_ON_L = 0x3E
CH14_ON_H = 0x3F
CH14_OFF_L = 0x40
CH14_OFF_H = 0x41

# Канал 15: base = 0x06 + 4*15 = 0x42
CH15_ON_L = 0x42
CH15_ON_H = 0x43
CH15_OFF_L = 0x44
CH15_OFF_H = 0x45


def set_brightness_ch14(value):
    """value: 0..4095"""  # value = max(0, min(4095, int(value)))
    write_reg(CH14_ON_L, 0x00)
    write_reg(CH14_ON_H, 0x00)
    write_reg(CH14_OFF_L, value & 0xFF)
    write_reg(CH14_OFF_H, (value >> 8) & 0x0F)


def set_brightness_ch15(value):
    """value: 0..4095"""  # value = max(0, min(4095, int(value)))
    write_reg(CH15_ON_L, 0x00)
    write_reg(CH15_ON_H, 0x00)
    write_reg(CH15_OFF_L, value & 0xFF)
    write_reg(CH15_OFF_H, (value >> 8) & 0x0F)


# ============================================================
# Анимация
# ============================================================

try:
    print("Запуск анимации. Ctrl+C для выхода.")

    speed = 0.1
    phase = 0.0

    while True:
        print(phase)
        # Синусоида для канала 14
        brightness_14 = (math.sin(phase) + 1) / 4
        # Синусоида для канала 15 со сдвигом на 180 градусов
        brightness_15 = (math.sin(phase - math.pi / 4) + 1) / 4

        duty_14 = int(brightness_14 * 4095)
        duty_15 = int(brightness_15 * 4095)

        set_brightness_ch14(duty_14)
        set_brightness_ch15(duty_15)

        phase += speed
        if phase > 2 * math.pi:
            phase -= 2 * math.pi

        time.sleep(0.001)

except KeyboardInterrupt:
    print("\nОстановка")

finally:
    set_brightness_ch14(0)
    set_brightness_ch15(0)
    gpio.write(0x00)
    i2c.terminate()
    print("Выключено")