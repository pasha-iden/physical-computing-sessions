from pyftdi.i2c import I2cController, I2cNackError  # Объект для работы с другим режимом чипа (I2C, включающим в себя GPIO)
from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools
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


# ============================================================
# PCA9685 — инициализация
# ============================================================

MODE1 = 0x00  # адрес регистра Mode 1 (общие настройки чипа)
MODE2 = 0x01  # адрес регистра Mode 2 (настройки выходов)
PRESCALE = 0xFE  # адрес регистра предделителя частоты ШИМ

def write_reg(reg, value):
    port.write_to(reg, bytes([value]))

# Настройка частоты ШИМ 1000 Гц
mode1 = port.read_from(MODE1, 1)[0]  #  Чтение текущего MODE1 (Возвращает массив байтов и читает 1 байт из регистра MODE1 (0x00))
    # Нужно, чтобы не сбросить важные биты, которые уже настроены в MODE1 (например, RESTART, AI, EXTCLK).
    # Так сохраняется текущее состояние, чтобы потом вернуть его с изменениями.
write_reg(MODE1, (mode1 & 0x7F) | 0x10)  # SLEEP
    # mode1 & 0x7F — берёт текущее значение mode1 и сбрасывает бит 7 (RESTART).
    # | 0x10 — устанавливает бит 4 (SLEEP) в 1.
    # Чип уходит в спящий режим. ШИМ-генератор останавливается. Это нужно, чтобы безопасно изменить частоту в PRESCALE
prescale = int(25000000 / (4096 * 1000) - 1)
    # 25000000 — внутренняя частота осциллятора PCA9685 (25 МГц).
    # 4096 — количество шагов ШИМ (12 бит, от 0 до 4095).
    # 1000 — желаемая частота ШИМ в герцах.
write_reg(PRESCALE, prescale)
    # Записывает 5 в регистр 0xFE. Теперь чип знает: «чтобы получить 1000 Гц, дели частоту 25 МГц на 5+1 и ещё на 4096».
write_reg(MODE1, mode1 & ~0x90)  # Сброс RESTART и SLEEP  # WAKE
    # Берёт сохранённое значение mode1 и сбрасывает бит 7 (RESTART)
    # Чип просыпается. ШИМ-генератор запускается с новой частотой.
write_reg(MODE2, 0x04)  # Настройка выходов (totem-pole output)
    # 0x04 - устанавливает бит 2 (OUTDRV) в 1.
    # OUTDRV = 1 → выходы работают в режиме totem-pole (push-pull): могут активно тянуть вверх (к V+) и вниз (к GND).
    # OUTDRV = 0 → выходы open-drain: только тянут вниз, вверх — через внешний pull-up.

print("\nPCA9685 инициализирован\n")

# ============================================================
# Перебор каналов 0–15 (Full ON через бит 4)
# ============================================================

LED0_ON_L = 0x06

print("Перебираю каналы 0–15...")
print("Смотри, на каком загорится светодиод.\n")

try:
    for ch in range(16):
        base = LED0_ON_L + 4 * ch

        # Full ON: ON_H = 0x10 (бит 4)
        write_reg(base + 1, 0x10)  # LEDx_ON_H = Full ON
        write_reg(base + 3, 0x00)  # LEDx_OFF_H = 0
        data = port.read_from(base, 4)

        print(f"  Канал {ch} (регистр 0x{base:02X}) — ВКЛ")
        time.sleep(1)

        # Выключаем: Full OFF
        write_reg(base + 1, 0x00)
        write_reg(base + 3, 0x10)  # LEDx_OFF_H = Full OFF
        print(f"  Канал {ch} — выкл")

except KeyboardInterrupt:
    print("\nПрервано.")

finally:
    # Гасим все каналы (Full OFF)
    for ch in range(16):
        base = LED0_ON_L + 4 * ch
        # Выключаем: Full OFF
        write_reg(base + 1, 0x00)
        write_reg(base + 3, 0x10)  # LEDx_OFF_H = Full OFF

    gpio.write(0x00)
    i2c.terminate()
    print("Все каналы выключены.")