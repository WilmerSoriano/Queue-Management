"""
    Queue Management System with Animated Background
    Features:
    - 30-device grid with status colors
    - Image background
    - UDP server for device communication
    - Canvas-based boxes with proper font sizing
"""

import socket
import tkinter as tk
from threading import Thread

from device_manager import DeviceManager
from PIL import Image, ImageTk
from server import udp_server

# Global counter for activation order
activation_counter = 0
def get_next_order():
    # Generate sequential activation order for queue prioritization (First in, TA Chose => FITC? not FIFO priority)
    global activation_counter
    activation_counter += 1
    return activation_counter

class GUI:
    def __init__(self, master, device_manager):
        # Initialize main application window
        self.master = master
        self.device_manager = device_manager
        master.title("Queue Management Helper")
        
        # Animation configuration, this prevents jiggles when new Device incoming (Makes it look smooth)
        self.resize_delay = 100
        self.animation_paused = False
        self.resize_after_id = None
        
        # Box size parameters (Change as needed)
        self.box_width = 150  # Initial width in pixels
        self.box_height = 100  # Initial height in pixels
        self.font_size = 60  # Initial font size
        
        # Background setup
        self.bg_frames = []
        self.load_background_frames("bg.jpg")
        self.current_bg_image = None

        # Initialize UI components
        self.create_widgets()
        self.update_display()
        self.update_background()
        self.animate_background()
        self.update_box_positions()  # Initialize box positions

    def load_background_frames(self, path):
        try:
            img = Image.open(path)
            self.original_size = img.size
            self.bg_frames = [img.convert('RGB')]
            self.frame_durations = [100]
        except Exception as e:
            print(f"Error loading Image: {e}")
            self.bg_frames = [Image.new('RGBA', (100, 100), (0,0,0,0))]
            self.frame_durations = [100]

    def create_widgets(self):
        """Create and arrange UI components"""
        # Main canvas
        self.canvas = tk.Canvas(self.master, bg='black', highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Background container
        self.bg_container = self.canvas.create_image(0, 0, anchor="nw", tags="bg")
        
        # Create device grid (6 columns x 5 rows) as canvas rectangles
        self.boxes = []
        self.box_texts = []
        self.box_ids = []
        
        # Create boxes with ALL box ID and repective layout (Change as needed)
        for i in range(30):
            # We'll position them later
            box_id = self.canvas.create_rectangle(
                0, 0, self.box_width, self.box_height,
                width=3, outline="black", fill="white",
                tags=f"box_{i+1}"
            ) # FONT here
            text_id = self.canvas.create_text(
                self.box_width/2, self.box_height/2,
                text=str(i+1), font=('Arial', self.font_size, "bold"),
                fill="black", tags=f"text_{i+1}"
            )
            self.box_ids.append(box_id)
            self.box_texts.append(text_id)
            
            # Bind click event to the box
            self.canvas.tag_bind(box_id, "<Button-1>", lambda e, bid=i+1: self.press_box(bid))
            self.canvas.tag_bind(text_id, "<Button-1>", lambda e, bid=i+1: self.press_box(bid))

        # Window resize handler
        self.canvas.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.animation_paused = True
        if self.resize_after_id:
            self.master.after_cancel(self.resize_after_id)
        self.resize_after_id = self.master.after(self.resize_delay, self.finish_resize)
    # Updates everything completely with new device incoming
    def finish_resize(self):
        self.update_background()
        self.update_box_positions()
        self.animation_paused = False

    def update_box_positions(self):
        #Calculate and update box positions based on window size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
         
         # Do nothing is not changes appear
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        # Calculate dynamic box size based on window dimensions
        self.box_width = max(100, min(200, canvas_width // 8))
        self.box_height = max(60, min(150, canvas_height // 8))
        
        # Calculate font size as a fraction of box height
        self.font_size = max(14, min(36, int(self.box_height * 0.4)))
        
        # Calculate grid layout 
        cols = 6
        rows = 5
        padding = 15
        
        # Calculate total grid width and height
        grid_width = (self.box_width + padding) * cols
        grid_height = (self.box_height + padding) * rows
        
        # Calculate starting position to center the grid
        start_x = (canvas_width - grid_width) / 2
        start_y = (canvas_height - grid_height) / 3  # Slightly higher than center
        
        # Position all boxes
        for i in range(30):
            row = i // cols
            col = i % cols
            
            x1 = start_x + col * (self.box_width + padding)
            y1 = start_y + row * (self.box_height + padding)
            x2 = x1 + self.box_width
            y2 = y1 + self.box_height
            
            # Update box position and size
            self.canvas.coords(self.box_ids[i], x1, y1, x2, y2)
            
            # Update text position and size
            text_x = (x1 + x2) / 2
            text_y = (y1 + y2) / 2
            self.canvas.coords(self.box_texts[i], text_x, text_y)
            # FIX: Update font size for each text item (from feedback)
            self.canvas.itemconfig(self.box_texts[i], font=('Arial', self.font_size, "bold"))

    def update_background(self):
        # Resize background to current window size
        try:
            width = self.canvas.winfo_width() or self.original_size[0]
            height = self.canvas.winfo_height() or self.original_size[1]
            
            new_size = (max(int(width), 1), max(int(height), 1))
            
            self.resized_frames = []
            for frame in self.bg_frames:
                resized = frame.resize(new_size, Image.Resampling.NEAREST)
                self.resized_frames.append(ImageTk.PhotoImage(resized))
        except Exception as e:
            print(f"Resize error: {e}")

    # NOTE: this handles the sudden change while mainting background
    def animate_background(self):
        if not self.animation_paused and hasattr(self, 'resized_frames'):
            try:
                if self.resized_frames:
                    self.current_bg_image = self.resized_frames[0]
                    self.canvas.itemconfig(self.bg_container, image=self.current_bg_image)
                self.master.after(100, self.animate_background)
            except Exception as e:
                print(f"Background error: {e}")
                self.master.after(100, self.animate_background)
        else:
            self.master.after(100, self.animate_background)

    # If TA touches on screen value
    def press_box(self, device_id):
        with self.device_manager.lock:
            device = self.device_manager.devices[device_id]
            current_status = device['status']
            
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
                
            device['status'] = new_status
            device['priority'] = priority

        self.update_display()

        if new_status == 'off':
            with self.device_manager.lock:
                device = self.device_manager.devices[device_id]
                addr = device.get('address')
                last_color = device.get('last_color')

            # If TA press button from screen, tell client to turn of LED
            if addr and last_color:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                        sock.sendto(f"LED_OFF:{last_color}".encode(), addr)
                        print(f"Sent LED_OFF to {addr}")
                except Exception as e:
                    print(f"Error sending LED_OFF: {e}")

    def update_display(self):
        # Get the properly ordered queue (Was using the wrong queue order)
        ordered_ids = self.queue_status()
        
        # Get device statuses for coloring
        with self.device_manager.lock:
            status_snapshot = [(d['status'], d['priority']) for d in self.device_manager.devices.values()]

        # Update box colors and positions
        for new_idx, device_id in enumerate(ordered_ids):
            status, priority = status_snapshot[device_id-1]

            # FIX: Update color (based on feedback) 
            """
                NOTE! everything else is still using Red and Green
                Change the color here only to display on Screen.
            """
            if status == 'red':
                fill_color = 'Salmon'
            elif status == 'green':
                fill_color = 'light green'
            else:
                fill_color = 'white'
                
            self.canvas.itemconfig(self.box_ids[device_id-1], fill=fill_color)
            
            # FIX: Issue where Font did not display correct size 
            self.canvas.itemconfig(self.box_texts[device_id-1], text=str(device_id))
            
            # Update position if needed
            row = new_idx // 6
            col = new_idx % 6
            
            padding = 15
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calculate total grid width and height
            grid_width = (self.box_width + padding) * 6
            grid_height = (self.box_height + padding) * 5
            
            # Calculate starting position to center the grid
            start_x = (canvas_width - grid_width) / 2
            start_y = (canvas_height - grid_height) / 3
            
            # Calculate new position
            x1 = start_x + col * (self.box_width + padding)
            y1 = start_y + row * (self.box_height + padding)
            x2 = x1 + self.box_width
            y2 = y1 + self.box_height
            
            # Move the box
            self.canvas.coords(self.box_ids[device_id-1], x1, y1, x2, y2)
            
            # Move the text
            text_x = (x1 + x2) / 2
            text_y = (y1 + y2) / 2
            self.canvas.coords(self.box_texts[device_id-1], text_x, text_y)

        self.master.after(1000, self.update_display)

# ======================= MAIN QUEUE ACTION FI-TAC (First in, TA Chooses)====================================
    def queue_status(self):
        active = []
        inactive = []
        
        for Id in range(1, 31):
            device = self.device_manager.devices[Id]
            if device['status'] != 'off':
                if device.get('order') is None:
                    device['order'] = get_next_order()
                active.append((device['order'], Id))
            else:
                device['order'] = None
                inactive.append(Id)
        
        active.sort(key=lambda tup: tup[0])
        return [Id for _, Id in active] + inactive
# =========================================================================================================
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
    root.geometry("1400x900")  # Default startup size
    gui = GUI(root, dm)
    root.mainloop()