import re
from socket import *
from threading import Thread

from device_manager import DeviceManager

SERVER_PORT = 12000

def udp_server(device_manager: DeviceManager):
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(("", SERVER_PORT))
    
    try:
        while True:
            message, addr = sock.recvfrom(2048)
            decoded = message.decode().strip()
            
            # Use to extract device ID and status
            match = re.match(r'ID:(\d+),status:(red|green|off)', decoded, re.IGNORECASE)
            if match:
                try:
                    device_id = int(match.group(1))
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
                        elif status == 'off':
                            device_manager.set_offline(device_id)
                            
                except (ValueError, IndexError) as e:
                    print(f"Error processing message: {e}")
                    
    finally:
        sock.close()