import socket
import sys
import time

import machine
import network
import uos
from button import Button
from LED import LED

# ==================== Configuration ====================
SSID = '' #skynet FUTURE UPDATE:skynet CANNOT be hard coded WiFi Password, implement dynamic WiFi
PASSWORD = ''
SERVER_IP = ""  # Verify this IP matches your server! #FUTURE UPDATE: Client must update when connecting to Server
SERVER_PORT = 12000
DEVICE_ID = 20 # Number All device hardcoded and add Sticker to Number each device

# Hardware pins (verify these match your wiring)
GREEN_BUTTON_PIN = 15
GREEN_LED_PIN = 13

RED_BUTTON_PIN = 16
RED_LED_PIN = 18

# ==================== WiFi Connection ==================
def connect_wifi():
    global green_led, red_led  # Access the LED objects created later
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    # Orange LED is on!
    green_led.on()
    red_led.on()
    
    print("Connecting to WiFi", end='')
    for _ in range(15):
        if wlan.isconnected():
            print("\nConnected!")
            print("IP:", wlan.ifconfig()[0])
            green_led.off()
            red_led.off()
            return True
        print(".", end='')
        time.sleep(1)
    print("\nConnection failed!")
    return False

# ==================== Device Registration ============== FUTURE UPDATE: Server must handle incoming new devices and assigning ID
def register_device(sock):
    print("Attempting registration...")
    retries = 3
    # In this loop, the Pico send message and Server would ask for ID
    for attempt in range(retries):
        try:
            sock.sendto(b"HELLO", (SERVER_IP, SERVER_PORT))
            sock.settimeout(5)  # 5 second timeout for registration
            response, addr = sock.recvfrom(128)
            
            if response.startswith(b"ID:"):
                device_id = int(response.split(b":")[1])
                with open(DEVICE_ID, "w") as f:
                    f.write(str(device_id))
                print(f"Registered as Device {device_id}")
                return device_id
                
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            time.sleep(1)
    
    print("Registration failed after 3 attempts")
    raise RuntimeError("Registration timeout")

# ==================== Main Program =====================
try:
    # Initialize hardware
    green_led = LED(GREEN_LED_PIN)
    red_led = LED(RED_LED_PIN)
    green_button = Button(GREEN_BUTTON_PIN)
    red_button = Button(RED_BUTTON_PIN)
    green_active = False
    red_active = False
    
    # Connect to WiFi
    if not connect_wifi():
        raise RuntimeError("WiFi connection failed")

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0)  # Normal operation timeout

    # Check for existing device ID
    try:
        if DEVICE_ID:
            device_id = int(DEVICE_ID)
            print(f"Device ID: {device_id}")
    except:
        device_id = register_device(sock)

# =============== MESSAGE Handler ===============
    print("Ready for operation!")
    while True:
        # [1] Check for server messages
        try:
            data, _ = sock.recvfrom(1024)
            decoded = data.decode().strip()
            if decoded.startswith("LED_OFF"):
                color = decoded.split(':')[1].lower()
                if color == 'red':
                    red_led.off()
                    red_active = False
                    print("Red LED turned off")
                elif color == 'green':
                    green_led.off()
                    green_active = False
                    print("Green LED turned off")
        except OSError as e:
            if e.args[0] == 11:  # EAGAIN (no data available)
                pass  # Normal non-blocking behavior
            else:
                print("Error:", e)
        except Exception as e:
            print("Error:", e)
        
        # [2] Handle button presses
        green_pressed = green_button.is_pressed()
        red_pressed = red_button.is_pressed()
        status = None

        # Handle simultaneous press first # FUTURE UPDATE: MUST handle any possible button combination
        if green_pressed and red_pressed:
            print("PASSED!!!")
            green_led.off()
            red_led.off()
            green_active = False
            red_active = False
            status = "off"
        else:
            # Handle green button toggle
            if green_pressed:
                green_led.toggle()
                green_active = not green_active
                status = "green" if green_active else "off"
                print("green")
                
            # Handle red button toggle
            if red_pressed:
                red_led.toggle()
                red_active = not red_active
                status = "red" if red_active else "off"
                print("red")

        # Send status update
        if status:
            try:
                message = f"ID:{device_id},status:{status}"
                sock.sendto(message.encode(), (SERVER_IP, SERVER_PORT))
            except Exception as e:
                print(f"Send error: {str(e)}")

        time.sleep(1)

except Exception as e:
    print("Fatal error:", str(e))
finally:
    green_led.off()
    red_led.off()
    if 'sock' in locals():
        sock.close()
    print("Shutdown complete")
    sys.exit()