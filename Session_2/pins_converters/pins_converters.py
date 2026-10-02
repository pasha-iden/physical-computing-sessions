def _parse_pin(pin):
    """
    Превращает 'AD0'..'AD7' в номер бита (0..7).
    Принимает только строки в формате 'ADx'.
    Регистр не важен: 'ad0', 'Ad0', 'AD0' — всё валидно.
    """
    if not isinstance(pin, str):
        raise TypeError(f"Пин должен быть строкой 'ADx', получено: {type(pin)}")

    name = pin.upper().strip()
    if not name.startswith('AD'):
        raise ValueError(f"Пин должен начинаться с 'AD', получено: {pin}")

    num_str = name[2:]
    if not num_str.isdigit():
        raise ValueError(f"После 'AD' должно быть число, получено: {pin}")

    num = int(num_str)
    if not 0 <= num <= 7:
        raise ValueError(f"Номер пина должен быть 0..7, получено: {pin}")
    return num


def pins_to_mask(*pins):
    """
    Принимает произвольное количество пинов и возвращает битовую маску.
    Пин — строка вида 'AD0'..'AD7'.

    Примеры:
      pins_to_mask('AD0', 'AD2')     -> 0x05
      pins_to_mask('AD1')            -> 0x02
      pins_to_mask('AD1', 'AD3')     -> 0x0A
      pins_to_mask()                 -> 0x00
    """
    mask = 0
    for pin in pins:
        mask |= 1 << _parse_pin(pin)
    return mask


def states_to_mask(states):
    """
    Принимает словарь {пин: True/False} и возвращает битовую маску.
    True  -> бит = 1 (HIGH)
    False -> бит = 0 (LOW)

    Примеры:
      states_to_mask({'AD0': True})               -> 0x01
      states_to_mask({'AD1': True, 'AD3': False}) -> 0x02
      states_to_mask({0: True, 2: False})         -> 0x01
    """
    mask = 0
    for pin, value in states.items():
        bit = _parse_pin(pin)
        if value:
            mask |= 1 << bit
        else:
            mask &= ~(1 << bit)
    return mask


def read_to_states(value):
    """
    Превращает результат gpio.read() в словарь {пин: True/False}.
    Бит = 1 -> True (HIGH), бит = 0 -> False (LOW).

    Примеры:
      read_to_states(0x00) -> {'AD0': False, 'AD1': False, ..., 'AD7': False}
      read_to_states(0x02) -> {'AD0': False, 'AD1': True,  ..., 'AD7': False}
      read_to_states(0x05) -> {'AD0': True,  'AD1': False, 'AD2': True, ...}
    """
    return {f'AD{bit}': bool(value & (1 << bit)) for bit in range(8)}


def set_pin(mask, pin, value):
    """
    Устанавливает или сбрасывает бит пина в маске.

    mask  — текущая битовая маска
    pin   — строка 'ADx' (например, 'AD1')
    value — True (установить в HIGH) или False (сбросить в LOW)

    Примеры:
      set_pin(0x00, 'AD3', True)   -> 0x08
      set_pin(0x08, 'AD3', False)  -> 0x00
      set_pin(0x0A, 'AD0', False)  -> 0x0A  (AD0 там и не было)
    """
    bit = _parse_pin(pin)
    if value:
        return mask | (1 << bit)  # установить бит
    else:
        return mask & ~(1 << bit)  # сбросить бит