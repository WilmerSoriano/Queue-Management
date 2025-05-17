import machine


class Button:
    
    def __init__(self, pin):
                               #(GPIO, ReadSignal from button, isResistor ON/Off)
        self.button = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.previous_button_status = self.button.value()

    def is_pressed(self):
        current_button_status = self.button.value()
        
        # Detect only when the button changes from NOT PRESSED = (1) to PRESSED = (0)
        if current_button_status == 0 and self.previous_button_status == 1:
            self.previous_button_status = current_button_status
            return True  # Button was just pressed
        
        self.previous_button_status = current_button_status
        return False  # No new press detected
