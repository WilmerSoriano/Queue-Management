import ujson
import uos

#creates a json file to hold Wifi info
CONFIG_FILE = "config.json"

def save_config(ssid, password, server_ip, device_id):
    config = {
        "ssid": ssid,
        "password": password,
        "server_ip": server_ip,
        "device_id": device_id
    }
    with open(CONFIG_FILE, "w") as f:
        ujson.dump(config, f)
    print("Configuration saved")
# load current Wifi-config even if Pico is turn off
def load_config():
    try:
        if CONFIG_FILE in uos.listdir():
            with open(CONFIG_FILE, "r") as f:
                return ujson.load(f)
    except Exception as e:
        print("Config load error:", e)
    return None
# If user presses both button, Reset and delete the json file
def reset_config():
    try:
        uos.remove(CONFIG_FILE)
        print("Configuration reset")
    except:
        print("No config to reset")