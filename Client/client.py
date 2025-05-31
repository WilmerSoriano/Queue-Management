import socket
import time

import machine
import network
from button import Button
from config_manager import load_config, reset_config
from led import LED, Orange
from wifi_setup import start_setup_portal

# ==================== Hardware Pins ====================
GREEN_BUTTON_PIN = 15
GREEN_LED_PIN = 13
RED_BUTTON_PIN = 16
RED_LED_PIN = 18
# Connecting to Server
SERVER_PORT = 12000

# ==================== WiFi Connection ==================
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    print(f"Connecting to {ssid}", end='')
    for _ in range(15):
        if wlan.isconnected():
            print("\nConnected!")
            return True
        print(".", end='')
        time.sleep(1)
    print("\nConnection failed!")
    return False

# ==================== Main Program =====================
try:
    # Initialize hardware
    green_led = LED(GREEN_LED_PIN)
    red_led = LED(RED_LED_PIN)
    
    green_button = Button(GREEN_BUTTON_PIN)
    red_button = Button(RED_BUTTON_PIN)
    
    orange_led = Orange(GREEN_LED_PIN, RED_LED_PIN)
    
    # Blink LEDs to indicate setup mode
    def blink_setup_mode():
        for _ in range(5):
            orange_led.on()
            time.sleep(0.3)
            orange_led.off()
            time.sleep(0.3)
            orange_led.on()
    
    # Load wifi-config file 
    config = load_config()
    
    # Start setup portal if no config exists
    if not config:
        print("No Wifi-config found - starting setup portal")
        blink_setup_mode()
        start_setup_portal()
        orange_led.off()
    else:
        print("Loaded config:", config)
        for _ in range(5):# Indicating to user, set up was success!
            green_led.on()
            time.sleep(0.2)
            green_led.off()
            time.sleep(0.2)
    
    # Use configuration values
    SSID = config["ssid"]
    PASSWORD = config["password"]
    SERVER_IP = config["server_ip"]
    DEVICE_ID = config["device_id"]
    
    print(f"Device ID: {DEVICE_ID}")
    print(f"Server IP: {SERVER_IP}")
    
    # Connect to WiFi
    if not connect_wifi(SSID, PASSWORD):
        # Connection failed - reset config and reboot
        for _ in range(5):
            red_led.on()
            time.sleep(0.2)
            red_led.off()
            time.sleep(0.2)
            
        reset_config()
        machine.reset()

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0)  # Non-blocking mode

# =============== Main Operation Loop ===============
    print("Ready for operation!")
    green_active = False
    red_active = False
    last_reset_check = time.time()
    
    while True:
        
        # Handle incoming messages from server(TA pressed button from monitor)
        try:
            data, _ = sock.recvfrom(1024)
            decoded = data.decode().strip()
            if decoded.startswith("LED_OFF"):
                color = decoded.split(':')[1].lower()
                if color == 'red':
                    red_led.off()
                    red_active = False
                elif color == 'green':
                    green_led.off()
                    green_active = False
        except:
            pass
        
        # Handle button presses
        green_pressed = green_button.is_pressed()
        red_pressed = red_button.is_pressed()
        status = None

        if green_pressed and red_pressed:
            print("Resetting Wifi-configuration")
            blink_setup_mode()
            reset_config()
            machine.reset()
            
        else:
            if green_pressed:
                green_led.toggle()
                green_active = not green_active
                status = "green" if green_active else "off"
                print("Green on!")#debugging
            if red_pressed:
                red_led.toggle()
                red_active = not red_active
                status = "red" if red_active else "off"
                print("Red on!")

        # Send status update if changed
        if status:
            try:
                message = f"ID:{DEVICE_ID},status:{status}"
                sock.sendto(message.encode(), (SERVER_IP, SERVER_PORT))
            except:
                pass

        time.sleep(0.1)

except Exception as e:
    print("Fatal error:", e)
    # Error indication
    for _ in range(10):
        red_led.on()
        time.sleep(0.2)
        red_led.off()
        time.sleep(0.2)
finally:
    green_led.off()
    red_led.off()
    if 'sock' in locals():
        sock.close()
    print("Shutdown complete")