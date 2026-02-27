import os
import re # To read incoming message from client
from socket import *

import pygame
from device_manager import DeviceManager

SERVER_PORT = 12000

# Initialize pygame mixer once, to replay music as many times as needed
pygame.mixer.init()

# Finds the path to sound and plays it.
def play_notification():
    sound_path = os.path.join(os.getcwd(), "sound.wav")
    if os.path.exists(sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()
    else:
        print("Sound file not found.")

def udp_server(device_manager: DeviceManager):
    sock = socket(AF_INET, SOCK_DGRAM)          # AF_INET is for IPv4 , and SOCK_DGRAM is for UDP protocol is used
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # Makes sure to tell other device only 'server' can reuse this address
    sock.bind(("0.0.0.0", SERVER_PORT))
    
    try:
        while True:
            message, addr = sock.recvfrom(2048) # ISSUE/FIX: What if 2 user send a message at same time? RECVFROM will read 1 packet at a time. NOTE: This can also based on OS Queue socket buffer, no sokcet collision!
            decoded = message.decode().strip()
            print(f"Received from {addr}: {decoded}")

            # Use to extract device ID and status
            match = re.match(r'ID:(\d+),status:(red|green|off)', decoded, re.IGNORECASE)
            if match:
                try:
                    device_id = int(match.group(1)) # Grabs ID and Status color only
                    status = match.group(2).lower()
                    
                    if 1 <= device_id <= 30:
                        with device_manager.lock:
                            device = device_manager.devices[device_id]
                            device['address'] = addr  # Store client address
                            if status in ['red', 'green']:
                                device['last_color'] = status  # Track last active color
                            elif status == 'off':
                                device['last_color'] = None

                        if status in ['red', 'green']:
                            device_manager.update_device(device_id, status)
                            play_notification()
                        elif status == 'off':
                            device_manager.set_offline(device_id)
                            
                except (ValueError, IndexError) as e:
                    print(f"Error processing message: {e}")
                    
    finally:
        sock.close()