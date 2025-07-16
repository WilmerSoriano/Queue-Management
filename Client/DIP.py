from machine import Pin

# GPIO pins connected to DIP switches (bit 0 to bit 5)(GP0 to GP5 on Pico)
switch_pins = [0, 1, 2, 3, 4, 5]  # Can expand later to [0, 1, 2, 3, 4, 5]

switches = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in switch_pins]

def ID_num():
    value = 0
    for i, sw in enumerate(switches):
        if not sw.value():  # Switch is ON
            value |= (1 << i)  # Set bit i
    return value