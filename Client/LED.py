import machine


# UPDATED, LED now handles dynamic color Red, Geen , and Orange
class LED:
    def __init__(self, pin, active_high=True):
        self.pin = machine.Pin(pin, machine.Pin.OUT)
        self.active_high = active_high

    def on(self):
        self.pin.value(self.active_high)

    def off(self):
        self.pin.value(not self.active_high)

    def toggle(self):
        self.pin.value(not self.pin.value())

class Orange:
    def __init__(self, red_pin, green_pin, active_high=True):
        self.red = LED(red_pin, active_high)
        self.green = LED(green_pin, active_high)
    
    def on(self):
        self.red.on()
        self.green.on()
    
    def off(self):
        self.red.off()
        self.green.off()