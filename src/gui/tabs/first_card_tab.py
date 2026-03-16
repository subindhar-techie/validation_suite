# first_card_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image as PILImage, ImageTk
import threading
import sys
import os
import tempfile
import glob
import datetime
import re


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
print(f"First Card - Running as {'EXE' if getattr(sys, 'frozen', False) else 'script'}")
print(f"First Card - Initial modules path: {modules_path}")

# If modules not found at expected path, try development structure
if not os.path.exists(modules_path):
    dev_modules_path = resource_path('src/modules')
    if os.path.exists(dev_modules_path):
        modules_path = dev_modules_path
        print(f"First Card - Using development modules path: {modules_path}")

print(f"Final modules path: {modules_path}")

# Add modules path to ensure imports work
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)
    print(f"First Card - Added to sys.path: {modules_path}")

try:
    from first_card_validation.core.validation_engine import ValidationEngine
    print("SUCCESS: Imported ValidationEngine")
except ImportError as e:
    print(f"First Card Import Error: {e}")
    messagebox.showerror(
        "Import Error", 
        f"Cannot import ValidationEngine:\n{str(e)}\n\n"
        f"Please check the modules directory structure."
    )
    sys.exit(1)


    print(f"First Card - Added to sys.path: {modules_path}")

print(f"First Card Tab - sys.path: {sys.path}")
print(f"First Card Tab - Current dir: {os.getcwd()}")

try:
    from first_card_validation.core.validation_engine import ValidationEngine  # type: ignore
    print("SUCCESS: Imported ValidationEngine")
    
    # Fix for Pylance warning
    ValidationEngine = ValidationEngine  # type: ignore
    
except ImportError as e:
    print(f"First Card Import Error: {e}")
    
    # Debug: Check if file exists
    validation_engine_path = os.path.join(modules_path, 'first_card_validation', 'core', 'validation_engine.py')
    print(f"Looking for file: {validation_engine_path}")
    print(f"File exists: {os.path.exists(validation_engine_path)}")
    
    # Show error dialog
    messagebox.showerror(
        "Import Error", 
        f"Cannot import ValidationEngine:\n{str(e)}\n\n"
        f"Looking for: {validation_engine_path}\n\n"
        f"Please check the modules directory structure."
    )
    sys.exit(1)

