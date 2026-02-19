import tkinter as tk
import os
import sys
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import logging
from pathlib import Path

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
print(f"Running as {'EXE' if getattr(sys, 'frozen', False) else 'script'}")
print(f"Initial modules path: {modules_path}")

# If modules not found at expected path, try development structure
if not os.path.exists(modules_path):
    dev_modules_path = resource_path('src/modules')
    if os.path.exists(dev_modules_path):
        modules_path = dev_modules_path
        print(f"Using development modules path: {modules_path}")
    else:
        print(f"Modules directory not found: {modules_path}")

print(f"Final modules path: {modules_path}")

# Debug: List all files in modules directory
print("Contents of modules directory:")
if os.path.exists(modules_path):
    for root, dirs, files in os.walk(modules_path):
        level = root.replace(modules_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{subindent}{file}')
else:
    print(f"Modules directory does not exist: {modules_path}")

# Add modules path to ensure imports work
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)
    print(f"Added to sys.path: {modules_path}")

print(f"Current sys.path: {sys.path}")

# ========== ADDED IMPORT SECTION ==========
try:
    # Debug: Check if file exists
    file_comparator_path = os.path.join(modules_path, 'mno_file_validator', 'core', 'file_comparator.py')
    print(f"Looking for file: {file_comparator_path}")
    print(f"File exists: {os.path.exists(file_comparator_path)}")
    
    # Check what's actually in the mno_file_validator path
    mno_path = os.path.join(modules_path, 'mno_file_validator')
    print(f"mno_file_validator path exists: {os.path.exists(mno_path)}")
    if os.path.exists(mno_path):
        print("Contents of mno_file_validator:")
        for item in os.listdir(mno_path):
            print(f"  {item}")
    
    # Use absolute import with the modules path we just added
    from mno_file_validator.core.file_comparator import MNOFileComparator  # type: ignore
    print("SUCCESS: Imported MNOFileComparator using absolute import")
    
except ImportError as e:
    print(f"Import failed: {e}")
    
    # Show detailed error information
    import traceback
    error_details = traceback.format_exc()
    
    # Check if the file exists
    file_exists = os.path.exists(file_comparator_path)
    
    messagebox.showerror(
        "Import Error", 
        f"Cannot import MNOFileComparator:\n{str(e)}\n\n"
        f"File exists: {file_exists}\n"
        f"Looking for: {file_comparator_path}\n\n"
        f"Please check:\n"
        f"1. The modules directory structure is correct\n"
        f"2. file_comparator.py contains MNOFileComparator class\n"
        f"3. All core modules have proper imports\n\n"
        f"Full error:\n{error_details}"
    )
    sys.exit(1)

# Fix for Pylance warning
MNOFileComparator = MNOFileComparator  # type: ignore
# ========== END OF ADDED SECTION ==========

# REST OF YOUR ORIGINAL mno_file_tab.py CODE CONTINUES HERE...
# Make sure there are no references to project_root in the remaining code

