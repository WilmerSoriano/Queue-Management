import socket
import sys
import time

import machine
import network
import uos
from button import Button
from DIP import ID_num
from led import LED, Orange

# ==================== Configuration ====================
SSID = 'skynet' #PicoTest
PASSWORD = 't3rm1n4t0r' #qwerty123
SERVER_IP = "192.168.1.22"#192.168.4.1
SERVER_PORT = 12000
DEVICE_ID = ID_num() 

# Hardware pins (verify these match your wiring)
GREEN_BUTTON_PIN = 8
GREEN_LED_PIN = 12

RED_BUTTON_PIN = 28
RED_LED_PIN = 15

# ==================== WiFi Connection ==================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("Connecting to WiFi", end='')
    for _ in range(15):
        if wlan.isconnected():
            print("\nConnected!")
            print("IP:", wlan.ifconfig()[0])
            return True
        print(".", end='')
        time.sleep(1)
    print("\nConnection failed!")
    return False

# ==================== Device Registration ==============
def register_device(sock):
    print("Attempting registration...")
    retries = 3
    for attempt in range(retries):
        try:
            sock.sendto(b"HELLO", (SERVER_IP, SERVER_PORT))
            sock.settimeout(5)  # 5 second timeout for registration
            response, addr = sock.recvfrom(128)
            
            if response.startswith(b"ID:"):
                device_id = int(response.split(b":")[1])
                print(f"Registered as Device {device_id}")
                return device_id
                
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            time.sleep(1)
    
    print("Registration failed after 3 attempts")
    raise RuntimeError("Registration timeout")

# ==================== Part 1. Main Program =====================
try:
    # Initialize hardware
    green_led = LED(GREEN_LED_PIN)
    red_led = LED(RED_LED_PIN)
    orange_led = Orange(GREEN_LED_PIN, RED_LED_PIN)
    
    green_button = Button(GREEN_BUTTON_PIN)
    red_button = Button(RED_BUTTON_PIN)
    
    green_active = False
    red_active = False
    
    # Display Orange on and off to indicate connecting to Wifi
    for _ in range(5):
        orange_led.on()
        time.sleep(0.3)
        orange_led.off()
        time.sleep(0.3)
        orange_led.on()
        
    # Connect to WiFi
    if not connect_wifi():
        orange_led.off()
        raise RuntimeError("WiFi connection failed")
    orange_led.off()
    
    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0)

    # Check for existing device ID
    try:
        if DEVICE_ID:
            device_id = int(DEVICE_ID)
            print(f"Device ID: {device_id}")
    except:
        device_id = register_device(sock)

# =============== Part 2. MESSAGE Handler ===============
    print("Ready for operation!")
    for _ in range(10):
        green_led.on()
        time.sleep(0.3)
        green_led.off()
        time.sleep(0.3)
    green_led.off()
        
    while True:
        # [1] Check for server messages, Server may ask to turn off LED
        try:
            data, _ = sock.recvfrom(1024)
            decoded = data.decode().strip()
            if decoded.startswith("LED_OFF"):
                color = decoded.split(':')[1].lower()
                if color == 'red':
                    red_led.off()
                    red_active = False
                    print("Server: Red LED turned off")
                elif color == 'green':
                    green_led.off()
                    green_active = False
                    print("Server: Green LED turned off")
        except OSError as e:
            if e.args[0] == 11:  # EAGAIN (no data available)
                pass  # Normal non-blocking behavior
            else:
                print("Error:", e)
        except Exception as e:
            print("Error:", e)
            
# ================= Part 3. User presses a Button =================
        # [2] Handle button presses
        green_pressed = green_button.is_pressed()
        red_pressed = red_button.is_pressed()
        status = None

        # Handle simultaneous press first
        if green_pressed and red_pressed:
            print("Orange!")
            orange_led.off()
            green_active = False
            red_active = False
            status = "off"
        else:
            # Handle green button toggle
            if green_pressed:
                green_led.toggle()
                green_active = not green_active
                status = "green" if green_active else "off"
                print("Client: green pressed")
                
            # Handle red button toggle
            if red_pressed:
                red_led.toggle()
                red_active = not red_active
                status = "red" if red_active else "off"
                print("Client: Red pressed")

        # Send status update
        if status:
            try:
                message = f"ID:{device_id},status:{status}"
                sock.sendto(message.encode(), (SERVER_IP, SERVER_PORT))
            except Exception as e:
                print(f"Send error: {str(e)}")

        time.sleep(1)

except Exception as e:
    # LED indicate red when issue has been encounter
    for _ in range(10):
        red_led.on()
        time.sleep(0.3)
        red_led.off()
        time.sleep(0.3)
        red_led.on()
        
    red_led.off()
    print("Error encounter:", str(e))
finally:
    green_led.off()
    red_led.off()
    orange_led.off()
    if 'sock' in locals():
        sock.close()
    print("Shutdown complete")
    sys.exit()
