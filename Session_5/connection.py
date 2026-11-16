from pyftdi.i2c import I2cController, I2cNackError
from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools
import time


def connect():
    # --- Поиск чипа ---
    devices = False
    while not devices:
        try:
            UsbTools.flush_cache()
            devices = Ftdi.list_devices()
        except KeyboardInterrupt:
            return None

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
        return None

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
        return None

    def write_reg(reg, value):
        port.write_to(reg, bytes([value]))

    MODE1 = 0x00
    MODE2 = 0x01
    PRESCALE = 0xFE

    mode1 = port.read_from(MODE1, 1)[0]
    write_reg(MODE1, (mode1 & 0x7F) | 0x10)  # MODE1 = SLEEP
    write_reg(PRESCALE, 5)  # PRESCALE
    write_reg(MODE1, mode1 & ~0x90)  # MODE1 = WAKE
    mode2 = port.read_from(MODE2, 1)[0]
    write_reg(MODE2, (mode2 & ~0x04) | 0x04)  # MODE2 = totem-pole (push - pull)
    write_reg(MODE1, port.read_from(MODE1, 1)[0] | 0x20)  # AI (Auto-Increment) = 1

    print("PCA9685 инициализирован\n")

    return i2c, gpio, port