Прошивка чипа ft232h:
    Программа FT_Prog
        Нажать лупу, чтобы ПО нашло чип
        Выбрать Hardware Specific -> Port A -> Hardware
            В правом окне выбрать 245 FIFO
            Нажать молнию
                В открывшемся окне нажать Program

Примечание: если в чипе уже изменен драйвер - его нужно откатить
через диспетчер устройств на 
    USB Serial Converter Версия: 2.12.36.20 [28.10.2024]

Обновление драйвера ft232h:
    Программа Zadig (ccылка zadig.akeo.ie)
        Выбрать устройство: Single RS232-HS (USB ID 0403 6014)
        Поставить драйвер libusbK
        
Python dependencies
    pip install pyusb
    pip install pyftdi