class MNOFileTab:
    def __init__(self, parent):
        self.parent = parent
        self.icons = []
        self.icon = None
        
        # Setup logging
        self.setup_logging()
        
        # Initialize comparator - USING ACTUAL CLASS NOW
        self.comparator = MNOFileComparator()  # type: ignore
        
        # Initialize variables
        self.parent_folder = tk.StringVar()
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.is_loading = False
        
        # Batch counters
        self.total_batches = tk.IntVar(value=0)
        self.passed_batches = tk.IntVar(value=0)
        self.failed_batches = tk.IntVar(value=0)
        
        self.create_widgets()
    
    # ... rest of your MNOFileTab class methods remain the same ...
    
    def get_icon_path(self):
        """Get the absolute path to the application icon using resource_path"""
        try:
            # Use resource_path to find icon in both development and EXE
            possible_paths = [
                r"D:\Jio_Validation_Suite\assets\icons\RTL_logo.ico",
            ]
            
            print("Searching for icon in following paths:")
            for icon_relative_path in possible_paths:
                icon_path = resource_path(icon_relative_path)
                exists = os.path.exists(icon_path)
                print(f"  {icon_path} -> {'EXISTS' if exists else 'NOT FOUND'}")
                if exists:
                    print(f"FOUND ICON: {icon_path}")
                    return icon_path
            
            print("Icon not found in any location")
            return None
            
        except Exception as e:
            print(f"Error finding icon: {e}")
            return None

    def set_application_icon(self):
        """Set application icon"""
        icon_path = self.get_icon_path()
        
        if not icon_path or not os.path.exists(icon_path):
            print("No icon file found, using default system icon")
            return
        
        try:
            # Method 1: Direct .ico file (Windows)
            self.parent.iconbitmap(icon_path)
            print("Icon set using iconbitmap")
            
        except Exception as e:
            print(f"Failed to set application icon: {e}")
            # Try alternative methods if needed
            try:
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                icon = ImageTk.PhotoImage(img)
                self.parent.iconphoto(True, icon)
                self.icon = icon  # Keep reference
                print("Icon set using PIL fallback")
            except Exception as pil_error:
                print(f"PIL icon also failed: {pil_error}")

    def center_window(self):
        """Center the window on screen"""
        self.parent.update_idletasks()
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        x = (self.parent.winfo_screenwidth() // 2) - (width // 2)
        y = (self.parent.winfo_screenheight() // 2) - (height // 2)
        self.parent.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Remove existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(stream=sys.stderr)
            ]
        )
    
    def create_widgets(self):
        """Create professional GUI"""
        # Set application icon
        self.set_application_icon()
        
        # Main container
        main_frame = tk.Frame(self.parent, bg='#f5f6fa', padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#2c3e50', height=70)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(fill=tk.BOTH, padx=25, pady=15)
        
        title_label = tk.Label(
            header_content,
            text="MNO FILE VALIDATION SYSTEM",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        title_label.pack(side=tk.LEFT)
        
        version_label = tk.Label(
            header_content,
            text="",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='#bdc3c7'
        )
        version_label.pack(side=tk.RIGHT)
        
        # Main content
        content_frame = tk.Frame(main_frame, bg='#f5f6fa')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls
        left_panel = tk.Frame(content_frame, bg='#ffffff', relief=tk.RAISED, bd=1, width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        # Right panel - Results
        right_panel = tk.Frame(content_frame, bg='#ffffff', relief=tk.RAISED, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # === LEFT PANEL CONTROLS ===
        left_content = tk.Frame(left_panel, bg='#ffffff', padx=20, pady=20)
        left_content.pack(fill=tk.BOTH, expand=True)
        
        # Folder selection
        folder_frame = ttk.LabelFrame(left_content, text="Project Configuration", padding=15)
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        # INPUT Folder
        input_label = ttk.Label(folder_frame, text="INPUT Folder (contains .txt files):", font=('Arial', 9, 'bold'))
        input_label.pack(anchor=tk.W, pady=(0, 8))
        
        input_entry_frame = tk.Frame(folder_frame, bg='#ffffff')
        input_entry_frame.pack(fill=tk.X, pady=(0, 15))
        
        input_entry = ttk.Entry(input_entry_frame, textvariable=self.input_folder, font=('Arial', 9))
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        input_browse_btn = ttk.Button(input_entry_frame, text="Browse", command=self.browse_input_folder, width=8)
        input_browse_btn.pack(side=tk.RIGHT)
        
        # OUTPUT Folder
        output_label = ttk.Label(folder_frame, text="OUTPUT Folder (contains subfolders & report):", font=('Arial', 9, 'bold'))
        output_label.pack(anchor=tk.W, pady=(0, 8))
        
        output_entry_frame = tk.Frame(folder_frame, bg='#ffffff')
        output_entry_frame.pack(fill=tk.X, pady=(0, 5))
        
        output_entry = ttk.Entry(output_entry_frame, textvariable=self.output_folder, font=('Arial', 9))
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        output_browse_btn = ttk.Button(output_entry_frame, text="Browse", command=self.browse_output_folder, width=8)
        output_browse_btn.pack(side=tk.RIGHT)
        
        # Chip Type
        chip_label = ttk.Label(folder_frame, text="Chip Type:", font=('Arial', 9, 'bold'))
        chip_label.pack(anchor=tk.W, pady=(10, 8))
        
        self.chip_type = ttk.Combobox(
            folder_frame, 
            values=["SAMSUNG 340", "SAMSUNG 480", "TRANSA 380" , "SLM17ECB800B"],
            state="readonly",
            font=('Arial', 9)
        )
        self.chip_type.pack(fill=tk.X, pady=(0, 5))
        self.chip_type.set("SAMSUNG 340")
        
        # Batch Statistics Section
        stats_frame = ttk.LabelFrame(left_content, text="Validation Statistics", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Statistics with consistent spacing
        stats_config = [
            ("Total Batches:", self.total_batches, "#3498db"),
            ("Passed:", self.passed_batches, "#27ae60"), 
            ("Failed:", self.failed_batches, "#e74c3c")
        ]
        
        for label_text, var, color in stats_config:
            stat_frame = tk.Frame(stats_frame, bg='#ffffff')
            stat_frame.pack(fill=tk.X, pady=(0, 8))
            
            label = tk.Label(
                stat_frame,
                text=label_text,
                font=('Arial', 9, 'bold'),
                bg='#ffffff',
                fg='#2c3e50'
            )
            label.pack(side=tk.LEFT)
            
            value_label = tk.Label(
                stat_frame,
                textvariable=var,
                font=('Arial', 10, 'bold'),
                bg='#ffffff',
                fg=color
            )
            value_label.pack(side=tk.RIGHT)
        
        # Actions Section
        action_frame = ttk.LabelFrame(left_content, text="Validation Actions", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 0))
        
        # Primary action buttons
        self.validate_btn = tk.Button(
            action_frame,
            text="Start Validation",
            command=self.start_comparison,
            font=('Arial', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=10,
            cursor='hand2'
        )
        self.validate_btn.pack(fill=tk.X, pady=(0, 8))
        
        # Utility buttons
        utility_frame = tk.Frame(action_frame, bg='#ffffff')
        utility_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.clear_btn = tk.Button(
            utility_frame,
            text="Clear Results",
            command=self.clear_results,
            font=('Arial', 9),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=8,
            cursor='hand2'
        )
        self.clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Status label
        self.status_label = tk.Label(
            action_frame,
            text="● Ready",
            foreground='#27ae60',
            font=('Arial', 9, 'bold'),
            bg='#ffffff'
        )
        self.status_label.pack(anchor=tk.W, pady=(10, 0))
        
        # === LOADING INDICATOR ===
        self.loading_frame = tk.Frame(self.parent, bg='#f5f6fa')
        self.loading_label = tk.Label(
            self.loading_frame,
            text="Processing...",
            font=('Arial', 12, 'bold'),
            bg='#f5f6fa',
            fg='#3498db'
        )
        
        # === RIGHT PANEL RESULTS ===
        right_content = tk.Frame(right_panel, bg='#ffffff')
        right_content.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Results header
        results_header = tk.Frame(right_content, bg='#34495e', height=45)
        results_header.pack(fill=tk.X)
        results_header.pack_propagate(False)
        
        results_title = tk.Label(
            results_header,
            text="VALIDATION RESULTS",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        results_title.pack(side=tk.LEFT, padx=20, pady=12)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            right_content,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white',
            selectbackground='#3498db',
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text colors
        self.results_text.tag_configure("success", foreground="#27ae60")
        self.results_text.tag_configure("error", foreground="#e74c3c")
        self.results_text.tag_configure("warning", foreground="#f39c12")
        self.results_text.tag_configure("info", foreground="#3498db")
        self.results_text.tag_configure("timestamp", foreground="#95a5a6")
        
        # Initialize log
        self.log_message("System initialized and ready", "info")
        
        # Center window
        self.center_window()
    
    def show_loading(self):
        """Show loading indicator"""
        if not self.is_loading:
            self.is_loading = True
            self.loading_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.loading_label.pack(pady=10)
            self.validate_btn.config(state='disabled', bg='#95a5a6')
            self.parent.update()
    
    def hide_loading(self):
        """Hide loading indicator"""
        if self.is_loading:
            self.is_loading = False
            self.loading_frame.place_forget()
            self.validate_btn.config(state='normal', bg='#27ae60')
            self.parent.update()
    
    def update_counters(self, total=0, passed=0, failed=0):
        """Update batch counters"""
        self.total_batches.set(total)
        self.passed_batches.set(passed)
        self.failed_batches.set(failed)
    
    def browse_folder(self):
        """Browse for parent folder (report output location)"""
        folder = filedialog.askdirectory(title="Select Report Output Folder")
        if folder:
            self.parent_folder.set(folder)
            self.log_message(f"Report output folder selected: {folder}", "info")
            self.update_status("Folder selected", "success")
    
    def browse_input_folder(self):
        """Browse for INPUT folder containing .txt files"""
        folder = filedialog.askdirectory(title="Select INPUT Folder (contains .txt files)")
        if folder:
            self.input_folder.set(folder)
            self.log_message(f"INPUT folder selected: {folder}", "info")
            self.update_status("INPUT folder selected", "success")
    
    def browse_output_folder(self):
        """Browse for OUTPUT folder containing subfolders"""
        folder = filedialog.askdirectory(title="Select OUTPUT Folder (contains subfolders)")
        if folder:
            self.output_folder.set(folder)
            self.log_message(f"OUTPUT folder selected: {folder}", "info")
            self.update_status("OUTPUT folder selected", "success")
    
    def update_status(self, message, status_type="info"):
        """Update status indicator"""
        colors = {
            "info": "#3498db",
            "success": "#27ae60", 
            "warning": "#f39c12",
            "error": "#e74c3c"
        }
        color = colors.get(status_type, "#3498db")
        self.status_label.configure(text=f"● {message}", foreground=color)
    
    def log_message(self, message, level="info"):
        """Log message to results area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create a safe version without emojis for logging
        safe_message = message
        emoji_replacements = {
            "🎉": "[SUCCESS]",
            "✅": "[PASS]",
            "❌": "[FAIL]",
            "⚠️": "[WARNING]",
            "🔄": "[PROCESSING]"
        }
        for emoji, text in emoji_replacements.items():
            safe_message = safe_message.replace(emoji, text)
        
        if level == "error":
            formatted = f"[{timestamp}] ERROR: {message}\n"
            tag = "error"
            logging.error(safe_message)
        elif level == "warning":
            formatted = f"[{timestamp}] WARNING: {message}\n"
            tag = "warning"
            logging.warning(safe_message)
        elif level == "success":
            formatted = f"[{timestamp}] SUCCESS: {message}\n"
            tag = "success"
            logging.info(safe_message)
        else:
            formatted = f"[{timestamp}] INFO: {message}\n"
            tag = "info"
            logging.info(safe_message)
        
        self.results_text.insert(tk.END, formatted, tag)
        self.results_text.see(tk.END)
        self.parent.update_idletasks()
    
    def clear_results(self):
        """Clear results and reset counters"""
        self.results_text.delete(1.0, tk.END)
        self.comparator.clear_tracking()
        self.update_counters(0, 0, 0)
        self.log_message("Results cleared", "info")
        self.update_status("Ready", "success")
    
    def start_comparison(self):
        """Start validation process - USING ACTUAL VALIDATION NOW"""
        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()

        if not input_folder:
            messagebox.showerror("Error", "Please select an INPUT folder.")
            return
        
        if not output_folder:
            messagebox.showerror("Error", "Please select an OUTPUT folder.")
            return
        
        if not Path(input_folder).exists():
            messagebox.showerror("Error", "Selected INPUT folder does not exist.")
            return
        
        if not Path(output_folder).exists():
            messagebox.showerror("Error", "Selected OUTPUT folder does not exist.")
            return
        
        try:
            self.show_loading()
            self.update_status("Validation running...", "info")
            
            # Reset UI counters
            self.update_counters(0, 0, 0)
            
            # Logging header
            self.log_message("=" * 50, "info")
            self.log_message("STARTING VALIDATION PROCESS", "info")
            self.log_message("=" * 50, "info")
            self.log_message(f"INPUT Folder: {input_folder}", "info")
            self.log_message(f"OUTPUT Folder: {output_folder}", "info")
            self.log_message(f"Chip Type: {self.chip_type.get()}", "info")
            self.log_message("-" * 50, "info")
            
            # Configure comparator - ACTUAL VALIDATION
            self.comparator.set_log_callback(self.log_message)
            self.comparator.set_chip_type(self.chip_type.get())
            
            # Run validation - ACTUAL VALIDATION (pass both input and output folders)
            success_count, failure_count = self.comparator.run_validation(output_folder, input_folder, output_folder)
            
            # Update counters
            total = success_count + failure_count
            self.update_counters(total, success_count, failure_count)

            # Show results in UI
            self.display_final_summary(success_count, failure_count)

            # Generate Excel report automatically
            if total > 0:
                self.update_status("Generating Excel report...", "info")
                self.generate_excel_report()

        except Exception as e:
            error_msg = f"Validation process error: {str(e)}"
            self.log_message(error_msg, "error")
            self.update_status("Validation failed", "error")
            logging.exception("Validation error")
            messagebox.showerror("Error", f"Validation failed: {str(e)}")
        
        finally:
            self.hide_loading()
    
    def generate_excel_report(self):
        """Generate Excel report automatically - ACTUAL REPORT GENERATION"""
        output_folder = self.output_folder.get()

        if not output_folder:
            messagebox.showwarning("Report", "Please select an OUTPUT folder first.")
            return
        
        try:
            self.log_message("Starting Excel report generation...", "info")

            # Generate report - ACTUAL REPORT GENERATION
            excel_path = self.comparator.generate_excel_reports(output_folder)

            self.log_message(f"Excel report generated: {excel_path}", "success")
            self.update_status("Excel report ready", "success")

        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            self.log_message(error_msg, "error")
            self.update_status("Excel report failed", "error")
            messagebox.showerror("Error", error_msg)
    
    def display_final_summary(self, success_count, failure_count):
        """Display final summary"""
        total = success_count + failure_count
        
        self.log_message("-" * 50, "info")
        self.log_message("VALIDATION SUMMARY", "info")
        self.log_message("-" * 50, "info")
        self.log_message(f"Total batches processed: {total}", "info")
        self.log_message(f"Successful validations: {success_count}", "success")
        self.log_message(f"Failed validations: {failure_count}", "error" if failure_count > 0 else "success")
        
        if failure_count == 0 and total > 0:
            self.log_message("[SUCCESS] All validations completed successfully!", "success")
            self.update_status("Validation passed", "success")
        elif success_count > 0 and failure_count > 0:
            self.log_message(f"[WARNING] Validation completed with {failure_count} failures", "warning")
            self.update_status("Partial success", "warning")
        elif failure_count > 0:
            self.log_message("[FAIL] All validations failed", "error")
            self.update_status("Validation failed", "error")
        else:
            self.update_status("Ready", "success")