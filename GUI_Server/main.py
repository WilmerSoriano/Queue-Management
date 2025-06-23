"""
    Queue Management System with Animated Background
    Features:
    - 30-device grid with status colors
    - GIF background
    - UDP server for device communication
"""

import socket
import tkinter as tk
from threading import Thread

from device_manager import DeviceManager
from PIL import Image, ImageTk  # ImageSequence For GIF handling
from server import udp_server

# Global counter for activation order
activation_counter = 0
def get_next_order():
    # Generate sequential activation order for queue prioritization
    global activation_counter
    activation_counter += 1
    return activation_counter

class GUI:
    def __init__(self, master, device_manager):
        # Initialize main application window
        self.master = master
        self.device_manager = device_manager
        master.title("Queue Management Helper")
        
        # Animation configuration
        self.resize_delay = 100  # Debounce time for resizing (ms)
        self.animation_paused = False
        self.resize_after_id = None  # Resize event tracker
        
        # GIF background setup
        self.bg_frames = []
        #self.frame_index = 0
        self.load_background_frames("bg.jpg")  # Load and process GIF
        self.current_bg_image = None  # Track current background image

        # Initialize UI components
        self.create_widgets()
        self.update_display()
        self.update_background()
        self.animate_background()

    def load_background_frames(self, path):
        # Load the image background
        try:
            img = Image.open(path)
            self.original_size = img.size
            self.bg_frames = [img.convert('RGB')]
            self.frame_durations = [100]
                
        except Exception as e:
            print(f"Error loading Image: {e}")
            # Fallback to blank image if GIF load fails
            self.bg_frames = [Image.new('RGBA', (100, 100), (0,0,0,0))]
            self.frame_durations = [100]

    def create_widgets(self):
        """Create and arrange UI components"""
        # Main canvas setup
        self.canvas = tk.Canvas(self.master, bg='black', highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Background image container
        self.bg_container = self.canvas.create_image(0, 0, anchor="nw", tags="bg")
        
        # Centered frame for device grid
        self.frame = tk.Frame(self.canvas)
        #Keep the grid in the center
        self.frame_id = self.canvas.create_window(self.canvas.winfo_width()//2, self.canvas.winfo_height()//3, window=self.frame, anchor="center")

        # Create device grid (6 columns x 5 rows)
        self.boxes = []
        for i in range(30):
            # Compact font, the border size etc...
            box = tk.Label(self.frame, text=str(i+1), width=12, height=4, borderwidth=5, relief="solid", font=('Times New Roman', 12))
            box.grid(row=i//6, column=i%6, padx=10, pady=8)
            # Allowes user to left click the box to change color
            box.bind("<Button-1>", lambda e, bid=i+1: self.press_box(bid))
            self.boxes.append(box)

        # Window resize handler
        self.canvas.bind("<Configure>", self.on_resize)

    # =============================== Window Resize Handlers ======================================
    def on_resize(self, event):
        # Debounce resize events to improve performance
        self.animation_paused = True
        if self.resize_after_id:
            self.master.after_cancel(self.resize_after_id)
        self.resize_after_id = self.master.after(self.resize_delay, self.finish_resize)

    def finish_resize(self):
        # Execute after resize debounce delay 
        self.update_background()
        self.center_frame()
        self.animation_paused = False

    def center_frame(self):
        # Maintain grid centering after resize
        self.canvas.coords(self.frame_id, self.canvas.winfo_width()//2, self.canvas.winfo_height()//2)

    # =================== Background Animation System =========================
    def update_background(self):
        # Resize background frames to current window size
        try:
            # Get current dimensions with fallback values
            width = self.canvas.winfo_width() or self.original_size[0]
            height = self.canvas.winfo_height() or self.original_size[1]
            
            # Calculate new size maintaining aspect ratio
            new_size = (
                max(int(width), 1),  # Prevent zero-size
                max(int(height), 1)
            )
            
            # Resize all frames using fast resampling
            self.resized_frames = []
            for frame in self.bg_frames:
                resized = frame.resize(new_size, Image.Resampling.NEAREST)
                self.resized_frames.append(ImageTk.PhotoImage(resized))
        except Exception as e:
            print(f"Resize error: {e}")

    def animate_background(self):
        # Simplified for static image with resize handling
        if not self.animation_paused and hasattr(self, 'resized_frames'):
            try:
                if self.resized_frames:
                    self.current_bg_image = self.resized_frames[0]
                    self.canvas.itemconfig(self.bg_container, image=self.current_bg_image)
                
                # Maintain refresh cycle for resize updates
                self.master.after(100, self.animate_background)
            except Exception as e:
                print(f"Background error: {e}")
                self.master.after(100, self.animate_background)
        else:
            self.master.after(100, self.animate_background)

    # ========================= Queue Management System ================================
    def press_box(self, device_id):
        # Handle device state changes on click
        with self.device_manager.lock:
            device = self.device_manager.devices[device_id]
            current_status = device['status']
            
            # State transition logic
            if current_status == 'off':
                new_status = 'green'
                priority = 'Check Off'
                if device.get('order') is None:
                    device['order'] = get_next_order()
            elif current_status == 'green':
                new_status = 'red'
                priority = 'Need Help'
            else:
                new_status = 'off'
                priority = 'Relaxing'
                device['order'] = None
                
            # Update device state
            device['status'] = new_status
            device['priority'] = priority

        self.update_display()

        if new_status == 'off':
            with self.device_manager.lock:
                device = self.device_manager.devices[device_id]
                addr = device.get('address')  # Should be (IP, 12000)
                last_color = device.get('last_color')
            
            if addr and last_color:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                        sock.sendto(f"LED_OFF:{last_color}".encode(), addr)
                        print(f"Sent LED_OFF to {addr}")
                except Exception as e:
                    print(f"Error sending LED_OFF: {e}")

    def update_display(self):
        # Refresh UI elements without jittering/blinking too much 
        with self.device_manager.lock:
            # Create a snapshot of current device states
            status_snapshot = [
                (d['status'], d['priority'], d.get('order')) 
                for d in self.device_manager.devices.values()
            ]
            active = []
            inactive = []
            
            # Build active/inactive lists
            for idx, (status, _, order) in enumerate(status_snapshot):
                device_id = idx + 1
                if status != 'off':
                    active.append((order or float('inf'), device_id))
                else:
                    inactive.append(device_id)
            
            # Sort active devices
            active.sort(key=lambda x: x[0])
            ordered_ids = [device_id for _, device_id in active] + inactive

        # Update positions only for changed devices
        current_positions = {
            device_id: (self.boxes[device_id-1].grid_info()['row'], self.boxes[device_id-1].grid_info()['column'])
            for device_id in ordered_ids
        }

        # Update UI elements
        for new_idx, device_id in enumerate(ordered_ids):
            target_row = new_idx // 6
            target_col = new_idx % 6
            
            # Only move boxes that need repositioning
            if current_positions.get(device_id, (-1, -1)) != (target_row, target_col):
                self.boxes[device_id-1].grid(row=target_row, column=target_col)
            
            # Update colors and text regardless of position
            status, priority, _ = status_snapshot[device_id-1]
            color = 'white' if status == 'off' else status
            self.boxes[device_id-1].config(bg=color, text=f"ID: {device_id}\n{priority}")

        # Schedule next update (changed from 15000 to 1000ms for better responsiveness)
        self.master.after(1000, self.update_display)

    def queue_status(self):
        # Generate priority-ordered device list, FIFO / directory, so dynamic FIFO without the First Out part
        active = []
        inactive = []
        
        for Id in range(1, 31):
            device = self.device_manager.devices[Id]
            if device['status'] != 'off':
                # Add activation order if missing
                if device.get('order') is None:
                    device['order'] = get_next_order()
                active.append((device['order'], Id))
            else:
                device['order'] = None
                inactive.append(Id)
        
        # Sort by activation order
        active.sort(key=lambda tup: tup[0])
        return [Id for _, Id in active] + inactive

if __name__ == "__main__":
    # Initialize device states
    dm = DeviceManager()
    for dev_id in range(1, 31):
        dm.devices[dev_id]['order'] = None

    # Start UDP server in background thread
    server_thread = Thread(target=udp_server, args=(dm,), daemon=True)
    server_thread.start()
    
    # Create and run GUI
    root = tk.Tk()
    root.minsize(1000, 800)  # Minimum window size
    root.geometry("1024x768")  # Default startup size
    gui = GUI(root, dm)
    root.mainloop()