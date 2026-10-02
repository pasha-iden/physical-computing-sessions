import time
from pyftdi.gpio import GpioController  # Объект управления gpio пинами -- основной инструмент
from pyftdi.ftdi import Ftdi  # Объект чипа
from pyftdi.usbtools import UsbTools  # Объект управления usb
import usb.core  # Метод работы с usb

print(usb.core.find(find_all=True), '\n')  # список всех USB-устройств

devices = False

while not devices:  # Ожидание подключения чипа по usb
    try:
        UsbTools.flush_cache()  # Сброс данных о чипах, подключенных по usb
        devices = Ftdi.list_devices()  # Получение списка чипов, подключенных по usb
    except KeyboardInterrupt:
        exit()

if devices:
    print(devices)
    Ftdi.show_devices()  # Вывод системных данных о чипе
    print("Найденные FTDI-устройства:", devices)
    url = 'ftdi://ftdi:232h:0:ff/1'  # Адрес подключения к чипу (передается в объект управления пинами)
    print(f"Подключаюсь к {url}\n")
    # Подключаемся к FT232H
    gpio = GpioController()  # Инициализация объекта управления пинами
    gpio.configure(  # Конфигурация объекта управления пинами
        url='ftdi://ftdi:232h:0:ff/1',  # Передача адреса управления пинами
        direction=0x02,  # Пины (их маска), которые будут назначены на выход (в данном случае - AD1)
        initial=0x00,)  # Задание изначальных сигналов (маска) всех пинов (в данном случае - LOW - нет сигнала)
else:
    print("Устройство не найдено!")
    exit()

# Функция переназначения входящих-выходящих пинов (все сразу через маску)
# gpio.set_direction(0x01, 0x01)  # Второй аргумент задает направление (вход выход), где 0x00 - вход, 0x01 - выход

light = False * 2  # Начальный сигнал на второй пин (AD1) [Временное неправильное решение]

# Переопределение значений всех сигналов на пинах (все разом через маску)
gpio.write(light)

print("Светодиод горит. Нажми Ctrl+C для выхода.")
try:
    # Держим программу запущенной
    while True:
        time.sleep(1)
        light = (not light) * 2  # Смена значения на втором пине (AD1) [Временное неправильное решение]
        gpio.write(light)  # Переопределение значений всех сигналов на пинах (все разом через маску)
        print("Состояние:", hex(gpio.read()))  # Чтение текущего значения на всех пинах
except KeyboardInterrupt:
    # Выключаем светодиод перед выходом
    gpio.write(0x00)
    gpio.close()  # Завершение связи с чипом
    print("Светодиод выключен. Чип освобождён.")