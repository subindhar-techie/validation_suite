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
                self.root.iconbitmap(icon_path)
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
        # Main container
        main_container = tk.Frame(self.root, bg=Theme.BG_MAIN)
        main_container.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Header
        header_frame = tk.Frame(main_container, bg=Theme.BG_MAIN)
        header_frame.pack(fill='x', pady=(0, 30))
        
        # Branding / Logo area would go here
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="Validation Toolkit", # Slightly more professional title
            font=Theme.title_font(24),
            bg=Theme.BG_MAIN,
            fg=Theme.PRIMARY
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Select a tool to launch",
            font=Theme.text_font(11),
            bg=Theme.BG_MAIN,
            fg=Theme.TEXT_LIGHT
        )
        subtitle_label.pack()
        
        # Cards container
        cards_frame = tk.Frame(main_container, bg=Theme.BG_MAIN)
        cards_frame.pack(fill='both', expand=True)
        
        # Create tool cards
        self.create_tool_card(cards_frame, "First Card Validation", "Validate text file and image", self.launch_first_card_tab)
        self.create_tool_card(cards_frame, "Machine Log Validation", "Validate machine logs against script", self.launch_machine_log_tab)
        self.create_tool_card(cards_frame, "Input/Output Files Validation", "Validate Input/Output files in bulk", self.launch_mno_file_tab)
        
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
    
    def create_tool_card(self, parent, title, description, command):
        """Modern card component with hover effect"""
        
        card_bg = Theme.BG_WHITE
        
        card = tk.Frame(
            parent,
            bg=card_bg,
            bd=0,
            highlightthickness=1,
            highlightbackground="#e0e0e0" # Very subtle border
        )
        card.pack(fill='x', pady=10, ipady=5)

        # Inner padding frame
        inner = tk.Frame(card, bg=card_bg)
        inner.pack(fill='x', padx=15, pady=15)

        # Left side: Text
        text_frame = tk.Frame(inner, bg=card_bg)
        text_frame.pack(side="left", fill="both", expand=True)

        title_label = tk.Label(
            text_frame,
            text=title,
            font=Theme.header_font(13),
            bg=card_bg,
            fg=Theme.TEXT_MAIN,
            anchor="w"
        )
        title_label.pack(fill="x", anchor="w")
        
        desc_label = tk.Label(
            text_frame,
            text=description,
            font=Theme.text_font(10),
            bg=card_bg,
            fg=Theme.TEXT_LIGHT,
             anchor="w"
        )
        desc_label.pack(fill="x", anchor="w", pady=(2, 0))

        # Right side: Button (styled as icon or arrow)
        btn_frame = tk.Frame(inner, bg=card_bg)
        btn_frame.pack(side="right")

        launch_btn = tk.Button(
            btn_frame,
            text="Launch",
            font=Theme.bold_font(10),
            bg=Theme.ACCENT,
            fg="white",
            activebackground=Theme.PRIMARY,
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=command
        )
        launch_btn.pack()

        # Bind events for hover effect on the entire card
        def on_enter(e):
            card.config(highlightbackground=Theme.ACCENT)
            
        def on_leave(e):
            card.config(highlightbackground="#e0e0e0")

        # Bind to card and inner frames/labels to ensure smooth hover
        for widget in [card, inner, text_frame, title_label, desc_label, btn_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            
            # Make clicking anywhere on the card launch the tool
            widget.bind("<Button-1>", lambda e: command())
    
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