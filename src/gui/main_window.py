import tkinter as tk
import os
import sys

from tkinter import ttk , messagebox

try:
    from runtime_hook import resource_path
except ImportError:
    # Fallback for development
    def resource_path(relative_path):
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(current_dir)
        base_path = getattr(sys, '_MEIPASS', project_root)
        return os.path.join(base_path, relative_path)

from .theme import Theme
import math

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(int(c) for c in rgb)

def interpolate_color(c1, c2, f):
    rgb1 = hex_to_rgb(c1)
    rgb2 = hex_to_rgb(c2)
    rgb = [rgb1[i] + (rgb2[i] - rgb1[i]) * f for i in range(3)]
    return rgb_to_hex(rgb)

def create_gradient_rounded_rect(canvas, x, y, w, h, r, c1, c2):
    lines = []
    for i in range(w):
        f = i / float(w)
        color = interpolate_color(c1, c2, f)
        dy = 0
        if i < r:
            dx = r - i
            dy = r - math.sqrt(r*r - dx*dx)
        elif i >= w - r:
            dx = i - (w - r) + 1
            if dx > r: dx = r
            dy = r - math.sqrt(r*r - dx*dx)
        line_id = canvas.create_line(x+i, y+dy, x+i, y+h-dy, fill=color)
        lines.append(line_id)
    return lines

