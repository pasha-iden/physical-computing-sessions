# Текущее состояние всех 16 каналов
brightness_state = [0] * 16


def set_signal(port, channels):
    """
    channels: {канал: яркость}
    Пример:
        set_signal(port, {3: 1024, 5: 2048})
    Неуказанные каналы сохраняют прежнюю яркость.
    """

    # Сначала проверяем входные данные
    for channel in channels:
        if not isinstance(channel, int) or not 0 <= channel < 16:
            raise ValueError(f"Неверный канал: {channel}")

    # Обновляем сохранённые значения
    for channel, value in channels.items():
        brightness_state[channel] = max(0, min(4095, int(value)))

    # Формируем данные для всех 16 каналов
    data = bytearray()

    for value in brightness_state:
        if value == 0:
            data.extend([0x00, 0x00, 0x00, 0x10])  # FULL OFF
        else:
            data.extend([
                0x00,                   # ON_L
                0x00,                   # ON_H
                value & 0xFF,           # OFF_L
                (value >> 8) & 0x0F     # OFF_H
            ])

    # Одна I²C-транзакция для всех 16 каналов
    port.write_to(0x06, data)