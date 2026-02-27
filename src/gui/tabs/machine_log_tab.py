import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image as PILImage, ImageTk
import os
import sys
import time
from datetime import datetime
from ..theme import Theme

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
            self.script_entry.delete(0, tk.END)
            self.script_entry.insert(0, filename)

    def browse_machine_log_file(self):
        filename = filedialog.askopenfilename(
            title="Select Machine Log File", 
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.machine_log_entry.delete(0, tk.END)
            self.machine_log_entry.insert(0, filename)

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

            if iccid_swapped:
                report_filename = f"{iccid_swapped}_1st_card_machine_log_Validation.txt"
            else:
                log_filename = os.path.basename(machine_log_path)
                log_name = os.path.splitext(log_filename)[0]
                report_filename = f"{log_name}_1st_card_machine_log_Validation.txt"

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
        self.script_entry.delete(0, tk.END)
        self.machine_log_entry.delete(0, tk.END)
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
        
        # Initialize icon reference to prevent garbage collection
        self.window_icon = None
        
        # Set icon - FIXED: Store reference in instance variable
        try:
            icon_path = self.get_icon_path()
            if icon_path and os.path.exists(icon_path):
                print(f"Loading icon from: {icon_path}")
                img = PILImage.open(icon_path).resize((32, 32), PILImage.LANCZOS)
                # CRITICAL: Store the icon reference in instance variable
                self.window_icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.window_icon)
                print("Icon loaded successfully")
            else:
                print(f"Icon not found at: {icon_path}")
                # Create a simple default icon
                try:
                    from PIL import ImageDraw
                    default_img = PILImage.new('RGB', (32, 32), color='#2c3e50')
                    draw = ImageDraw.Draw(default_img)
                    draw.rectangle([8, 8, 24, 24], fill='#3498db')
                    self.window_icon = ImageTk.PhotoImage(default_img)
                    self.root.iconphoto(True, self.window_icon)
                    print("Using default icon")
                except Exception as de:
                    print(f"Could not create default icon: {de}")
        except Exception as e:
            print(f"Icon loading failed: {e}. Using default icon.")
            # Don't crash the application if icon fails

        self.root.title("1st Card Machine Log Validation")
        
        # DO NOT reset geometry - it's already centered from main_window
        # But ensure the size is correct
        self.root.geometry("1100x750")
        
        # PREVENT MAXIMIZING - Set min and max size to current size
        self.root.minsize(1100, 750)  # Minimum size = current size
        self.root.maxsize(1100, 750)  # Maximum size = current size
        self.root.configure(bg="#f5f6fa")
        
        # Make window NOT resizable (this should work now)
        self.root.resizable(False, False)

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure modern styles with smaller fonts
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), background='#2c3e50', foreground='white')
        style.configure('Header.TLabel', font=('Arial', 9, 'bold'), background='#ffffff', foreground='#2c3e50')
        style.configure('TButton', font=('Arial', 9))
        style.configure('Accent.TButton', background='#3498db', foreground='white')
        style.configure('TEntry', font=('Arial', 9))
        style.configure('TCombobox', font=('Arial', 9))
        style.configure('TLabelframe', background='#ffffff', bordercolor='#bdc3c7')
        style.configure('TLabelframe.Label', background='#ffffff', foreground='#2c3e50', font=('Arial', 10, 'bold'))

        # Main container with reduced padding
        main_frame = tk.Frame(self.root, bg='#f5f6fa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header with reduced height
        header_frame = tk.Frame(main_frame, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(fill=tk.BOTH, padx=20, pady=12)
        
        title_label = tk.Label(
            header_content,
            text="📊 1st Card Machine Log validation",
            font=('Arial', 16, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        title_label.pack(side=tk.LEFT)

        # Content area
        content_frame = tk.Frame(main_frame, bg=Theme.BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Configuration with reduced width
        left_panel = tk.Frame(content_frame, bg=Theme.BG_WHITE, relief=tk.FLAT, bd=0, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)

        # Right panel - Results
        right_panel = tk.Frame(content_frame, bg=Theme.BG_WHITE, relief=tk.FLAT, bd=0)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # === LEFT PANEL - CONFIGURATION ===
        left_content = tk.Frame(left_panel, bg=Theme.BG_WHITE, padx=20, pady=20)
        left_content.pack(fill=tk.BOTH, expand=True)

        # File Selection Frame
        file_frame = ttk.LabelFrame(left_content, text="File Selection", padding=15)
        file_frame.pack(fill=tk.X, pady=(0, 15))

        # Perso Script File Selection
        ttk.Label(file_frame, text="Perso Script File:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 6))
        
        script_frame = tk.Frame(file_frame, bg='#ffffff')
        script_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.script_entry = ttk.Entry(script_frame)
        self.script_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        script_btn = ttk.Button(script_frame, text="Browse", command=self.browse_script_file, width=8)
        script_btn.pack(side=tk.RIGHT)

        # Machine Log File Selection
        ttk.Label(file_frame, text="Machine Log File:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 6))
        
        machine_frame = tk.Frame(file_frame, bg='#ffffff')
        machine_frame.pack(fill=tk.X)
        
        self.machine_log_entry = ttk.Entry(machine_frame)
        self.machine_log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        machine_btn = ttk.Button(machine_frame, text="Browse", command=self.browse_machine_log_file, width=8)
        machine_btn.pack(side=tk.RIGHT)

        # Validation Info Frame
        info_frame = ttk.LabelFrame(left_content, text="ℹ️ Validation Info", padding=12)
        info_frame.pack(fill=tk.X, pady=(0, 12))
        
        info_text = "Validation is performed internally.\nResults will be displayed after completion."
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=('Arial', 9),
            bg='#ffffff',
            fg='#2c3e50',
            justify=tk.LEFT,
            anchor="w",
            wraplength=280
        )
        info_label.pack(fill=tk.BOTH, expand=True)

        # Actions Frame
        action_frame = ttk.LabelFrame(left_content, text="🚀 Actions", padding=12)
        action_frame.pack(fill=tk.X)

        # Store button reference for threading
        self.validate_button = tk.Button(
            action_frame,
            text="▶️ Validate First Card Log",
            command=self.validate_machine_log,
            font=('Arial', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.validate_button.pack(fill=tk.X, pady=(0, 8))

        # Clear Button
        clear_btn = tk.Button(
            action_frame,
            text="🗑️ Clear All Fields",
            command=self.clear_all_fields,
            font=('Arial', 9),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        clear_btn.pack(fill=tk.X)

        # === RIGHT PANEL - RESULTS ===
        right_content = tk.Frame(right_panel, bg='#ffffff')
        right_content.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Results header
        results_header = tk.Frame(right_content, bg='#34495e', height=40)
        results_header.pack(fill=tk.X)
        results_header.pack_propagate(False)

        results_title = tk.Label(
            results_header,
            text="📋 Validation Results",
            font=('Arial', 11, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        results_title.pack(side=tk.LEFT, padx=15, pady=10)

        # Log Output Frame
        log_frame = ttk.LabelFrame(right_content, text="Validation Log", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.log_output = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white',
            selectbackground='#3498db',
            relief=tk.FLAT,
            padx=12,
            pady=12
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)

        # Configure text colors for better readability
        self.log_output.tag_configure("success", foreground="#27ae60")
        self.log_output.tag_configure("error", foreground="#e74c3c")
        self.log_output.tag_configure("warning", foreground="#f39c12")
        self.log_output.tag_configure("info", foreground="#3498db")

        # Add initial instructions
        self.clear_all_fields()