def create_rounded_rect(canvas, x1, y1, x2, y2, r=20, **kwargs):
    points = []
    # Top-Left
    cx, cy = x1+r, y1+r
    for i in range(180, 270, 5):
        rad = math.radians(i)
        points.extend([cx + r * math.cos(rad), cy + r * math.sin(rad)])
    # Top-Right
    cx, cy = x2-r, y1+r
    for i in range(270, 360, 5):
        rad = math.radians(i)
        points.extend([cx + r * math.cos(rad), cy + r * math.sin(rad)])
    # Bottom-Right
    cx, cy = x2-r, y2-r
    for i in range(0, 90, 5):
        rad = math.radians(i)
        points.extend([cx + r * math.cos(rad), cy + r * math.sin(rad)])
    # Bottom-Left
    cx, cy = x1+r, y2-r
    for i in range(90, 180, 5):
        rad = math.radians(i)
        points.extend([cx + r * math.cos(rad), cy + r * math.sin(rad)])
        
    return canvas.create_polygon(points, smooth=False, **kwargs)

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Validation Tool")
        self.root.resizable(False, False)
        self.root.configure(bg=Theme.BG_MAIN)
        
        # Set icon FIRST before any geometry changes to ensure it's visible from start
        try:
            icon_path = self.get_icon_path()
            if os.path.exists(icon_path):
                self.root.iconbitmap(default=icon_path)
        except Exception as e:
            print(f"Icon error: {e}")
        
        # Calculate screen dimensions and set geometry with center position in ONE call
        # This prevents the window from appearing in wrong position first
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 500
        window_height = 650
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.create_launcher_interface()
    
    def center_window(self):
        """
        Center the window on the screen
        """
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")
    
    def get_icon_path(self):
        """Get the absolute path to the application icon"""
        try:
            from runtime_hook import resource_path
            # Use resource_path for both dev and exe
            icon_path = resource_path(r"assets/icons/RTL_logo.ico")
            if os.path.exists(icon_path):
                return icon_path
            # Fallback: try different variations
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            possible_paths = [
                os.path.join(current_dir, 'assets', 'icons', 'RTL_logo.ico'),
                os.path.join(current_dir, '..', 'assets', 'icons', 'RTL_logo.ico'),
            ]
            for path in possible_paths:
                path = os.path.normpath(path)
                if os.path.exists(path):
                    return path
            return None
        except Exception as e:
            print(f"Error finding icon: {e}")
            return None
    
    def create_launcher_interface(self):
        # Background Canvas for Modern Design
        self.bg_canvas = tk.Canvas(self.root, width=500, height=650, bg=Theme.BG_MAIN, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0)
        
        # Modern Decorative Background Shapes
        self.bg_canvas.create_oval(-100, -50, 150, 200, fill="#E6EEFA", outline="")
        self.bg_canvas.create_oval(350, 80, 600, 330, fill="#EEF0FD", outline="")
        self.bg_canvas.create_oval(-50, 400, 100, 550, fill="#EEF0FD", outline="")
        
        # Header (Drawn directly on canvas for transparency)
        header_y = 60
        self.bg_canvas.create_text(250, header_y, text="Validation Toolkit", font=Theme.title_font(24), fill=Theme.PRIMARY)
        self.bg_canvas.create_line(220, header_y + 25, 280, header_y + 25, fill=Theme.ACCENT, width=3, capstyle=tk.ROUND)
        self.bg_canvas.create_text(250, header_y + 55, text="Select a tool to launch", font=Theme.text_font(11), fill=Theme.TEXT_LIGHT)
        
        self.cards_data = []
        
        # Create tool cards directly positioned
        self.create_tool_card("First Card Validation", "Validate text file and image", self.launch_first_card_tab, y=160)
        self.create_tool_card("Machine Log Validation", "Validate machine logs against script", self.launch_machine_log_tab, y=275)
        self.create_tool_card("Input/Output Validation", "Validate Input/Output files in bulk", self.launch_mno_file_tab, y=390)
        
        def on_canvas_motion(e):
            x, y = e.x, e.y
            cursor_set = False
            for card in self.cards_data:
                btn_w = card['btn_w']
                btn_h = card['btn_h']
                btn_x1 = card['btn_x']
                btn_y1 = card['btn_y']
                is_on_btn = (btn_x1 <= x <= btn_x1+btn_w) and (btn_y1 <= y <= btn_y1+btn_h)
                is_on_card = (card['x'] <= x <= card['x']+card['w']) and (card['y'] <= y <= card['y']+card['h'])
                
                if is_on_card:
                    cursor_set = True
                    if not card['hovered']:
                        card['hovered'] = True
                        self.bg_canvas.itemconfig(card['id'], outline="#9B72F9", width=1.5)
                    
                    if is_on_btn:
                        if not card.get('btn_hovered', False):
                            card['btn_hovered'] = True
                            for i, line_id in enumerate(card['btn_lines']):
                                color = interpolate_color("#7A58E5", "#487AFF", i / float(btn_w))
                                self.bg_canvas.itemconfig(line_id, fill=color)
                    else:
                        if card.get('btn_hovered', True):
                            card['btn_hovered'] = False
                            for i, line_id in enumerate(card['btn_lines']):
                                color = interpolate_color("#9B72F9", "#6284FF", i / float(btn_w))
                                self.bg_canvas.itemconfig(line_id, fill=color)
                else:
                    if card['hovered']:
                        card['hovered'] = False
                        self.bg_canvas.itemconfig(card['id'], outline="#e6e8f0", width=1)
                        if card.get('btn_hovered', True):
                            card['btn_hovered'] = False
                            for i, line_id in enumerate(card['btn_lines']):
                                color = interpolate_color("#9B72F9", "#6284FF", i / float(btn_w))
                                self.bg_canvas.itemconfig(line_id, fill=color)
            
            self.bg_canvas.config(cursor="hand2" if cursor_set else "")
                        
        def on_canvas_click(e):
            x, y = e.x, e.y
            for card in self.cards_data:
                if card['x'] <= x <= card['x']+card['w'] and card['y'] <= y <= card['y']+card['h']:
                    card['command']()
                    
        self.bg_canvas.bind("<Motion>", on_canvas_motion)
        self.bg_canvas.bind("<Button-1>", on_canvas_click)
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg=Theme.SECONDARY, height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=Theme.text_font(9),
            bg=Theme.SECONDARY,
            fg=Theme.TEXT_WHITE
        )
        self.status_label.pack(side='left', padx=10, pady=5)
        
        version_label = tk.Label(
             self.status_frame,
             text="v1.0.0",
             font=Theme.text_font(9),
             bg=Theme.SECONDARY,
             fg=Theme.BORDER
        )
        version_label.pack(side='right', padx=10, pady=5)
    
    def create_tool_card(self, title, description, command, y):
        """Modern transparent card component drawn directly on canvas"""
        
        x = 40
        w = 420
        h = 100
        
        # Determine icon and tag based on title
        if "First" in title:
            icon_char = "📄"
            tag_text = "📄 Text & Image"
        elif "Machine" in title:
            icon_char = "⚙️"
            tag_text = "⚙️ Script Match"
        else:
            icon_char = "📁"
            tag_text = "📁 Bulk Input"

        # 1. White Card Background
        card_id = create_rounded_rect(self.bg_canvas, x, y, x+w, y+h, r=20, fill="#ffffff", outline="#e6e8f0", width=1)
        
        # 2. Left Icon Block
        icon_bg = create_rounded_rect(self.bg_canvas, x+15, y+15, x+85, y+85, r=15, fill="#edf3ff", outline="")
        icon_txt = self.bg_canvas.create_text(x+50, y+50, text=icon_char, font=("Segoe UI Emoji", 24), fill=Theme.ACCENT)
        
        # 3. Texts
        title_id = self.bg_canvas.create_text(x + 105, y + 30, text=title, font=Theme.header_font(12), fill=Theme.TEXT_MAIN, anchor="w")
        desc_id = self.bg_canvas.create_text(x + 105, y + 55, text=description, font=Theme.text_font(9), fill=Theme.TEXT_LIGHT, anchor="w")
        
        # 4. Tag Pill
        tag_bg = create_rounded_rect(self.bg_canvas, x+105, y+70, x+105+90, y+90, r=10, fill="#edf3ff", outline="")
        tag_txt = self.bg_canvas.create_text(x+150, y+80, text=tag_text, font=Theme.text_font(8), fill="#005ff8")
        
        # 5. Launch Button (Gradient Style)
        btn_w = 80
        btn_h = 34
        btn_x1 = x + w - btn_w - 15
        btn_y1 = y + (h - btn_h) // 2
        
        # Purple to blue gradient
        btn_lines = create_gradient_rounded_rect(self.bg_canvas, btn_x1, btn_y1, btn_w, btn_h, r=8, c1="#9B72F9", c2="#6284FF")
        btn_txt = self.bg_canvas.create_text(btn_x1 + btn_w//2, btn_y1 + btn_h//2, text="▶ Launch", font=Theme.bold_font(10), fill="#ffffff")
        
        card_data = {
            'id': card_id,
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'command': command,
            'hovered': False,
            'btn_x': btn_x1,
            'btn_y': btn_y1,
            'btn_w': btn_w,
            'btn_h': btn_h,
            'btn_lines': btn_lines,
            'btn_hovered': False
        }
        
        self.cards_data.append(card_data)
    
    def launch_first_card_tab(self):
        """Launch First Card Validation in new window"""
        self.update_status("Launching First Card Validation...")
        try:
            from .tabs.first_card_tab import FirstCardTab
            self.root.withdraw()
            
            # Create window but keep it withdrawn until fully configured
            new_window = tk.Toplevel(self.root)
            new_window.withdraw()  # Keep hidden until fully ready
            new_window.title("First Card Validation")
            new_window.resizable(False, False)
            new_window.configure(bg=Theme.BG_MAIN) # Apply theme background
            
            # Set icon FIRST before geometry to ensure it's visible from start
            try:
                icon_path = self.get_icon_path()
                if os.path.exists(icon_path):
                    new_window.iconbitmap(icon_path)
            except Exception as e:
                print(f"Icon error: {e}")
            
            # Calculate center position and set geometry with position in ONE call
            new_window.update_idletasks()
            screen_width = new_window.winfo_screenwidth()
            screen_height = new_window.winfo_screenheight()
            window_width = 820
            window_height = 750
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            def on_close():
                new_window.destroy()
                self.root.deiconify()
                self.update_status("Ready")

            new_window.protocol("WM_DELETE_WINDOW", on_close)
            FirstCardTab(new_window)
            
            # Show window only after all setup is complete
            new_window.deiconify()
            new_window.focus_force()
            
            self.update_status("Running First Card Validation")

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Launch Error", str(e))

    def launch_machine_log_tab(self):
        """Launch Machine Log Validation in new window"""
        self.update_status("Launching Machine Log Validation...")
        try:
            from .tabs.machine_log_tab import MachineLogTab
            self.root.withdraw()
            
            # Create window but keep it withdrawn until fully configured
            new_window = tk.Toplevel(self.root)
            new_window.withdraw()  # Keep hidden until fully ready
            new_window.title("Machine Log Validation")
            new_window.resizable(False, False)
            new_window.configure(bg=Theme.BG_MAIN)
            
            # Set icon FIRST before geometry to ensure it's visible from start
            try:
                icon_path = self.get_icon_path()
                if os.path.exists(icon_path):
                    new_window.iconbitmap(icon_path)
            except Exception as e:
                print(f"Icon error: {e}")
            
            # Calculate center position and set geometry with position in ONE call
            new_window.update_idletasks()
            screen_width = new_window.winfo_screenwidth()
            screen_height = new_window.winfo_screenheight()
            window_width = 1100
            window_height = 750
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            def on_close():
                new_window.destroy()
                self.root.deiconify()
                self.update_status("Ready")

            new_window.protocol("WM_DELETE_WINDOW", on_close)
            MachineLogTab(new_window)
            
            # Show window only after all setup is complete
            new_window.deiconify()
            new_window.focus_force()
            
            self.update_status("Running Machine Log Validation")

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Launch Error", str(e))

    def launch_mno_file_tab(self):
        """Launch MNO File Validation in new window"""
        self.update_status("Launching MNO File Validation...")
        try:
            from .tabs.mno_file_tab import MNOFileTab
            self.root.withdraw()
            
            # Create window but keep it withdrawn until fully configured
            new_window = tk.Toplevel(self.root)
            new_window.withdraw()  # Keep hidden until fully ready
            new_window.title("Input/Output Files Validation Version 1.2")
            new_window.resizable(False, False)
            new_window.configure(bg=Theme.BG_MAIN)
            
            # Set icon FIRST before geometry to ensure it's visible from start
            try:
                icon_path = self.get_icon_path()
                if os.path.exists(icon_path):
                    new_window.iconbitmap(icon_path)
            except Exception as e:
                print(f"Icon error: {e}")
            
            # Calculate center position and set geometry with position in ONE call
            new_window.update_idletasks()
            screen_width = new_window.winfo_screenwidth()
            screen_height = new_window.winfo_screenheight()
            window_width = 900
            window_height = 750
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            new_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            def on_close():
                new_window.destroy()
                self.root.deiconify()
                self.update_status("Ready")

            new_window.protocol("WM_DELETE_WINDOW", on_close)
            MNOFileTab(new_window)
            
            # Show window only after all setup is complete
            new_window.deiconify()
            new_window.focus_force()
            
            self.update_status("Running MNO File Validation")

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Launch Error", str(e))
    
    def center_child_window(self, window):
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        window.geometry(f"+{x}+{y}")
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()