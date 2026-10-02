import time
from pyftdi.gpio import GpioController
from pyftdi.ftdi import Ftdi
from pyftdi.usbtools import UsbTools
import usb.core

from pins_converters import pins_to_mask, states_to_mask, read_to_states

print(usb.core.find(find_all=True), '\n')

devices = False

while not devices:
    try:
        UsbTools.flush_cache()
        devices = Ftdi.list_devices()
    except KeyboardInterrupt:
        exit()

if devices:
    print(devices)
    Ftdi.show_devices()
    print("Найденные FTDI-устройства:", devices)
    url = 'ftdi://ftdi:232h:0:ff/1'
    print(f"Подключаюсь к {url}\n")
    # Подключаемся к FT232H
    gpio = GpioController()
    gpio.configure(
        url='ftdi://ftdi:232h:0:ff/1',
        direction=pins_to_mask('AD1', 'AD3'),
        initial=False,)  # False = 0x00
else:
    print("Устройство не найдено!")
    exit()

# Функция переназначения входящих-выходящих пинов (все сразу через маску)
# gpio.set_direction(0x01, 0x01)  # Второй аргумент задает направление (вход выход), где 0x00 - вход, 0x01 - выход

new_state = {'AD1': False, 'AD3': False}
gpio.write(states_to_mask(new_state))

print("Светодиод горит. Нажми Ctrl+C для выхода.")
try:
    # Держим программу запущенной
    while True:
        time.sleep(1)
        new_state = {'AD1': not new_state['AD1'], 'AD3': not new_state['AD3']}
        gpio.write(states_to_mask(new_state))
        print("Состояние:", read_to_states(gpio.read()))
except KeyboardInterrupt:
    gpio.write(0x00)
    gpio.close()
    print("Светодиод выключен. Чип освобождён.")