class FirstCardTab:
    def __init__(self, parent):
        self.parent = parent
        # Initialize operator widgets dictionary here
        self.operator_widgets = {
            'jio': [],
            'airtel': []
        }
        # JIO/AIRTEL frame tracking for two-frame flow
        self.jio_first_frame_shown = False
        self.jio_second_frame_shown = False
        self.airtel_first_frame_shown = False
        self.airtel_second_frame_shown = False
        
        # JIO/AIRTEL frame references
        self.jio_first_frame = None  # First form frame
        self.jio_second_frame = None  # Second form frame (Shared with Airtel "Output files")
        # Track JIO/AIRTEL field widgets for first and second frame
        self.jio_first_frame_widgets = []
        self.jio_second_frame_widgets = []
        self.airtel_first_frame_widgets = []
        self.airtel_second_frame_widgets = []
        self._clearing_in_progress = False
        self._validation_in_progress = False
        print("DEBUG: FirstCardTab initialized")
        self.create_widgets()
    
    def create_widgets(self):
        print("DEBUG: Starting First Card Tab widget creation...")
        
        # Global variables for GUI components
        self.root = None
        self.operator_cb = None
        self.profile_cb = None
        self.ml_entry = None
        self.pcom_entry = None
        self.cnum_entry = None
        self.scm_entry = None
        self.sim_oda_entry = None
        self.perso_script_entry = None
        self.circle_entry = None
        self.image1_entry = None
        self.image2_entry = None
        self.image3_entry = None
        self.image4_entry = None
        self.image5_entry = None
        self.log_output = None
        self.run_button = None
        self.back_button = None

        print("DEBUG: Variables initialized")
        self.launch_gui()
        print("DEBUG: GUI launched successfully")

    def clear_all_fields(self):
        """Clear all input fields and reset selections - FIXED for AIRTEL"""
        # Prevent multiple rapid clicks
        if hasattr(self, '_clearing_in_progress') and self._clearing_in_progress:
            return
        
        self._clearing_in_progress = True
        
        try:
            # Get current operator
            operator = self.operator_cb.get()
            
            # Reset operator selection and re-enable dropdown
            self.operator_cb.set("Select operator")
            self.operator_cb.config(state="readonly")
            
            # Reset profile selection
            self.profile_cb.set("Select profile")
            
            # Clear all JIO entry fields
            self.ml_entry.delete(0, tk.END)
            self.pcom_entry.delete(0, tk.END)
            if hasattr(self, 'perso_script_entry') and self.perso_script_entry:
                self.perso_script_entry.delete(0, tk.END)
            self.cnum_entry.delete(0, tk.END)
            self.scm_entry.delete(0, tk.END)
            self.sim_oda_entry.delete(0, tk.END)
            self.circle_entry.delete(0, tk.END)
            self.image1_entry.delete(0, tk.END)
            self.image2_entry.delete(0, tk.END)
            self.image3_entry.delete(0, tk.END)
            self.image4_entry.delete(0, tk.END)
            self.image5_entry.delete(0, tk.END)
            
            # NEW: Clear AIRTEL-specific entry fields if they exist
            if hasattr(self, 'airtel_ml_entry'):
                self.airtel_ml_entry.delete(0, tk.END)
                print("✅ Cleared Airtel ML entry")
            
            if hasattr(self, 'airtel_pcom_entry'):
                self.airtel_pcom_entry.delete(0, tk.END)
                print("✅ Cleared Airtel PCOM entry")
            
            if hasattr(self, 'airtel_cnum_entry'):
                self.airtel_cnum_entry.delete(0, tk.END)
                print("✅ Cleared Airtel CNUM entry")
            
            if hasattr(self, 'airtel_sim_oda_entry'):
                self.airtel_sim_oda_entry.delete(0, tk.END)
                print("✅ Cleared Airtel SIM ODA entry")
            
            # NEW: Also clear AIRTEL image entries if they exist
            for i in range(1, 3):  # Airtel has INNER LABEL and OUTER LABEL
                attr_name = f'airtel_image{i}_entry'
                if hasattr(self, attr_name):
                    entry_widget = getattr(self, attr_name)
                    entry_widget.delete(0, tk.END)
                    print(f"✅ Cleared Airtel image entry {i}")
            
            # Reset title
            self.jio_first_frame.config(text="")
            
            # Clear log output
            self.log_output.delete(1.0, tk.END)
            self.log_output.insert(tk.END, "All fields cleared. Please select an operator to continue...\n")
            
            # Hide all operator-specific fields
            for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown itself
                widget.grid_remove()
            for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown itself
                widget.grid_remove()
            
            # Also hide JIO second frame widgets
            for widget in self.jio_second_frame_widgets:
                widget.grid_remove()
            
            # Hide JIO second frame if shown
            if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
                self.jio_second_frame.pack_forget()
            
            # Show JIO first frame
            if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
                self.jio_first_frame.pack(padx=20, pady=10, fill="x")
            
            # Reset JIO frame tracking
            self.jio_first_frame_shown = False
            self.jio_second_frame_shown = False
            
            # Hide JIO-specific buttons, show default buttons
            if hasattr(self, 'jio_back_button') and self.jio_back_button:
                self.jio_back_button.pack_forget()
            if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
                self.jio_clear_button.pack_forget()
            if hasattr(self, 'jio_next_button') and self.jio_next_button:
                self.jio_next_button.pack_forget()
            if hasattr(self, 'run_button') and self.run_button:
                self.run_button.pack(side="left", padx=5)
            if hasattr(self, 'clear_all_button') and self.clear_all_button:
                self.clear_all_button.pack(side="left", padx=5)
            
            # Show success message
            messagebox.showinfo("Cleared", "All fields (JIO and AIRTEL) have been cleared successfully!")
            
        except Exception as e:
            print(f"❌ Error during clear operation: {e}")
            messagebox.showerror("Clear Error", f"Error clearing fields: {str(e)}")
            
        finally:
            # Reset flag after a short delay (500ms)
            if hasattr(self, 'root'):
                self.root.after(500, lambda: setattr(self, '_clearing_in_progress', False))

    def browse_ml_file(self, entry_widget):
        filename = filedialog.askopenfilename(
            title="Select Machine Log File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
            print(f"✅ Selected Machine Log: {filename}")

    def browse_pcom_file(self, entry_widget):
        filename = filedialog.askopenfilename(
            title="Select PCOM File",
            filetypes=[
                ("PCOM files", "*.L00;*.L01;*.L07;*.L02;*.L04;*.L78;*.L81;*.L0A"),
                ("All files", "*.*")
            ]
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
            print(f"✅ Selected PCOM file: {filename}")

    def browse_cnum_file(self, entry_widget, file_type="jio"):
        """Browse for CNUM file - different file types for JIO and AIRTEL"""
        if file_type == "airtel":
            filetypes = [("OUT files", "*.out"), ("All files", "*.*")]
            title = "Select Airtel CNUM File (.out)"
        else:  # jio
            filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
            title = "Select JIO CNUM File"
        
        filename = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
            print(f"✅ Selected {file_type} CNUM file: {filename}")

    def browse_scm_file(self, entry_widget):
        filename = filedialog.askopenfilename(
            title="Select SCM File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
            print(f"✅ Selected SCM file: {filename}")

    def browse_sim_oda_file(self, entry_widget):
        filename = filedialog.askopenfilename(
            title="Select SIM ODA File",
            filetypes=[("CPS files", "*.cps"), ("All files", "*.*")]
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
            print(f"✅ Selected SIM ODA file: {filename}")

    def browse_perso_script_file(self, entry_widget):
        """Browse for Perso Script File (.txt)"""
        filename = filedialog.askopenfilename(
            title="Select Perso Script File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
            print(f"✅ Selected Perso Script file: {filename}")

    def browse_image(self, entry):
        path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg"), ("All files", "*.*")]
        )
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)
            print(f"✅ Selected image: {path}")

    def reset_operator_selection(self):
        """Reset operator selection and hide all operator-specific fields"""
        self.operator_cb.set("Select operator")
        self.operator_cb.config(state="readonly")  # Re-enable the dropdown
        
        # Hide JIO second frame if shown
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack_forget()
        
        # Show JIO first frame
        if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
            self.jio_first_frame.pack(padx=20, pady=10, fill="x")
        
        # Hide all operator-specific fields
        for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown itself
            widget.grid_remove()
        for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown itself
            widget.grid_remove()
        
        # Reset JIO frame tracking
        self.jio_first_frame_shown = False
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack_forget()
        if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
            self.jio_first_frame.pack(padx=20, pady=10, fill="x")
        
        # Reset frame tracking
        self.jio_first_frame_shown = False
        self.jio_second_frame_shown = False
        self.airtel_first_frame_shown = False
        self.airtel_second_frame_shown = False
        
        # Show Run and Clear All buttons, hide Next/Back
        if hasattr(self, 'run_button') and self.run_button:
            self.run_button.pack(side="left", padx=5)
        if hasattr(self, 'clear_all_button') and self.clear_all_button:
            self.clear_all_button.pack(side="left", padx=5)
        
        if hasattr(self, 'jio_next_button') and self.jio_next_button:
            self.jio_next_button.pack_forget()
        if hasattr(self, 'jio_back_button') and self.jio_back_button:
            self.jio_back_button.pack_forget()
        if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
            self.jio_clear_button.pack_forget()
        
        # Clear any validation logs
        self.jio_first_frame.config(text="")
        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Please select an operator to continue...\n")

    def jio_clear_current_frame(self):
        """Clear only the current frame inputs for the active operator"""
        if hasattr(self, '_clearing_in_progress') and self._clearing_in_progress:
            return
        
        self._clearing_in_progress = True
        
        try:
            operator = self.operator_cb.get()
            
            if operator == "JIO":
                if self.jio_second_frame_shown:
                    # Clear second frame fields (CNUM, SCM, SIM_ODA)
                    self.cnum_entry.delete(0, tk.END)
                    self.scm_entry.delete(0, tk.END)
                    self.sim_oda_entry.delete(0, tk.END)
                    self.log_output.delete(1.0, tk.END)
                    self.log_output.insert(tk.END, "Second frame fields cleared. First frame inputs are preserved.\n")
                else:
                    # Clear first frame fields (Profile, ML, PCOM, Images)
                    self.profile_cb.set("Select profile")
                    self.ml_entry.delete(0, tk.END)
                    self.pcom_entry.delete(0, tk.END)
                    if hasattr(self, 'perso_script_entry') and self.perso_script_entry:
                        self.perso_script_entry.delete(0, tk.END)
                    self.image1_entry.delete(0, tk.END)
                    self.image2_entry.delete(0, tk.END)
                    self.image3_entry.delete(0, tk.END)
                    self.image4_entry.delete(0, tk.END)
                    self.image5_entry.delete(0, tk.END)
                    self.circle_entry.delete(0, tk.END)
                    self.log_output.delete(1.0, tk.END)
                    self.log_output.insert(tk.END, "First frame fields cleared.\n")
            
            elif operator == "AIRTEL":
                if self.airtel_second_frame_shown:
                    # Clear Airtel second frame (CNUM, SIM ODA)
                    self.airtel_cnum_entry.delete(0, tk.END)
                    self.airtel_sim_oda_entry.delete(0, tk.END)
                    self.log_output.delete(1.0, tk.END)
                    self.log_output.insert(tk.END, "Airtel Step 2 fields cleared. Step 1 inputs preserved.\n")
                else:
                    # Clear Airtel first frame (ML, PCOM, INNER, OUTER)
                    self.airtel_ml_entry.delete(0, tk.END)
                    self.airtel_pcom_entry.delete(0, tk.END)
                    self.airtel_image1_entry.delete(0, tk.END)
                    self.airtel_image2_entry.delete(0, tk.END)
                    self.log_output.delete(1.0, tk.END)
                    self.log_output.insert(tk.END, "Airtel Step 1 fields cleared.\n")
            
            messagebox.showinfo("Cleared", "Current frame inputs cleared successfully!")
            
        except Exception as e:
            print(f"❌ Error during JIO clear operation: {e}")
            messagebox.showerror("Clear Error", f"Error clearing fields: {str(e)}")
            
        finally:
            if hasattr(self, 'root'):
                self.root.after(500, lambda: setattr(self, '_clearing_in_progress', False))

    def jio_show_second_frame(self):
        """Show the second frame for JIO (replaces first frame)"""
        # Validate first frame has required fields
        profile = self.profile_cb.get()
        ml_path = self.ml_entry.get().strip()
        pcom_path = self.pcom_entry.get().strip()
        
        missing_fields = []
        if profile not in ["MOB", "WBIOT", "NBIOT"]:
            missing_fields.append("Profile Type")
        if not ml_path:
            missing_fields.append("Machine Log")
        if not pcom_path:
            missing_fields.append("PCOM")
        
        if missing_fields:
            error_message = "Please select the following required fields before proceeding:\n"
            for field in missing_fields:
                error_message += f"• {field}\n"
            messagebox.showerror("Missing Fields", error_message)
            return
        
        # Hide the first frame
        if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
            self.jio_first_frame.pack_forget()
        
        # Show the second frame
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack(padx=20, pady=10, fill="x")
            # Show all widgets in the second frame
            for widget in self.jio_second_frame_widgets:
                widget.grid()
        
        # Update the window to ensure proper layout
        self.root.update_idletasks()
        
        self.jio_second_frame_shown = True
        
        # Hide Next button
        if hasattr(self, 'jio_next_button') and self.jio_next_button:
            self.jio_next_button.pack_forget()
        
        # Show Run button for JIO second frame
        if hasattr(self, 'run_button') and self.run_button:
            self.run_button.pack(side="left", padx=5)
        
        # Show Clear button (for second frame)
        if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
            self.jio_clear_button.pack(side="left", padx=5)
        
        # Show JIO back button
        if hasattr(self, 'jio_back_button') and self.jio_back_button:
            self.jio_back_button.pack(side="left", padx=5)
            
        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Please select the CNUM, SCM, and SIM ODA files.\n")

    def jio_back_to_first_frame(self):
        """Go back to the first frame for JIO"""
        # Hide the second frame
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack_forget()
        
        # Show the first frame
        if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
            self.jio_first_frame.pack(padx=20, pady=10, fill="x")
            # Show JIO first frame widgets
            for widget in self.jio_first_frame_widgets:
                widget.grid()
            # Hide JIO second frame widgets
            for widget in self.jio_second_frame_widgets:
                widget.grid_remove()
        
        self.jio_second_frame_shown = False
        
        # Show Next button
        if hasattr(self, 'jio_next_button') and self.jio_next_button:
            self.jio_next_button.pack(side="left", padx=5)
        
        # Hide Run button
        if hasattr(self, 'run_button') and self.run_button:
            self.run_button.pack_forget()
            
        # Hide back button (in first step)
        if hasattr(self, 'jio_back_button') and self.jio_back_button:
            self.jio_back_button.pack_forget()
            
        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Back to First Frame. First frame inputs have been preserved.\n")

    def airtel_show_second_frame(self):
        """Show the second frame for AIRTEL (replaces first frame)"""
        # [REFINED] Machine Log and PCOM are mandatory to proceed to Step 2
        ml_path = self.airtel_ml_entry.get().strip()
        pcom_path = self.airtel_pcom_entry.get().strip()
        
        missing_fields = []
        if not ml_path: missing_fields.append("Machine Log")
        if not pcom_path: missing_fields.append("PCOM")
        
        if missing_fields:
            error_message = "Please select the following required fields before proceeding:\n"
            for field in missing_fields:
                error_message += f"• {field}\n"
            messagebox.showerror("Missing Fields", error_message)
            return

        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Airtel: Machine Log and PCOM verified. Proceeding to Step 2.\n")

        # Hide the first frame
        if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
            self.jio_first_frame.pack_forget()
        
        # Show the second frame
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack(padx=20, pady=10, fill="x")
            # Show AIRTEL second frame widgets
            for widget in self.airtel_second_frame_widgets:
                widget.grid()
            # Hide AIRTEL first frame widgets (if they were in second frame container, but they are in form_frame)
            # Actually AIRTEL Step 1 is in form_frame, and Step 2 is in self.jio_second_frame.
        
        self.root.update_idletasks()
        self.airtel_second_frame_shown = True
        
        # Update button visibility
        if hasattr(self, 'jio_next_button') and self.jio_next_button:
            self.jio_next_button.pack_forget()
        if hasattr(self, 'run_button') and self.run_button:
            self.run_button.pack(side="left", padx=5)
        if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
            self.jio_clear_button.pack(side="left", padx=5)
        if hasattr(self, 'jio_back_button') and self.jio_back_button:
            self.jio_back_button.pack(side="left", padx=5)
            
        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Please select the CNUM and SIM ODA files.\n")

    def airtel_back_to_first_frame(self):
        """Go back to the first frame for AIRTEL"""
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack_forget()
        
        if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
            self.jio_first_frame.pack(padx=20, pady=10, fill="x")
            # Show AIRTEL first frame widgets
            for widget in self.airtel_first_frame_widgets:
                widget.grid()
        
        self.airtel_second_frame_shown = False
        
        if hasattr(self, 'jio_next_button') and self.jio_next_button:
            self.jio_next_button.pack(side="left", padx=5)
        if hasattr(self, 'run_button') and self.run_button:
            self.run_button.pack_forget()
        if hasattr(self, 'jio_back_button') and self.jio_back_button:
            self.jio_back_button.pack_forget()
            
        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Back to Airtel Step 1. Inputs preserved.\n")

    def run_validation(self):
        # Prevent multiple validation runs
        if hasattr(self, '_validation_in_progress') and self._validation_in_progress:
            return
        
        self._validation_in_progress = True
        
        try:
            operator = self.operator_cb.get()
            
            if operator not in ["JIO", "AIRTEL"]:
                messagebox.showerror("Error", "Please select an operator (JIO or AIRTEL).")
                return
            
            # Helper function to check if a file is open
            def is_file_open(filepath):
                """Check if a file is already open"""
                if not filepath or not os.path.exists(filepath):
                    return False
                
                try:
                    # Try to open the file in write mode
                    with open(filepath, 'a') as f:
                        # If we can open it, it's not locked
                        return False
                except (IOError, PermissionError):
                    # If we get an access error, the file is probably open
                    return True
                except Exception:
                    # For any other error, assume it might be open
                    return True
            
            # Function to search for and check open report files
            def check_for_open_reports(operator_type, profile_type=""):
                """Search for and check if report files are open"""
                # Common report locations to check
                check_dirs = [
                    os.getcwd(),  # Current directory
                    os.path.join(os.path.expanduser("~"), "Desktop"),  # Desktop
                    os.path.join(os.path.expanduser("~"), "Documents"),  # Documents
                    "C:/Reports",  # Common report directory
                    tempfile.gettempdir(),  # Temp directory
                ]
                
                # Add directory from machine log file if available
                try:
                    if operator_type == "JIO":
                        ml_path = self.ml_entry.get().strip()
                    else:  # AIRTEL
                        if hasattr(self, 'airtel_ml_entry') and self.airtel_ml_entry:
                            ml_path = self.airtel_ml_entry.get().strip()
                        else:
                            ml_path = self.ml_entry.get().strip()
                    
                    if ml_path and os.path.exists(ml_path):
                        ml_dir = os.path.dirname(ml_path)
                        if ml_dir and ml_dir not in check_dirs:
                            check_dirs.append(ml_dir)
                except:
                    pass
                
                # Common report file patterns based on operator and profile
                report_patterns = []
                
                if operator_type == "JIO" and profile_type:
                    report_patterns.extend([
                        f"JIO_{profile_type}_Validation_Report*.xlsx",
                        f"JIO_{profile_type}_Report*.xlsx",
                        f"{profile_type}_Validation_Report*.xlsx",
                    ])
                
                report_patterns.extend([
                    f"{operator_type}_Validation_Report*.xlsx",
                    f"{operator_type}_*_Validation_Report.xlsx",
                    f"FirstCard_{operator_type}_Report*.xlsx",
                    "FirstCard_Validation_Report*.xlsx",
                    "Validation_Report*.xlsx",
                    "*Validation_Report*.xlsx",
                    "*Report*.xlsx"
                ])
                
                # Also check for reports with today's date
                today_str = datetime.datetime.now().strftime('%Y%m%d')
                report_patterns.extend([
                    f"*{today_str}*.xlsx",
                    f"*Report*{today_str}*.xlsx"
                ])
                
                open_reports = []
                
                for check_dir in check_dirs:
                    if not os.path.exists(check_dir):
                        continue
                        
                    for pattern in report_patterns:
                        if not pattern:
                            continue
                            
                        try:
                            for report_path in glob.glob(os.path.join(check_dir, pattern)):
                                if os.path.isfile(report_path) and is_file_open(report_path):
                                    # Get file size and modification time for better identification
                                    file_size = os.path.getsize(report_path)
                                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(report_path))
                                    
                                    # Only consider files that are Excel files and recently modified
                                    if report_path.lower().endswith('.xlsx') and file_size > 1024:  # At least 1KB
                                        open_reports.append({
                                            'path': report_path,
                                            'size': file_size,
                                            'modified': mod_time
                                        })
                        except:
                            continue
                
                return open_reports
            
            # Function to verify profile type from PCOM file
            def verify_profile_from_pcom(pcom_path, selected_profile):
                """Check if the selected profile matches the PCOM file content"""
                if not pcom_path or not os.path.exists(pcom_path):
                    return False, "PCOM file not found or inaccessible"
                
                try:
                    # Read the PCOM file content - try different encodings
                    content = ""
                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    
                    for encoding in encodings:
                        try:
                            with open(pcom_path, 'r', encoding=encoding, errors='ignore') as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if not content:
                        return False, "Could not read PCOM file content with any supported encoding"
                    
                    content_upper = content.upper()
                    filename = os.path.basename(pcom_path).upper()
                    
                    # Define profile mappings - what to look for in PCOM file
                    #Input side file validation
                    profile_mappings = {
                        "MOB": ["MOB", "MOBILE", "MOBILITY", "4G", "LTE", "GSM", "CAT1", "CAT 1", "CAT-1"],
                        "WBIOT": ["WBIOT", "WB-IOT", "WB IOT", "WIDE BAND", "WIDEBAND", "CAT-M1", "CAT M1", "CAT-M", "LTE-M", "CATM1", "CAT-M2"],
                        "NBIOT": ["NBIOT", "NB-IOT", "NB IOT", "NARROW BAND", "NARROWBAND", "CAT-NB", "CAT NB", "CAT-N", "NB1", "CAT-NB1", "CAT-NB2"]
                    }
                    
                    # 1. FIRST PRIORITY: Check filename for clear profile indicators
                    filename_profile = None
                    filename_keyword_found = None
                    
                    for profile_type, keywords in profile_mappings.items():
                        for keyword in keywords:
                            keyword_upper = keyword.upper()
                            # Check if keyword appears as a whole word in filename
                            if keyword_upper in filename:
                                # Check if it's a whole word (not part of another word)
                                # Simple check: look for word boundaries or check if it's a common pattern
                                filename_profile = profile_type
                                filename_keyword_found = keyword
                                break
                        if filename_profile:
                            break
                    
                    # 2. SECOND PRIORITY: Check content for profile indicators
                    content_profiles = []
                    content_keywords_found = []
                    
                    for profile_type, keywords in profile_mappings.items():
                        for keyword in keywords:
                            keyword_upper = keyword.upper()
                            if keyword_upper in content_upper:
                                if profile_type not in content_profiles:
                                    content_profiles.append(profile_type)
                                    content_keywords_found.append(keyword)
                                break  # Found at least one keyword for this profile
                    
                    # 3. DECISION LOGIC
                    # If filename clearly indicates a profile, it takes precedence
                    if filename_profile:
                        if filename_profile == selected_profile:
                            # Filename matches selected profile
                            if selected_profile in content_profiles:
                                return True, f"Filename indicates '{selected_profile}' ({filename_keyword_found}) and content confirms with '{content_keywords_found[content_profiles.index(selected_profile)]}'"
                            else:
                                # Filename matches but content doesn't confirm
                                if content_profiles:
                                    return False, f"Filename indicates '{filename_profile}' but content suggests: {', '.join(content_profiles)}. Filename mismatch!"
                                else:
                                    return True, f"Filename clearly indicates '{selected_profile}' profile ({filename_keyword_found})"
                        else:
                            # Filename indicates different profile than selected
                            if content_profiles and selected_profile in content_profiles:
                                # Content supports selected profile but filename contradicts
                                return False, f"Filename indicates '{filename_profile}' ({filename_keyword_found}) but you selected '{selected_profile}'. Filename mismatch!"
                            else:
                                return False, f"Filename indicates '{filename_profile}' ({filename_keyword_found}) but you selected '{selected_profile}'. Major mismatch!"
                    
                    # No clear filename indicator, check content
                    if content_profiles:
                        if selected_profile in content_profiles:
                            if len(content_profiles) == 1:
                                return True, f"Content indicates '{selected_profile}' profile"
                            else:
                                # Multiple profiles found in content
                                return False, f"Multiple profile indicators found in content: {', '.join(content_profiles)}. Please verify PCOM file."
                        else:
                            # Selected profile not in content profiles
                            if len(content_profiles) == 1:
                                return False, f"Profile mismatch! Selected: '{selected_profile}', but PCOM file content indicates: {content_profiles[0]}"
                            else:
                                return False, f"Profile mismatch! Selected: '{selected_profile}', but PCOM file contains indicators for: {', '.join(content_profiles)}"
                    else:
                        # No indicators found anywhere
                        return False, f"No profile indicators found in PCOM filename or content. Please verify file matches '{selected_profile}' profile"
                    
                except Exception as e:
                    return False, f"Error reading PCOM file: {str(e)}"
            
            # Check for open reports BEFORE running validation
            profile = self.profile_cb.get() if operator == "JIO" else ""
            open_reports = check_for_open_reports(operator, profile)
            
            if open_reports:
                # Sort by modification time (newest first)
                open_reports.sort(key=lambda x: x['modified'], reverse=True)
                
                # Prepare error message
                report_list = "\n".join([f"• {report['path']} (Modified: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')})" 
                                    for report in open_reports[:5]])  # Show first 5
                
                if len(open_reports) > 5:
                    report_list += f"\n• ... and {len(open_reports) - 5} more report files"
                
                self.log_output.delete(1.0, tk.END)
                self.log_output.insert(tk.END, f"❌ Found {len(open_reports)} open report file(s):\n")
                self.log_output.insert(tk.END, f"{report_list}\n\n")
                self.log_output.insert(tk.END, "Please close all report files before generating a new report.\n")
                
                # Ask user what to do
                response = messagebox.askretrycancel(
                    "Report Files Open", 
                    f"Found {len(open_reports)} open report file(s).\n\n"
                    f"To generate a new report, please:\n"
                    f"1. Close all open Excel files\n"
                    f"2. Click 'Retry' to continue\n\n"
                    f"Or click 'Cancel' to stop."
                )
                
                if response:
                    # User clicked Retry, check again
                    open_reports = check_for_open_reports(operator, profile)
                    if open_reports:
                        self.log_output.insert(tk.END, "❌ Reports are still open. Validation cancelled.\n")
                        return
                    else:
                        self.log_output.insert(tk.END, "✅ All reports closed. Continuing with validation...\n")
                else:
                    self.log_output.insert(tk.END, "❌ Validation cancelled by user.\n")
                    return
            
            if operator == "JIO":
                # JIO validation logic
                profile = self.profile_cb.get()
                circle_val = self.circle_entry.get().strip()
                perso_script_path = self.perso_script_entry.get().strip() if hasattr(self, 'perso_script_entry') and self.perso_script_entry else ""
                paths = [self.ml_entry.get(), self.pcom_entry.get(), self.cnum_entry.get(), self.scm_entry.get(), self.sim_oda_entry.get()]
                image_paths = [self.image1_entry.get(), self.image2_entry.get(), self.image3_entry.get(), self.image4_entry.get()]
                if self.image5_entry.get():
                    image_paths.append(self.image5_entry.get())

                if profile not in ["MOB", "WBIOT", "NBIOT"]:
                    messagebox.showerror("Error", "Please select a valid profile type.")
                    self._validation_in_progress = False
                    return

                # Check if all required files are selected and exist
                missing_files = []
                for i, (path, file_type) in enumerate([
                    (paths[0], "Machine Log"),
                    (paths[1], "PCOM"),
                    (paths[2], "CNUM"),
                    (paths[3], "SCM"),
                    (paths[4], "SIM ODA")
                ]):
                    if not path or not os.path.exists(path):
                        missing_files.append(file_type)

                if missing_files:
                    error_message = "Please select the following required files for JIO validation:\n"
                    for file in missing_files:
                        error_message += f"• {file}\n"
                    messagebox.showerror("File Selection Error", error_message)
                    self._validation_in_progress = False
                    return
                
                # Verify profile matches PCOM file content
                if paths[1]:
                    self.log_output.delete(1.0, tk.END)
                    self.log_output.insert(tk.END, f"🔍 Verifying profile type from PCOM file...\n")
                    self.log_output.update()
                    
                    profile_match, profile_message = verify_profile_from_pcom(paths[1], profile)
                    
                    if not profile_match:
                        self.log_output.insert(tk.END, f"❌ PROFILE VERIFICATION FAILED!\n")
                        self.log_output.insert(tk.END, "=" * 50 + "\n")
                        self.log_output.insert(tk.END, f"Error Details    : {profile_message}\n")
                        self.log_output.insert(tk.END, "=" * 50 + "\n\n")
                        messagebox.showerror("Profile Mismatch Detected", f"PROFILE VERIFICATION FAILED!\n\n{profile_message}")
                        self._validation_in_progress = False
                        return
                    else:
                        self.log_output.insert(tk.END, f"✅ Profile verified successfully.\n\n")

                # --- START THREADED VALIDATION ---
                self.run_button.config(text="⌛ Please Wait...", state="disabled")
                self.progress_bar.pack(side="left", padx=10, fill="x", expand=True)  # Show progress bar
                self.progress_bar.start(10)  # Start indeterminate animation (10ms interval)
                self.log_output.insert(tk.END, "\n" + "="*50 + "\n")
                self.log_output.insert(tk.END, "🚀 INITIALIZATION COMPLETE. STARTING VALIDATION...\n")
                self.log_output.insert(tk.END, "⏳ PLEASE WAIT: Processing images and SCM data...\n")
                self.log_output.insert(tk.END, "="*50 + "\n\n")
                self.log_output.see(tk.END)
                self.log_output.update()

                def validation_thread_func():
                    try:
                        from first_card_validation.core.validation_engine import main as run_validation_engine
                        
                        # Run validation
                        report_path, validation_errors = run_validation_engine(
                            profile_type=profile,
                            filepath=paths[0],
                            pcom_path=paths[1],
                            cnum_path=paths[2],
                            scm_path=paths[3],
                            sim_oda_path=paths[4],
                            image_paths=image_paths,
                            circle_value=circle_val,
                            perso_script_path=perso_script_path
                        )

                        # Callback to UI
                        self.parent.after(0, lambda: self.on_validation_complete(report_path, validation_errors))
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        err_msg = str(e)
                        self.parent.after(0, lambda: self.on_validation_error(err_msg))

                threading.Thread(target=validation_thread_func, daemon=True).start()
                return # Exit main thread, UI remains interactive
            
            else:  # AIRTEL
                # AIRTEL validation logic - FIXED: Collect and pass image paths
                if hasattr(self, 'airtel_ml_entry') and self.airtel_ml_entry:
                    ml_path = self.airtel_ml_entry.get().strip()
                    pcom_path = self.airtel_pcom_entry.get().strip()
                    cnum_path = self.airtel_cnum_entry.get().strip() 
                    sim_oda_path = self.airtel_sim_oda_entry.get().strip()
                    
                    # Collect AIRTEL image paths
                    airtel_image_paths = {}
                    
                    # Collect INNER LABEL image
                    if hasattr(self, 'airtel_image1_entry'):
                        inner_path = self.airtel_image1_entry.get().strip()
                        if inner_path and os.path.exists(inner_path):
                            airtel_image_paths['inner_label'] = inner_path
                            print(f"📸 Found INNER LABEL image: {inner_path}")
                        elif inner_path:
                            print(f"⚠️  INNER LABEL image not found: {inner_path}")
                    
                    # Collect OUTER LABEL image
                    if hasattr(self, 'airtel_image2_entry'):
                        outer_path = self.airtel_image2_entry.get().strip()
                        if outer_path and os.path.exists(outer_path):
                            airtel_image_paths['outer_label'] = outer_path
                            print(f"📸 Found OUTER LABEL image: {outer_path}")
                        elif outer_path:
                            print(f"⚠️  OUTER LABEL image not found: {outer_path}")
                    
                    print(f"🔍 USING AIRTEL-SPECIFIC ENTRIES")
                else:
                    # Fallback to JIO entries
                    ml_path = self.ml_entry.get().strip()
                    pcom_path = self.pcom_entry.get().strip()
                    cnum_path = self.cnum_entry.get().strip() 
                    sim_oda_path = self.sim_oda_entry.get().strip()
                    
                    # Fallback for images if Airtel entries don't exist
                    airtel_image_paths = {}
                    # Try JIO image entries for Airtel fallback
                    if self.image1_entry.get().strip() and os.path.exists(self.image1_entry.get().strip()):
                        airtel_image_paths['inner_label'] = self.image1_entry.get().strip()
                    if self.image2_entry.get().strip() and os.path.exists(self.image2_entry.get().strip()):
                        airtel_image_paths['outer_label'] = self.image2_entry.get().strip()
                
                # For AIRTEL, we can also add profile verification if needed
                if pcom_path and os.path.exists(pcom_path):
                    self.log_output.delete(1.0, tk.END)
                    self.log_output.insert(tk.END, f"🔍 Checking AIRTEL PCOM file...\n")
                    self.log_output.update()
                    
                    try:
                        content = ""
                        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                        
                        for encoding in encodings:
                            try:
                                with open(pcom_path, 'r', encoding=encoding, errors='ignore') as f:
                                    content = f.read()
                                break
                            except UnicodeDecodeError:
                                continue
                        
                        if content:
                            content_upper = content.upper()
                            if "AIRTEL" in content_upper or "BHARTI" in content_upper or "VODAFONE" in content_upper or "IDEA" in content_upper:
                                self.log_output.insert(tk.END, f"✅ AIRTEL operator verified in PCOM file.\n\n")
                            else:
                                self.log_output.insert(tk.END, f"⚠️  AIRTEL indicator not found in PCOM file.\n")
                                self.log_output.insert(tk.END, f"   Proceeding with validation anyway...\n\n")
                        else:
                            self.log_output.insert(tk.END, f"⚠️  Could not read PCOM file content.\n")
                            self.log_output.insert(tk.END, f"   Proceeding with validation...\n\n")
                    except Exception as e:
                        self.log_output.insert(tk.END, f"⚠️  Could not read PCOM file: {str(e)}\n")
                        self.log_output.insert(tk.END, f"   Proceeding with validation...\n\n")
                
                # [LIBERAL] No mandatory file checks for Airtel - allow running even if empty
                if not ml_path or not cnum_path or not sim_oda_path:
                    self.log_output.insert(tk.END, "⚠️  Warning: Some Airtel files are missing. Running in liberal mode...\n")

                # --- START THREADED AIRTEL VALIDATION ---
                self.run_button.config(text="⌛ Please Wait...", state="disabled")
                self.progress_bar.pack(side="left", padx=10, fill="x", expand=True)  # Show progress bar
                self.progress_bar.start(10)  # Start indeterminate animation (10ms interval)
                
                self.log_output.insert(tk.END, "\n" + "="*50 + "\n")
                self.log_output.insert(tk.END, "🚀 STARTING AIRTEL VALIDATION...\n")
                self.log_output.insert(tk.END, "⏳ PLEASE WAIT: Processing images and data...\n")
                self.log_output.insert(tk.END, "="*50 + "\n\n")
                self.log_output.see(tk.END)
                self.log_output.update()

                def airtel_thread_func():
                    try:
                        from first_card_validation.core.airtel_validation import main_airtel as run_airtel_validation
                        
                        report_path, validation_errors = run_airtel_validation(
                            filepath=ml_path,
                            pcom_path=pcom_path,
                            cnum_path=cnum_path,
                            sim_oda_path=sim_oda_path,
                            image_paths=airtel_image_paths
                        )

                        # Callback to UI
                        self.parent.after(0, lambda: self.on_validation_complete(report_path, validation_errors))
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        err_msg = str(e)
                        self.parent.after(0, lambda: self.on_validation_error(err_msg))

                threading.Thread(target=airtel_thread_func, daemon=True).start()
                return # Exit main thread, UI remains interactive
        
        finally:
            # Reset flag after validation completes
            if hasattr(self, 'root'):
                self.root.after(1000, lambda: setattr(self, '_validation_in_progress', False))

    def update_operator_fields(self, *args):
        """Show/hide fields based on operator selection"""
        operator = self.operator_cb.get()
        
        # Disable operator dropdown after selection to prevent changing operators
        if operator in ["JIO", "AIRTEL"]:
            self.operator_cb.config(state="disabled")
        
        # Clear log and update message based on operator selection
        self.log_output.delete(1.0, tk.END)
        
        if operator == "JIO":
            # Select correct Back button command
            self.jio_back_button.config(command=self.jio_back_to_first_frame)
            # Select correct Next button command
            self.jio_next_button.config(command=self.jio_show_second_frame)
            
            # Set dynamic title
            self.jio_first_frame.config(text="1st card results logs")
            # Reset JIO frame tracking
            self.jio_first_frame_shown = True
            self.jio_second_frame_shown = False
            
            # Hide second frame if shown, show first frame
            if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
                self.jio_second_frame.pack_forget()
            if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
                self.jio_first_frame.pack(padx=20, pady=10, fill="x")
            
            # Show JIO first frame widgets only (Profile, ML, PCOM, Images)
            for widget in self.jio_first_frame_widgets:
                widget.grid()
            
            # Hide JIO second frame widgets (CNUM, SCM, SIM_ODA)
            for widget in self.jio_second_frame_widgets:
                widget.grid_remove()
            
            # Hide Airtel specific fields
            for widget in self.operator_widgets['airtel']:
                if widget != self.operator_cb:  # Don't hide the operator dropdown itself
                    widget.grid_remove()
            
            # Hide Run and Clear All buttons
            if hasattr(self, 'run_button') and self.run_button:
                self.run_button.pack_forget()
            if hasattr(self, 'clear_all_button') and self.clear_all_button:
                self.clear_all_button.pack_forget()
            
            # Show JIO-specific buttons
            if hasattr(self, 'jio_back_button') and self.jio_back_button:
                self.jio_back_button.pack_forget() # Hidden on first step
            if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
                self.jio_clear_button.pack(side="left", padx=5)
            if hasattr(self, 'jio_next_button') and self.jio_next_button:
                self.jio_next_button.pack(side="left", padx=5)
            
            # Show buttons and logs in correct order
            if hasattr(self, 'button_frame'):
                self.button_frame.pack(pady=10)
            if hasattr(self, 'log_frame'):
                self.log_frame.pack_forget() # Repack to ensure it's at the bottom
                self.log_frame.pack(padx=20, pady=(0, 15), fill="both", expand=True)

            self.log_output.insert(tk.END, "JIO operator selected. Please select profile type and required files.\n")
            
        elif operator == "AIRTEL":
            # Select correct Back button command
            self.jio_back_button.config(command=self.airtel_back_to_first_frame)
            # Select correct Next button command
            self.jio_next_button.config(command=self.airtel_show_second_frame)
            
            # Set dynamic title
            self.jio_first_frame.config(text="1st card results logs")
            # Reset JIO frame tracking
            self.jio_first_frame_shown = False
            self.jio_second_frame_shown = False
            
            # Hide JIO frames
            if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
                self.jio_second_frame.pack_forget()
            if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
                self.jio_first_frame.pack(padx=20, pady=10, fill="x")
            
            # Hide JIO first frame widgets
            for widget in self.jio_first_frame_widgets:
                widget.grid_remove()
            # Hide JIO second frame widgets
            for widget in self.jio_second_frame_widgets:
                widget.grid_remove()
            
            # Hide JIO-specific buttons, Run and Clear All buttons
            if hasattr(self, 'jio_back_button') and self.jio_back_button:
                self.jio_back_button.pack_forget()
            if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
                self.jio_clear_button.pack_forget()
            if hasattr(self, 'jio_next_button') and self.jio_next_button:
                self.jio_next_button.pack_forget()
            
            # Hide Run and Clear All buttons
            if hasattr(self, 'run_button') and self.run_button:
                self.run_button.pack_forget()
            if hasattr(self, 'clear_all_button') and self.clear_all_button:
                self.clear_all_button.pack_forget()
            
            # Show buttons and logs in correct order
            if hasattr(self, 'button_frame'):
                self.button_frame.pack(pady=10)
            if hasattr(self, 'log_frame'):
                self.log_frame.pack_forget() # Repack to ensure it's at the bottom
                self.log_frame.pack(padx=20, pady=(0, 15), fill="both", expand=True)
            
            # Show Airtel Step 1 buttons
            if hasattr(self, 'jio_back_button') and self.jio_back_button:
                self.jio_back_button.pack_forget()
            if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
                self.jio_clear_button.pack(side="left", padx=5)
            if hasattr(self, 'jio_next_button') and self.jio_next_button:
                self.jio_next_button.pack(side="left", padx=5)
            
            # Show Airtel Step 1 fields
            for widget in self.airtel_first_frame_widgets:
                widget.grid()
            # Hide Airtel Step 2 fields
            for widget in self.airtel_second_frame_widgets:
                widget.grid_remove()
            
            self.log_output.insert(tk.END, "AIRTEL operator selected. Please select required files.\n")
        else:
            # No operator selected, hide all operator-specific fields
            for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown
                widget.grid_remove()
            for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown
                widget.grid_remove()
            
            # Reset JIO frame tracking
            self.jio_first_frame_shown = False
            self.jio_second_frame_shown = False
            
            # Hide JIO frames
            if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
                self.jio_second_frame.pack_forget()
            if hasattr(self, 'jio_first_frame') and self.jio_first_frame:
                self.jio_first_frame.pack(padx=20, pady=10, fill="x")
            
            # Hide JIO-specific buttons, show default buttons
            if hasattr(self, 'jio_back_button') and self.jio_back_button:
                self.jio_back_button.pack_forget()
            if hasattr(self, 'jio_clear_button') and self.jio_clear_button:
                self.jio_clear_button.pack_forget()
            if hasattr(self, 'jio_next_button') and self.jio_next_button:
                self.jio_next_button.pack_forget()
            
            if hasattr(self, 'run_button') and self.run_button:
                self.run_button.pack_forget()
            if hasattr(self, 'clear_all_button') and self.clear_all_button:
                self.clear_all_button.pack_forget()
            
            # Hide buttons and logs
            if hasattr(self, 'button_frame'):
                self.button_frame.pack_forget()
            if hasattr(self, 'log_frame'):
                self.log_frame.pack(padx=20, pady=(0, 15), fill="both", expand=True)

            self.log_output.insert(tk.END, "Please select an operator to continue...\n")

    def get_icon_path(self):
        """Get the absolute path to the application icon"""
        # Try using resource_path for exe compatibility
        try:
            from runtime_hook import resource_path
            icon_path = resource_path(r"assets/icons/RTL_logo.ico")
            if os.path.exists(icon_path):
                print(f"First Card - Icon found via resource_path: {icon_path}")
                return icon_path
        except Exception as e:
            print(f"resource_path error: {e}")
        
        # Fallback to direct paths
        icon_paths = [
            r"D:\Jio_Validation_Suite\assets\icons\RTL_logo.ico",
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                print(f"First Card - Icon found: {path}")
                return path
        
        print("First Card - Icon not found in typical locations")
        return None

    def launch_gui(self):
        # Create a new window for the first card validation
        self.root = self.parent
        
        # Set icon with error handling
        icon_path = self.get_icon_path()
        if icon_path and os.path.exists(icon_path):
            try:
                img = PILImage.open(icon_path).resize((32, 32), PILImage.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, icon)
                print("First Card - Icon set successfully")
                
                # Also set logo in header
                logo_img = PILImage.open(icon_path).resize((32, 32), PILImage.LANCZOS)
                logo_icon = ImageTk.PhotoImage(logo_img)
                
                # === Header Frame ===
                header = tk.Frame(self.root, bg="#2c3e50", height=60)
                header.pack(fill="x")

                logo_label = tk.Label(header, image=logo_icon, bg="#2c3e50")
                logo_label.image = logo_icon  # keep a reference!
                logo_label.pack(side="left", padx=15)

                title_label = tk.Label(
                    header,
                    text="First Card Validation Tool",
                    bg="#2c3e50",
                    fg="white",
                    font=("Segoe UI", 16, "bold"),
                )
                title_label.pack(side="left", pady=15)
                
            except Exception as e:
                print(f"First Card - Error setting icon: {e}")
                self.create_header_without_icon()
        else:
            print("First Card - Using default system icon")
            self.create_header_without_icon()

        # Only set title, DO NOT reset geometry - it's already centered from main_window
        self.root.title("First Card Validator Tool Version 1.2")
        self.root.configure(bg="#e9edf0")
        self.root.resizable(False, True)  # Allow vertical resizing for JIO two-step flow

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 10), background="#f8f9fa")
        style.configure("TButton", font=("Segoe UI", 10), padding=4)
        style.configure("TEntry", font=("Segoe UI", 10), padding=4)
        style.configure("TCombobox", font=("Segoe UI", 10))

        # Continue with the rest of the GUI creation...
        self.create_form_elements()

    def create_header_without_icon(self):
        """Create header without icon if icon loading fails"""
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill="x")

        title_label = tk.Label(
            header,
            text="First Card Validation Tool",
            bg="#2c3e50",
            fg="white",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.pack(side="left", padx=15, pady=15)

    def create_form_elements(self):
        """Create the form elements (moved from launch_gui for better organization)"""
        # === Input Container (Top) ===
        self.input_container = tk.Frame(self.root, bg="#f8f9fa")
        self.input_container.pack(side="top", fill="x")

        # === Form Frame ===
        form_frame = tk.LabelFrame(self.input_container, text="", bg="#f8f9fa", font=("Segoe UI", 10))
        form_frame.pack(padx=20, pady=10, fill="x")
        
        # Store reference to first form frame
        self.jio_first_frame = form_frame
        
        # === JIO Second Frame (Initially Hidden) ===
        self.jio_second_frame = tk.LabelFrame(self.input_container, text="Output files", bg="#f8f9fa", font=("Segoe UI", 10))
        # Will be packed later when needed
        
        row = 0
        
        # Operator Selection
        ttk.Label(form_frame, text="Operator:").grid(row=row, column=0, sticky="e", pady=4, padx=8)
        self.operator_cb = ttk.Combobox(form_frame, values=["JIO", "AIRTEL"], width=40, state="readonly")
        self.operator_cb.set("Select operator")
        self.operator_cb.grid(row=row, column=1, pady=4, padx=4, sticky="w") # Removed columnspan
        self.operator_widgets['jio'].append(self.operator_cb)
        self.operator_widgets['airtel'].append(self.operator_cb)
        
        row += 1
        
        # Profile Type (JIO only) AND Circle (Manual Input)
        profile_label = ttk.Label(form_frame, text="Profile Type:")
        profile_label.grid(row=row, column=0, sticky="e", pady=4, padx=8)
        self.profile_cb = ttk.Combobox(form_frame, values=["MOB", "WBIOT", "NBIOT"], width=40, state="readonly")
        self.profile_cb.set("Select profile")
        self.profile_cb.grid(row=row, column=1, pady=4, padx=4, sticky="w") # Removed columnspan
        
        # Circle field parallel to Profile Type in Row 1
        circle_lbl = ttk.Label(form_frame, text="Circle:")
        circle_lbl.grid(row=row, column=2, sticky="e", pady=4, padx=8) # Aligned with Browse column
        self.circle_entry = ttk.Entry(form_frame, width=20)
        self.circle_entry.grid(row=row, column=3, pady=4, padx=4, sticky="w")
        
        self.operator_widgets['jio'].extend([profile_label, self.profile_cb, circle_lbl, self.circle_entry])
        
        # Add Profile and Circle to first frame widgets
        self.jio_first_frame_widgets.extend([profile_label, self.profile_cb, circle_lbl, self.circle_entry])
        
        # Perso Script File field (below Profile Type)
        row += 1
        perso_script_label = ttk.Label(form_frame, text="Perso Script File:")
        perso_script_label.grid(row=row, column=0, sticky="e", pady=4, padx=8)
        self.perso_script_entry = ttk.Entry(form_frame, width=55)
        self.perso_script_entry.grid(row=row, column=1, pady=4, sticky="w")
        perso_script_btn = ttk.Button(form_frame, text="Browse", width=10,
                command=lambda e=self.perso_script_entry: self.browse_perso_script_file(e))
        perso_script_btn.grid(row=row, column=2, padx=6)
        
        self.operator_widgets['jio'].extend([perso_script_label, self.perso_script_entry, perso_script_btn])
        self.jio_first_frame_widgets.extend([perso_script_label, self.perso_script_entry, perso_script_btn])

        # Create separate entry lists for each operator
        jio_entries = []
        airtel_entries = []

        # JIO file inputs - FIRST FRAME (ML, PCOM only)
        jio_first_frame_inputs = [
            ("Machine Log (.txt)", self.browse_ml_file),
            ("PCOM (.L00, .L07)", self.browse_pcom_file)
        ]

        for label, browse_func in jio_first_frame_inputs:
            row += 1
            lbl = ttk.Label(form_frame, text=label + ":")
            lbl.grid(row=row, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(form_frame, width=55)
            ent.grid(row=row, column=1, pady=4, sticky="w")
            btn = ttk.Button(form_frame, text="Browse", width=10,
                    command=lambda e=ent, f=browse_func: f(e))
            btn.grid(row=row, column=2, padx=6)
            jio_entries.append(ent)
            self.operator_widgets['jio'].extend([lbl, ent, btn])
            self.jio_first_frame_widgets.extend([lbl, ent, btn])

        # JIO image labels - FIRST FRAME
        jio_image_labels = [
            "INNER LABEL 100", "INNER LABEL 500",
            "OUTER LABEL 5000", "ARTWORK FRONT", "ARTWORK BACK"
        ]

        image_rows = {}  # <-- store widgets by label
        for img_label in jio_image_labels:
            row += 1
            lbl = ttk.Label(form_frame, text=img_label + ":")
            lbl.grid(row=row, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(form_frame, width=55)
            ent.grid(row=row, column=1, pady=4, sticky="w")
            btn = ttk.Button(form_frame, text="Browse", width=10,
                            command=lambda e=ent: self.browse_image(e))
            btn.grid(row=row, column=2, padx=6)
            jio_entries.append(ent)
            image_rows[img_label] = (lbl, ent, btn)
            self.operator_widgets['jio'].extend([lbl, ent, btn])
            self.jio_first_frame_widgets.extend([lbl, ent, btn])

        # JIO file inputs - SECOND FRAME (CNUM, SCM, SIM_ODA) - in separate frame
        jio_second_frame_inputs = [
            ("CNUM (.txt)", lambda e: self.browse_cnum_file(e, "jio")),
            ("SCM (.txt)", self.browse_scm_file),
            ("SIM ODA (.cps)", self.browse_sim_oda_file)
        ]

        # Create second frame widgets
        second_frame_row = 1
        
        # Operator display in second frame
        # jio_second_frame_label = ttk.Label(self.jio_second_frame, text="Operator: JIO (Step 2 of 2)")
        # jio_second_frame_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=10, padx=8)
        # self.jio_second_frame_widgets.extend([jio_second_frame_label])
        
        for label, browse_func in jio_second_frame_inputs:
            second_frame_row += 1
            lbl = ttk.Label(self.jio_second_frame, text=label + ":")
            lbl.grid(row=second_frame_row, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(self.jio_second_frame, width=55)
            ent.grid(row=second_frame_row, column=1, pady=4, sticky="w")
            btn = ttk.Button(self.jio_second_frame, text="Browse", width=10,
                    command=lambda e=ent, f=browse_func: f(e))
            btn.grid(row=second_frame_row, column=2, padx=6)
            jio_entries.append(ent)
            self.operator_widgets['jio'].extend([lbl, ent, btn])
            # Add to second frame widgets
            self.jio_second_frame_widgets.extend([lbl, ent, btn])

        # AIRTEL file inputs - FIRST FRAME (ML, PCOM ONLY)
        airtel_first_frame_inputs = [
            ("Machine Log (.txt)", self.browse_ml_file),
            ("PCOM (.L00, .L07)", self.browse_pcom_file)
        ]

        row_airtel = 1  # Start from row 1 for Airtel (after operator selection)

        for label, browse_func in airtel_first_frame_inputs:
            lbl = ttk.Label(form_frame, text=label + ":")
            lbl.grid(row=row_airtel, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(form_frame, width=55)
            ent.grid(row=row_airtel, column=1, pady=4, sticky="w")
            btn = ttk.Button(form_frame, text="Browse", width=10,
                    command=lambda e=ent, f=browse_func: f(e))
            btn.grid(row=row_airtel, column=2, padx=6)
            airtel_entries.append(ent)
            self.operator_widgets['airtel'].extend([lbl, ent, btn])
            self.airtel_first_frame_widgets.extend([lbl, ent, btn])
            row_airtel += 1

        # AIRTEL image labels - FIRST FRAME
        airtel_image_labels = ["INNER LABEL", "OUTER LABEL"]
        airtel_image_entries = []

        for img_label in airtel_image_labels:
            lbl = ttk.Label(form_frame, text=img_label + ":")
            lbl.grid(row=row_airtel, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(form_frame, width=55)
            ent.grid(row=row_airtel, column=1, pady=4, sticky="w")
            btn = ttk.Button(form_frame, text="Browse", width=10,
                            command=lambda e=ent: self.browse_image(e))
            btn.grid(row=row_airtel, column=2, padx=6)
            airtel_entries.append(ent)
            airtel_image_entries.append(ent)
            self.operator_widgets['airtel'].extend([lbl, ent, btn])
            self.airtel_first_frame_widgets.extend([lbl, ent, btn])
            row_airtel += 1

        # AIRTEL file inputs - SECOND FRAME (CNUM, SIM ODA)
        airtel_second_frame_inputs = [
            ("CNUM (.out)", lambda e: self.browse_cnum_file(e, "airtel")),
            ("SIM ODA (.cps)", self.browse_sim_oda_file)
        ]

        # Use second frame for these
        airtel_second_frame_row = second_frame_row # Continue from JIO's second frame rows if needed, or restart
        # Note: self.jio_second_frame is shared now as "Output files"
        
        for label, browse_func in airtel_second_frame_inputs:
            airtel_second_frame_row += 1
            lbl = ttk.Label(self.jio_second_frame, text=label + ":")
            lbl.grid(row=airtel_second_frame_row, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(self.jio_second_frame, width=55)
            ent.grid(row=airtel_second_frame_row, column=1, pady=4, sticky="w")
            btn = ttk.Button(self.jio_second_frame, text="Browse", width=10,
                    command=lambda e=ent, f=browse_func: f(e))
            btn.grid(row=airtel_second_frame_row, column=2, padx=6)
            airtel_entries.append(ent)
            self.operator_widgets['airtel'].extend([lbl, ent, btn])
            self.airtel_second_frame_widgets.extend([lbl, ent, btn])

        # FIXED ENTRY ASSIGNMENTS
        # JIO entries
        if len(jio_entries) >= 10:
            # Creation order: 
            # 0: Machine Log, 1: PCOM
            # 2-6: Images (100, 500, 5000, Front, Back)
            # 7: CNUM, 8: SCM, 9: SIM ODA
            self.ml_entry = jio_entries[0]
            self.pcom_entry = jio_entries[1]
            self.image1_entry = jio_entries[2]
            self.image2_entry = jio_entries[3]
            self.image3_entry = jio_entries[4]
            self.image4_entry = jio_entries[5]
            self.image5_entry = jio_entries[6]
            self.cnum_entry = jio_entries[7]
            self.scm_entry = jio_entries[8]
            self.sim_oda_entry = jio_entries[9]
            print("[PASS] JIO entries assigned successfully")

        # AIRTEL entries - SPECIFIC ENTRIES FOR AIRTEL
        if len(airtel_entries) >= 6:
            # Creation order:
            # 0: Machine Log, 1: PCOM
            # 2: INNER LABEL, 3: OUTER LABEL
            # 4: CNUM, 5: SIM ODA
            self.airtel_ml_entry = airtel_entries[0]
            self.airtel_pcom_entry = airtel_entries[1]
            self.airtel_image1_entry = airtel_entries[2]
            self.airtel_image2_entry = airtel_entries[3]
            self.airtel_cnum_entry = airtel_entries[4]
            self.airtel_sim_oda_entry = airtel_entries[5]
            
            print("[PASS] Airtel entries assigned successfully")
        else:
            print(f"[FAIL] Not enough Airtel entries: {len(airtel_entries)}")

        # === Update fields based on operator and profile selection ===
        def update_image_fields(*args):
            """Update image fields based on profile selection (JIO only)"""
            if self.operator_cb.get() == "JIO":
                selected = self.profile_cb.get()
                if selected == "MOB":
                    for widget in image_rows.get("INNER LABEL 100", []):
                        widget.grid_remove()
                else:
                    for widget in image_rows.get("INNER LABEL 100", []):
                        widget.grid()

        self.profile_cb.bind("<<ComboboxSelected>>", update_image_fields)
        self.operator_cb.bind("<<ComboboxSelected>>", self.update_operator_fields)

        # Initially hide all fields until operator is selected
        for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown itself
            widget.grid_remove()
        for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown itself
            widget.grid_remove()
        
        # Also hide JIO second frame widgets initially
        for widget in self.jio_second_frame_widgets:
            widget.grid_remove()
        
        # Hide JIO second frame initially
        if hasattr(self, 'jio_second_frame') and self.jio_second_frame:
            self.jio_second_frame.pack_forget()

        # === Button Frame for Run and Clear buttons ===
        self.button_frame = tk.Frame(self.root, bg="#e9edf0")
        # Initially hidden (will be packed in update_operator_fields)
        self.button_frame.pack_forget() 

        # === JIO-specific Back Button ===
        self.jio_back_button = ttk.Button(self.button_frame, text="← Back", command=self.jio_back_to_first_frame, width=15)
        self.jio_back_button.pack_forget() # Initially hidden

        # === JIO-specific Clear Button (for current frame) ===
        self.jio_clear_button = ttk.Button(self.button_frame, text="Clean", command=self.jio_clear_current_frame, width=15)
        self.jio_clear_button.pack_forget() # Initially hidden
        
        # === Run Button ===
        self.run_button = ttk.Button(self.button_frame, text="▶ Run Validation", command=self.run_validation, width=20)
        self.run_button.pack(side="left", padx=5)

        # === Clear All Button (for Airtel) ===
        self.clear_all_button = ttk.Button(self.button_frame, text="🗑️ Clean All", command=self.clear_all_fields, width=20)
        self.clear_all_button.pack(side="left", padx=5)
        
        # === JIO-specific Next Button (to show second frame) ===
        self.jio_next_button = ttk.Button(self.button_frame, text="Next →", command=self.jio_show_second_frame, width=15)
        self.jio_next_button.pack_forget() # Initially hidden
        
        # === Progress Bar ===
        self.progress_bar = ttk.Progressbar(self.button_frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress_bar.pack(side="left", padx=10, fill="x", expand=True)
        self.progress_bar.pack_forget()  # Initially hidden
        
        # === Log Output Frame ===
        self.log_frame = tk.LabelFrame(self.root, text="Validation Log", bg="#f8f9fa", font=("Segoe UI", 10))
        # Show initially
        self.log_frame.pack(padx=20, pady=(0, 15), fill="both", expand=True)

        self.log_output = scrolledtext.ScrolledText(
            self.log_frame,
            font=("Consolas", 10),
            wrap="word",
            height=10
        )
        self.log_output.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message in log
        self.log_output.insert(tk.END, "Please select an operator to continue...\n")

    def on_validation_complete(self, report_path, validation_errors):
        """Callback when validation thread finishes successfully"""
        self._validation_in_progress = False
        self.run_button.config(text="▶ Run Validation", state="normal")
        
        # Stop and hide progress bar
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        if not report_path:
            self.log_output.insert(tk.END, "[FAIL] Validation failed to generate report!\n")
            if validation_errors:
                self.log_output.insert(tk.END, "Errors returned:\n")
                for error in validation_errors:
                    self.log_output.insert(tk.END, f"• {error}\n")
            messagebox.showerror("Report Generation Failed", "Cannot save the report. Check if the Excel file is open or if there are permission issues.")
            return

        # Check if the report file exists and is accessible
        if report_path and os.path.exists(report_path):
            operator = self.operator_cb.get()
            self.log_output.insert(tk.END, "=" * 50 + "\n")
            self.log_output.insert(tk.END, f"[PASS] {operator} Validation completed successfully.\n")
            self.log_output.insert(tk.END, f"📄 Report saved at: {report_path}\n")
            self.log_output.insert(tk.END, "=" * 50 + "\n\n")
            
            # Show data field validation errors in GUI
            if validation_errors:
                self.log_output.insert(tk.END, "❌ DATA FIELD VALIDATION ERRORS:\n")
                self.log_output.insert(tk.END, "-" * 50 + "\n")
                for error in validation_errors:
                    self.log_output.insert(tk.END, f"• {error}\n")
                self.log_output.insert(tk.END, "-" * 50 + "\n")
                self.log_output.insert(tk.END, f"Total errors found: {len(validation_errors)}\n\n")
                messagebox.showwarning("Validation Completed with Errors", 
                                    f"Validation completed with {len(validation_errors)} data field error(s).\nCheck the log for details.")
            else:
                self.log_output.insert(tk.END, "[PASS] All data fields validated successfully!\n")
                self.log_output.insert(tk.END, "No data field validation errors found.\n\n")
                messagebox.showinfo("Success", "All data fields validated successfully!")
        else:
            self.log_output.insert(tk.END, f"[FAIL] Report file not found at: {report_path}\n")
            messagebox.showerror("Report Not Found", "Report file was not created. Check permissions and disk space.")

        self.log_output.see(tk.END)

    def on_validation_error(self, error_msg):
        """Callback when validation thread encounters an unhandled exception"""
        self._validation_in_progress = False
        self.run_button.config(text="▶ Run Validation", state="normal")
        
        # Stop and hide progress bar
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        full_error = "\n" + "=" * 50 + "\n"
        full_error += f"[FAIL] CRITICAL ERROR DURING VALIDATION:\n{error_msg}\n"
        full_error += "=" * 50 + "\n"
        
        self.log_output.insert(tk.END, full_error)
        messagebox.showerror("Validation Error", f"An error occurred during validation:\n\n{error_msg}")
        self.log_output.see(tk.END)
