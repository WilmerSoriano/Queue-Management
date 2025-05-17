import time
from threading import Lock


class DeviceManager:
    def __init__(self):
        self.devices = {}
        self.lock = Lock()
        
        # Initialize all 30 devices with status 'off'
        for device_id in range(1, 31):
            self.devices[device_id] = {
                'status': 'off',
                'priority': 'Relaxing',
                'last_seen': time.time(),
                'address' : None,
                'last_color': None
            }
    # New device? assign a Status, priority, and time
    def update_device(self, device_id, status):
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id]['status'] = status.lower()
                self.devices[device_id]['priority'] = 'Need Help' if status.lower() == 'red' else 'Check Off'
                self.devices[device_id]['last_seen'] = time.time()
    # Resets or make this default button display
    def set_offline(self, device_id):
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id]['status'] = 'off'
                self.devices[device_id]['priority'] = 'Relaxing'