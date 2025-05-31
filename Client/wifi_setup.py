import socket
import time

import machine
import network
import ubinascii
from config_manager import save_config

# NOTE use http://192.168.4.1  when connected to Pico Wifi

def start_setup_portal():
    # Creating a Device Wifi access point
    ap = network.WLAN(network.AP_IF)
    ap_name = f"PicoW-Device20"
    
    # You may change as needed, but set only the essential parameters
    ap.config(essid=ap_name, security=0)  # Only set SSID, and password
     # NOTE: security=0 means no password for Device Wifi
     
    ap.active(True)
    
    # Wait for AP to start
    print("Starting AP...")
    time.sleep(5)  # Longer wait for stability
    print(f"AP running: {ap_name}")
    print(f"AP IP: {ap.ifconfig()[0]}")
    
    # Simple HTML form, user will entering local web using http://192.168.4.1 
    html = """<html><body>
    <h1>Pico W Setup</h1>
    <form action="/config" method="post">
        WiFi SSID: <input type="text" name="ssid"><br>
        Password: <input type="password" name="password"><br>
        Server IP: <input type="text" name="server_ip"><br>
        Device ID: <input type="number" name="device_id"><br>
        <input type="submit" value="Save">
    </form>
    </body></html>"""
    
    # Start web server
    s = socket.socket()
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    print("Web server running on port 80")
    
    while True:
        try:
            conn, addr = s.accept()
            request = conn.recv(1024)
            print("Request received")
            
            if b"POST /config" in request:
                # Extract form data
                data = request.split(b'\r\n\r\n')[1].decode()
                params = {}
                for pair in data.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        params[key] = value
                
                print("Config received:", params)
                
                # Save configuration
                save_config(
                    params.get('ssid', ''),
                    params.get('password', ''),
                    params.get('server_ip', ''),
                    int(params.get('device_id', '0')))
                
                # Send response
                conn.send(b"HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n")
                conn.send(b"<h1>Configuration saved!</h1>")
                conn.send(b"<p>Device will reboot in 5 seconds...your safe to close this tab</p>")
                conn.close()
                
                # Reboot device
                time.sleep(5)
                machine.reset()
                
            else:
                # Serve HTML form
                conn.send(b"HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n")
                conn.send(html)
                conn.close()
                
        except Exception as e:
            print("Web server error:", e)
            time.sleep(1)