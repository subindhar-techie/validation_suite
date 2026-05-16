import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image as PILImage, ImageTk
import os
import sys
import time
from datetime import datetime
from ..theme import Theme
import math

def create_sharp_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = []
    # Top-Left
    cx, cy = x1+r, y1+r
    for i in range(180, 270, 5):
        points.extend([cx + r * math.cos(math.radians(i)), cy + r * math.sin(math.radians(i))])
    # Top-Right
    cx, cy = x2-r, y1+r
    for i in range(270, 360, 5):
        points.extend([cx + r * math.cos(math.radians(i)), cy + r * math.sin(math.radians(i))])
    # Bottom-Right
    cx, cy = x2-r, y2-r
    for i in range(0, 90, 5):
        points.extend([cx + r * math.cos(math.radians(i)), cy + r * math.sin(math.radians(i))])
    # Bottom-Left
    cx, cy = x1+r, y2-r
    for i in range(90, 180, 5):
        points.extend([cx + r * math.cos(math.radians(i)), cy + r * math.sin(math.radians(i))])
    return canvas.create_polygon(points, smooth=False, **kwargs)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, width, height, r, bg_color, fg_color, hover_bg, hover_fg, font, command, outline_color="", **kwargs):
        super().__init__(parent, width=width, height=height, bg='white', highlightthickness=0, **kwargs)
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg
        self.command = command
        
        self.rect_id = create_sharp_rounded_rect(self, 1, 1, width-1, height-1, r, fill=bg_color, outline=outline_color)
        
        self.icon_poly = None
        self.icon_line = None
        self.text_id = self.create_text(width//2, height//2, text=text, font=font, fill=fg_color)
            
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonRelease-1>", self.on_release)
        
    def on_enter(self, e):
        self.itemconfig(self.rect_id, fill=self.hover_bg)
        self.itemconfig(self.text_id, fill=self.hover_fg)
        if self.icon_poly:
            self.itemconfig(self.icon_poly, outline=self.hover_fg)
            self.itemconfig(self.icon_line, fill=self.hover_fg)
        self.config(cursor="hand2")
        
    def on_leave(self, e):
        self.itemconfig(self.rect_id, fill=self.bg_color)
        self.itemconfig(self.text_id, fill=self.fg_color)
        if self.icon_poly:
            self.itemconfig(self.icon_poly, outline=self.fg_color)
            self.itemconfig(self.icon_line, fill=self.fg_color)
            
    def on_release(self, e):
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            if self.command:
                self.command()

# Import resource_path function
try:
    from runtime_hook import resource_path
except ImportError:
    # Fallback for development
    def resource_path(relative_path):
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_path = getattr(sys, '_MEIPASS', current_dir)
        return os.path.join(base_path, relative_path)

# Setup module paths for both development and EXE
modules_path = resource_path('modules')

# Debug info
print(f"Machine Log - Running as {'EXE' if getattr(sys, 'frozen', False) else 'script'}")
print(f"Machine Log - Initial modules path: {modules_path}")

# If modules not found at expected path, try development structure
if not os.path.exists(modules_path):
    dev_modules_path = resource_path('src/modules')
    if os.path.exists(dev_modules_path):
        modules_path = dev_modules_path
        print(f"Machine Log - Using development modules path: {modules_path}")
    else:
        print(f"Machine Log - Modules directory not found: {modules_path}")

print(f"Final modules path: {modules_path}")

# Debug: List all files in modules directory
print("Machine Log - Contents of modules directory:")
if os.path.exists(modules_path):
    for root, dirs, files in os.walk(modules_path):
        level = root.replace(modules_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{subindent}{file}')
else:
    print(f"Machine Log - Modules directory does not exist: {modules_path}")

# Add modules path to ensure imports work
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)
    print(f"Machine Log - Added to sys.path: {modules_path}")

print(f"Machine Log Tab - sys.path: {sys.path}")
print(f"Machine Log Tab - Current dir: {os.getcwd()}")

try:
    from machine_log_validation.core.script_validator import ScriptValidator  # type: ignore
    print("SUCCESS: Imported ScriptValidator")
    
    # Fix for Pylance warning
    ScriptValidator = ScriptValidator  # type: ignore
    
except ImportError as e:
    print(f"Machine Log Import Error: {e}")
    
    # Debug: Check if file exists
    script_validator_path = os.path.join(modules_path, 'machine_log_validation', 'core', 'script_validator.py')
    print(f"Looking for file: {script_validator_path}")
    print(f"File exists: {os.path.exists(script_validator_path)}")
    
    # Show error dialog
    messagebox.showerror(
        "Import Error", 
        f"Cannot import ScriptValidator:\n{str(e)}\n\n"
        f"Looking for: {script_validator_path}\n\n"
        f"Please check the modules directory structure."
    )
    sys.exit(1)

class MachineLogTab:
    def __init__(self, parent):
        self.parent = parent
        self.window_icon = None  # Add this line
        self.create_widgets()
    
    def is_file_open(self, filepath):
        """Check if a file is already open"""
        if not filepath:
            return False
        
        # Check if file exists
        if os.path.exists(filepath):
            # Try to open the file in write mode to check if it's locked
            try:
                with open(filepath, 'r+') as f:
                    # Try to read a byte to test access
                    f.read(1)
                return False  # File is accessible, not locked
            except (IOError, PermissionError, OSError):
                # File is likely open/locked by another application
                return True
            except Exception:
                return True
        
        # File doesn't exist yet - check if directory is writable
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.access(dir_path, os.W_OK):
            return True
        
        return False
    
    def create_widgets(self):
        # Global variables for GUI components
        self.root = None
        self.script_entry = None
        self.machine_log_entry = None
        self.log_output = None
        
        self.launch_gui()

    def get_icon_path(self):
        """Get the absolute path to the application icon - IMPROVED VERSION"""
        try:
            # Import resource_path
            from runtime_hook import resource_path
            
            # Try multiple possible locations for both development and EXE
            possible_paths = [
                # For PyInstaller EXE (using resource_path)
                resource_path('assets/icons/RTL_logo.ico'),
                resource_path('RTL_logo.ico'),
                
                # For development (relative paths)
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'icons', 'RTL_logo.ico'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icons', 'RTL_logo.ico'),
                
                # Common project structures
                'assets/icons/RTL_logo.ico',
                '../assets/icons/RTL_logo.ico',
                '../../assets/icons/RTL_logo.ico',
                'src/assets/icons/RTL_logo.ico',
            ]
            
            for icon_path in possible_paths:
                # Convert to absolute path
                icon_path = os.path.abspath(icon_path)
                if os.path.exists(icon_path):
                    print(f"Icon found at: {icon_path}")
                    return icon_path
            
            print("Icon not found in any expected location")
            return None
            
        except Exception as e:
            print(f"Error finding icon path: {e}")
            return None

    def browse_script_file(self):
        filename = filedialog.askopenfilename(
            title="Select Perso Script File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.script_entry.config(state='normal')
            self.script_entry.delete(0, tk.END)
            self.script_entry.insert(0, filename)
            self.script_entry.config(state='readonly')

    def browse_machine_log_file(self):
        filename = filedialog.askopenfilename(
            title="Select Machine Log File", 
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.machine_log_entry.config(state='normal')
            self.machine_log_entry.delete(0, tk.END)
            self.machine_log_entry.insert(0, filename)
            self.machine_log_entry.config(state='readonly')

    def validate_machine_log(self):
        """Main validation function with dynamic validation logic"""
        script_path = self.script_entry.get()
        machine_log_path = self.machine_log_entry.get()
        
        # Validation checks
        if not script_path or not machine_log_path:
            messagebox.showerror("Error", "Please select both Perso Script and Machine Log files.")
            return
        
        try:
            # Clear previous results
            self.log_output.delete(1.0, tk.END)
            self.log_output.insert(tk.END, "First Card Validation Machine\n")
            self.log_output.insert(tk.END, "="*50 + "\n\n")
            
            # Initialize validator
            validator = ScriptValidator()
            
            # Parse files (silent)
            if not validator.parse_script_file(script_path):
                self.log_output.insert(tk.END, "❌ Error: Failed to parse Perso Script file.\n")
                messagebox.showerror("Error", "Failed to parse Perso Script file.")
                return
            
            if not validator.parse_machine_log(machine_log_path):
                self.log_output.insert(tk.END, "❌ Error: Failed to parse Machine Log file.\n")
                messagebox.showerror("Error", "Failed to parse Machine Log file.")
                return
            
            # Run validation (silent)
            report = validator.validate_script_vs_machine_log()
            
            # Get summary only
            total = len(validator.validation_results)
            passed = sum(1 for r in validator.validation_results if r.get('status') == 'PASS')
            failed = total - passed
            
            # Display minimal results
            self.log_output.insert(tk.END, "Validation Results:\n")
            self.log_output.insert(tk.END, "-" * 30 + "\n")
            self.log_output.insert(tk.END, f"Total: {total}\n")
            self.log_output.insert(tk.END, f"Passed: {passed}\n")
            self.log_output.insert(tk.END, f"Failed: {failed}\n")
            self.log_output.insert(tk.END, "-" * 30 + "\n")
            
            # Save report to machine log directory
            machine_log_dir = os.path.dirname(machine_log_path)
            iccid_swapped = validator.field_values.get("ICCID_CARD_SWAPPED")
            
            # Generate date string for filename
            date_str = datetime.now().strftime('%Y%m%d')

            if iccid_swapped:
                report_filename = f"LogValidation_{iccid_swapped}_{date_str}.txt"
            else:
                log_filename = os.path.basename(machine_log_path)
                log_name = os.path.splitext(log_filename)[0]
                report_filename = f"LogValidation_{log_name}_{date_str}.txt"

            report_path = os.path.join(machine_log_dir, report_filename)
            print(f"Report Will Be Saved To: {report_path}")        
            try:
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.log_output.insert(tk.END, f"\n✅ Report saved to: {report_path}\n")
                if failed > 0:
                    messagebox.showwarning("Validation Completed with Errors", 
                        f"First Card Validation completed with {failed} error(s).\n\nReport saved to:\n{report_path}")
                else:
                    messagebox.showinfo("Success", 
                        f"First Card Validation completed successfully!\n\nReport saved to:\n{report_path}")
            except Exception as e:
                self.log_output.insert(tk.END, f"❌ Failed to save report: {str(e)}\n")
                messagebox.showerror("Error", f"Validation completed but failed to save report:\n{str(e)}")
            
        except Exception as e:
            error_msg = f"❌ First Card Validation Error: {str(e)}\n"
            self.log_output.insert(tk.END, error_msg)
            messagebox.showerror("Error", f"First Card Validation failed:\n{str(e)}")

    def clear_all_fields(self):
        """Clear all input fields and log output"""
        self.script_entry.config(state='normal')
        self.machine_log_entry.config(state='normal')
        self.script_entry.delete(0, tk.END)
        self.machine_log_entry.delete(0, tk.END)
        self.script_entry.config(state='readonly')
        self.machine_log_entry.config(state='readonly')
        self.log_output.delete(1.0, tk.END)
        
        # Show minimal instructions
        self.log_output.insert(tk.END, "First Card Validation Machine\n")
        self.log_output.insert(tk.END, "="*50 + "\n\n")
        self.log_output.insert(tk.END, "Instructions:\n")
        self.log_output.insert(tk.END, "1. Select Perso Script File\n")
        self.log_output.insert(tk.END, "2. Select Machine Log File\n")
        self.log_output.insert(tk.END, "3. Click Validate\n")
        self.log_output.insert(tk.END, "="*50 + "\n")
        self.log_output.insert(tk.END, "="*60 + "\n\n")

    def launch_gui(self):
        # Use the parent window passed from main launcher
        self.root = self.parent
        self.window_icon = None
        try:
            icon_path = self.get_icon_path()
            if icon_path and os.path.exists(icon_path):
                img = PILImage.open(icon_path).resize((32, 32), PILImage.LANCZOS)
                self.window_icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.window_icon)
        except Exception:
            pass

        self.root.title("Machine Log Validation Version 1.2")
        self.root.geometry("1100x750")
        self.root.minsize(1100, 750)
        self.root.maxsize(1100, 750)
        self.root.configure(bg="#F4F6F9")
        self.root.resizable(False, False)

        main_frame = tk.Frame(self.root, bg='#F4F6F9')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(15, 5))
        
        # --- Header Banner ---
        header_frame = tk.Frame(main_frame, bg='#1D4ED8', height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        lbl_title = tk.Label(header_frame, text="💻 Machine Log Validation", font=('Segoe UI', 18, 'bold'), bg='#1D4ED8', fg='white')
        lbl_title.pack(anchor=tk.W, padx=20, pady=(15, 0))
        lbl_sub = tk.Label(header_frame, text="Validate machine logs against perso script", font=('Segoe UI', 10), bg='#1D4ED8', fg='#DBEAFE')
        lbl_sub.pack(anchor=tk.W, padx=55, pady=(0, 0))
        
        # --- Content Area ---
        content_frame = tk.Frame(main_frame, bg='#F4F6F9')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel (width 360) drawn via Canvas for rounded cards
        left_panel = tk.Canvas(content_frame, bg='#F4F6F9', highlightthickness=0, width=360)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 20))
        
        def draw_rounded_card(y_offset, height):
            create_sharp_rounded_rect(left_panel, 2, y_offset, 356, y_offset+height, r=10, fill='white', outline='#E2E8F0')

        # 1. File Selection Card
        draw_rounded_card(0, 190)
        file_content = tk.Frame(left_panel, bg='white')
        left_panel.create_window(10, 10, window=file_content, anchor='nw', width=340)
        
        tk.Label(file_content, text="📁 File Selection", font=('Segoe UI', 11, 'bold'), bg='white', fg='#1E293B').pack(anchor=tk.W, padx=10, pady=(5, 15))
        
        # Perso Script Box
        box1 = tk.Frame(file_content, bg='white')
        box1.pack(fill=tk.X, padx=10, pady=(0, 15))
        icon1 = tk.Label(box1, text="📄", font=('Segoe UI', 18), bg='#EFF6FF', fg='#3B82F6', width=3, height=1)
        icon1.pack(side=tk.LEFT, padx=(0, 15))
        
        txt1_frame = tk.Frame(box1, bg='white')
        txt1_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(txt1_frame, text="Perso Script File", font=('Segoe UI', 9, 'bold'), bg='white', fg='#1E293B').pack(anchor=tk.W)
        self.script_entry = tk.Entry(txt1_frame, font=('Segoe UI', 9), bg='white', fg='#64748B', relief=tk.FLAT, readonlybackground="white", state='readonly')
        self.script_entry.pack(fill=tk.X, pady=(2,0))
        
        btn1 = RoundedButton(box1, text="Browse", width=85, height=30, r=8, bg_color='white', fg_color='#2563EB', hover_bg='#EFF6FF', hover_fg='#1D4ED8', font=('Segoe UI', 9, 'bold'), command=self.browse_script_file, outline_color="#CBD5E1")
        btn1.pack(side=tk.RIGHT, padx=5)
        
        # Machine Log Box
        box2 = tk.Frame(file_content, bg='white')
        box2.pack(fill=tk.X, padx=10, pady=(0, 15))
        icon2 = tk.Label(box2, text="📄", font=('Segoe UI', 18), bg='#ECFDF5', fg='#10B981', width=3, height=1)
        icon2.pack(side=tk.LEFT, padx=(0, 15))
        
        txt2_frame = tk.Frame(box2, bg='white')
        txt2_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(txt2_frame, text="Machine Log File", font=('Segoe UI', 9, 'bold'), bg='white', fg='#1E293B').pack(anchor=tk.W)
        self.machine_log_entry = tk.Entry(txt2_frame, font=('Segoe UI', 9), bg='white', fg='#64748B', relief=tk.FLAT, readonlybackground="white", state='readonly')
        self.machine_log_entry.pack(fill=tk.X, pady=(2,0))
        
        btn2 = RoundedButton(box2, text="Browse", width=85, height=30, r=8, bg_color='white', fg_color='#2563EB', hover_bg='#EFF6FF', hover_fg='#1D4ED8', font=('Segoe UI', 9, 'bold'), command=self.browse_machine_log_file, outline_color="#CBD5E1")
        btn2.pack(side=tk.RIGHT, padx=5)
        
        # 2. Validation Info Card
        draw_rounded_card(210, 120)
        info_content = tk.Frame(left_panel, bg='white')
        left_panel.create_window(10, 220, window=info_content, anchor='nw', width=340)
        tk.Label(info_content, text="ℹ️ Validation Information", font=('Segoe UI', 11, 'bold'), bg='white', fg='#1E293B').pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        info_box = tk.Frame(info_content, bg='#F8FAFC', highlightbackground="#E2E8F0", highlightthickness=1)
        info_box.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Label(info_box, text="Validation is performed internally.\nResults will be displayed after completion.", font=('Segoe UI', 9), bg='#F8FAFC', fg='#475569', justify=tk.LEFT, wraplength=300).pack(anchor=tk.W, padx=10, pady=10)
        
        # 3. Actions Card
        draw_rounded_card(350, 150)
        action_content = tk.Frame(left_panel, bg='white')
        left_panel.create_window(10, 360, window=action_content, anchor='nw', width=340)
        tk.Label(action_content, text="⚡ Actions", font=('Segoe UI', 11, 'bold'), bg='white', fg='#1E293B').pack(anchor=tk.W, padx=10, pady=(5, 15))
        
        self.validate_button = RoundedButton(action_content, text="▶ Validate First Card Log", width=320, height=36, r=8, bg_color='#2563EB', fg_color='white', hover_bg='#1D4ED8', hover_fg='white', font=('Segoe UI', 10, 'bold'), command=self.validate_machine_log)
        self.validate_button.pack(pady=(0, 10))
        
        clear_btn = RoundedButton(action_content, text="🗑 Clear All Fields", width=320, height=36, r=8, bg_color='#EF4444', fg_color='white', hover_bg='#DC2626', hover_fg='white', font=('Segoe UI', 10, 'bold'), command=self.clear_all_fields)
        clear_btn.pack(pady=(0, 10))

        # --- RIGHT PANEL ---
        right_panel = tk.Frame(content_frame, bg='#F4F6F9')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        right_canvas = tk.Canvas(right_panel, bg='#F4F6F9', highlightthickness=0)
        right_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        def on_right_resize(event):
            w, h = event.width, event.height
            right_canvas.delete("bg_rect")
            create_sharp_rounded_rect(right_canvas, 2, 2, w-2, h-2, r=10, fill='white', outline='#E2E8F0', tags="bg_rect")
            right_canvas.tag_lower("bg_rect")
            right_canvas.coords(content_win, 10, 10)
            right_canvas.itemconfig(content_win, width=w-20, height=h-20)
            
        right_canvas.bind("<Configure>", on_right_resize)
        
        results_content = tk.Frame(right_canvas, bg='white')
        content_win = right_canvas.create_window(10, 10, window=results_content, anchor='nw')
        
        results_header = tk.Frame(results_content, bg='white')
        results_header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(results_header, text="📊 Validation Results", font=('Segoe UI', 11, 'bold'), bg='white', fg='#1E293B').pack(side=tk.LEFT)
        
        # Terminal area
        term_frame = tk.Frame(results_content, bg='#111827', highlightbackground="#0F172A", highlightthickness=1)
        term_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        term_header = tk.Frame(term_frame, bg='#111827')
        term_header.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(term_header, text="Validation Log", font=('Segoe UI', 9), bg='#111827', fg='#94A3B8').pack(side=tk.LEFT)
        tk.Label(term_header, text="● Ready", font=('Segoe UI', 9, 'bold'), bg='#111827', fg='#10B981').pack(side=tk.RIGHT)
        
        self.log_output = scrolledtext.ScrolledText(
            term_frame, font=("Consolas", 10), bg='#111827', fg='#F8FAFC',
            insertbackground='white', selectbackground='#3B82F6', relief=tk.FLAT, padx=10, pady=10
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)
        
        self.log_output.tag_configure("success", foreground="#10B981")
        self.log_output.tag_configure("error", foreground="#EF4444")
        self.log_output.tag_configure("warning", foreground="#F59E0B")
        self.log_output.tag_configure("info", foreground="#3B82F6")

        # System Status Bar
        status_bar = tk.Frame(self.root, bg='#F4F6F9', height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(status_bar, text="🛡 System Status: Ready", font=('Segoe UI', 9, 'bold'), bg='#F4F6F9', fg='#10B981').pack(side=tk.LEFT)
        tk.Label(status_bar, text="All systems operational", font=('Segoe UI', 9), bg='#F4F6F9', fg='#64748B').pack(side=tk.LEFT, padx=10)
        tk.Label(status_bar, text=f"⏱ {datetime.now().strftime('%I:%M:%S %p')}  |  Version 1.2", font=('Segoe UI', 9), bg='#F4F6F9', fg='#94A3B8').pack(side=tk.RIGHT)
        
        self.clear_all_fields()