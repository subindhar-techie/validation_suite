# first_card_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image as PILImage, ImageTk
import threading
import sys
import os
import tempfile  # <-- ADD THIS LINE
import glob      # <-- ADD THIS LINE
import datetime  # <-- ADD THIS LINE


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
    else:
        print(f"First Card - Modules directory not found: {modules_path}")

print(f"Final modules path: {modules_path}")

# Debug: List all files in modules directory
print("First Card - Contents of modules directory:")
if os.path.exists(modules_path):
    for root, dirs, files in os.walk(modules_path):
        level = root.replace(modules_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{subindent}{file}')
else:
    print(f"First Card - Modules directory does not exist: {modules_path}")

# Add modules path to ensure imports work
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)
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
            # Reset operator selection
            self.operator_cb.set("Select operator")
            
            # Reset profile selection
            self.profile_cb.set("Select profile")
            
            # Clear all JIO entry fields
            self.ml_entry.delete(0, tk.END)
            self.pcom_entry.delete(0, tk.END)
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
            
            # Clear log output
            self.log_output.delete(1.0, tk.END)
            self.log_output.insert(tk.END, "All fields cleared. Please select an operator to continue...\n")
            
            # Hide all operator-specific fields
            for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown itself
                widget.grid_remove()
            for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown itself
                widget.grid_remove()
            
            # Hide back button
            self.back_button.pack_forget()
            
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
        
        # Hide all operator-specific fields
        for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown itself
            widget.grid_remove()
        for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown itself
            widget.grid_remove()
        
        # Hide back button
        self.back_button.pack_forget()
        
        # Clear any validation logs
        self.log_output.delete(1.0, tk.END)
        self.log_output.insert(tk.END, "Please select an operator to continue...\n")

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
                            circle_value=circle_val
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
                
                # Check if files actually exist and are selected
                missing_files = []
                if not ml_path or not os.path.exists(ml_path):
                    missing_files.append("Machine Log")
                if not cnum_path or not os.path.exists(cnum_path):
                    missing_files.append("CNUM")
                if not sim_oda_path or not os.path.exists(sim_oda_path):
                    missing_files.append("SIM ODA")
                    
                if missing_files:
                    error_message = "Please select the following required files for Airtel validation:\n"
                    for file in missing_files:
                        error_message += f"• {file}\n"
                    messagebox.showerror("File Selection Error", error_message)
                    self._validation_in_progress = False
                    return

                try:
                    from first_card_validation.core.airtel_validation import main_airtel as run_airtel_validation
                    
                    self.log_output.insert(tk.END, "Starting AIRTEL validation...\n")
                    self.log_output.insert(tk.END, f"📸 Images to process: {len(airtel_image_paths)}\n")
                    self.log_output.update()
                    
                    report_path, validation_errors = run_airtel_validation(
                        filepath=ml_path,
                        pcom_path=pcom_path,
                        cnum_path=cnum_path,
                        sim_oda_path=sim_oda_path,
                        image_paths=airtel_image_paths
                    )

                    if not report_path:
                        self.log_output.insert(tk.END, "❌ AIRTEL validation failed to generate report!\n")
                        if validation_errors:
                            self.log_output.insert(tk.END, "Errors returned:\n")
                            for error in validation_errors:
                                self.log_output.insert(tk.END, f"• {error}\n")
                        messagebox.showerror("AIRTEL Report Generation Failed", "Failed to generate AIRTEL report. Check the log for details.")
                        return
                    
                    if report_path and os.path.exists(report_path):
                        self.log_output.insert(tk.END, f"✅ AIRTEL Validation completed successfully.\n")
                        self.log_output.insert(tk.END, f"📄 Report saved at: {report_path}\n\n")
                        
                        if validation_errors:
                            self.log_output.insert(tk.END, "❌ DATA FIELD VALIDATION ERRORS:\n")
                            self.log_output.insert(tk.END, "=" * 50 + "\n")
                            for error in validation_errors:
                                self.log_output.insert(tk.END, f"• {error}\n")
                            self.log_output.insert(tk.END, "=" * 50 + "\n")
                            messagebox.showwarning("Validation Completed with Errors", f"AIRTEL validation completed with errors.")
                        else:
                            self.log_output.insert(tk.END, "✅ All Airtel data fields validated successfully!\n")
                            messagebox.showinfo("Success", "AIRTEL validation completed successfully!")
                    
                    self.log_output.see(tk.END)

                except Exception as e:
                    self.log_output.insert(tk.END, f"❌ AIRTEL Validation Error: {str(e)}\n")
                    messagebox.showerror("AIRTEL Exception", str(e))
        
        finally:
            # Reset flag after validation completes
            if hasattr(self, 'root'):
                self.root.after(1000, lambda: setattr(self, '_validation_in_progress', False))

    def update_operator_fields(self, *args):
        """Show/hide fields based on operator selection"""
        operator = self.operator_cb.get()
        
        # Clear log and update message based on operator selection
        self.log_output.delete(1.0, tk.END)
        
        if operator == "JIO":
            # Show all JIO fields (including profile dropdown)
            for widget in self.operator_widgets['jio']:
                if widget != self.operator_cb:  # Don't hide the operator dropdown itself
                    widget.grid()
            # Hide Airtel specific fields
            for widget in self.operator_widgets['airtel']:
                if widget != self.operator_cb:  # Don't hide the operator dropdown itself
                    widget.grid_remove()
            # Show back button
            self.back_button.pack(pady=5)
            self.log_output.insert(tk.END, "JIO operator selected. Please select profile type and required files.\n")
            
        elif operator == "AIRTEL":
            # Hide JIO specific fields
            for widget in self.operator_widgets['jio']:
                if widget != self.operator_cb:  # Don't hide the operator dropdown itself
                    widget.grid_remove()
            # Show Airtel fields
            for widget in self.operator_widgets['airtel']:
                if widget != self.operator_cb:  # Don't hide the operator dropdown itself
                    widget.grid()
            # Show back button
            self.back_button.pack(pady=5)
            self.log_output.insert(tk.END, "AIRTEL operator selected. Please select required files.\n")
        else:
            # No operator selected, hide back button and all operator-specific fields
            for widget in self.operator_widgets['jio'][1:]:  # Skip operator dropdown
                widget.grid_remove()
            for widget in self.operator_widgets['airtel'][1:]:  # Skip operator dropdown
                widget.grid_remove()
            self.back_button.pack_forget()
            self.log_output.insert(tk.END, "Please select an operator to continue...\n")

    def get_icon_path(self):
        """Get the absolute path to the application icon"""
        icon_paths = [
            r"D:\Jio_Validation_Suite\assets\icons\RTL_logo.ico",
            resource_path('assets/icons/Reliance_Jio_Logo.ico'),
            resource_path('assets/icons/RTL_logo.ico')
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

        self.root.title("Validator Tool Version 1.1")
        self.root.geometry("820x750")  # Increased height to accommodate back button
        self.root.configure(bg="#e9edf0")
        self.root.resizable(False, False)

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
        # === Form Frame ===
        form_frame = tk.LabelFrame(self.root, text="Input File Selection", bg="#f8f9fa", font=("Segoe UI", 10))
        form_frame.pack(padx=20, pady=10, fill="x")

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

        # Create separate entry lists for each operator
        jio_entries = []
        airtel_entries = []

        # JIO file inputs
        jio_file_inputs = [
            ("Machine Log (.txt)", self.browse_ml_file),
            ("PCOM (.L00, .L07)", self.browse_pcom_file),
            ("CNUM (.txt)", lambda e: self.browse_cnum_file(e, "jio")),
            ("SCM (.txt)", self.browse_scm_file),
            ("SIM ODA (.cps)", self.browse_sim_oda_file)
        ]

        for label, browse_func in jio_file_inputs:
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

        # JIO image labels
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

        # AIRTEL file inputs (with proper file types) - INCLUDING PCOM
        airtel_file_inputs = [
            ("Machine Log (.txt)", self.browse_ml_file),
            ("PCOM (.L00, .L07)", self.browse_pcom_file),  # PCOM added for Airtel
            ("CNUM (.out)", lambda e: self.browse_cnum_file(e, "airtel")),
            ("SIM ODA (.cps)", self.browse_sim_oda_file)
        ]

        row_airtel = 1  # Start from row 1 for Airtel (after operator selection)

        for label, browse_func in airtel_file_inputs:
            lbl = ttk.Label(form_frame, text=label + ":")
            lbl.grid(row=row_airtel, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(form_frame, width=55)
            ent.grid(row=row_airtel, column=1, pady=4, sticky="w")
            btn = ttk.Button(form_frame, text="Browse", width=10,
                    command=lambda e=ent, f=browse_func: f(e))
            btn.grid(row=row_airtel, column=2, padx=6)
            airtel_entries.append(ent)
            self.operator_widgets['airtel'].extend([lbl, ent, btn])
            row_airtel += 1

        # AIRTEL image labels (only INNER and OUTER labels)
        airtel_image_labels = ["INNER LABEL", "OUTER LABEL"]
        airtel_image_entries = []  # NEW: Store AIRTEL image entries separately

        for img_label in airtel_image_labels:
            lbl = ttk.Label(form_frame, text=img_label + ":")
            lbl.grid(row=row_airtel, column=0, sticky="e", pady=4, padx=8)
            ent = ttk.Entry(form_frame, width=55)
            ent.grid(row=row_airtel, column=1, pady=4, sticky="w")
            btn = ttk.Button(form_frame, text="Browse", width=10,
                            command=lambda e=ent: self.browse_image(e))
            btn.grid(row=row_airtel, column=2, padx=6)
            airtel_entries.append(ent)
            airtel_image_entries.append(ent)  # NEW: Store in separate list
            self.operator_widgets['airtel'].extend([lbl, ent, btn])
            row_airtel += 1

        # FIXED ENTRY ASSIGNMENTS
        # JIO entries
        if len(jio_entries) >= 10:
            self.ml_entry, self.pcom_entry, self.cnum_entry, self.scm_entry, self.sim_oda_entry, \
            self.image1_entry, self.image2_entry, self.image3_entry, self.image4_entry, self.image5_entry = jio_entries[:10]
            # Circle entry (self.circle_entry) is assigned explicitly in Row 1 logic
            print("[PASS] JIO entries assigned successfully")

        # AIRTEL entries - SPECIFIC ENTRIES FOR AIRTEL
        if len(airtel_entries) >= 6:  # Changed from 4 to 6 (4 files + 2 images)
            self.airtel_ml_entry = airtel_entries[0]  # Machine Log
            self.airtel_pcom_entry = airtel_entries[1]  # PCOM
            self.airtel_cnum_entry = airtel_entries[2]  # CNUM
            self.airtel_sim_oda_entry = airtel_entries[3]  # SIM ODA
            
            # NEW: Assign AIRTEL image entries
            if len(airtel_image_entries) >= 2:
                self.airtel_image1_entry = airtel_image_entries[0]  # INNER LABEL
                self.airtel_image2_entry = airtel_image_entries[1]  # OUTER LABEL
                print("[PASS] Airtel image entries assigned successfully")
            
            print("[PASS] Airtel-specific entries assigned successfully")
            print(f"   ML: {self.airtel_ml_entry}")
            print(f"   PCOM: {self.airtel_pcom_entry}")
            print(f"   CNUM: {self.airtel_cnum_entry}")
            print(f"   SIM ODA: {self.airtel_sim_oda_entry}")
            if hasattr(self, 'airtel_image1_entry'):
                print(f"   Image 1 (INNER): {self.airtel_image1_entry}")
            if hasattr(self, 'airtel_image2_entry'):
                print(f"   Image 2 (OUTER): {self.airtel_image2_entry}")
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

        # === Back Button ===
        self.back_button = ttk.Button(
            self.root, 
            text="← Back to Operator Selection", 
            command=self.reset_operator_selection, 
            width=30
        )
        # Initially hidden, will be shown when operator is selected

        # === Button Frame for Run and Clear buttons ===
        button_frame = tk.Frame(self.root, bg="#e9edf0")
        button_frame.pack(pady=10)

        # === Run Button ===
        self.run_button = ttk.Button(button_frame, text="▶ Run Validation", command=self.run_validation, width=20)
        self.run_button.pack(side="left", padx=5)

        # === Clear Button ===
        clear_button = ttk.Button(button_frame, text="🗑️ Clear All", command=self.clear_all_fields, width=20)
        clear_button.pack(side="left", padx=5)
        
        # === Log Output Frame ===
        log_frame = tk.LabelFrame(self.root, text="Validation Log", bg="#f8f9fa", font=("Segoe UI", 10))
        log_frame.pack(padx=20, pady=(0, 15), fill="both", expand=True)

        self.log_output = scrolledtext.ScrolledText(
            log_frame,
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
            self.log_output.insert(tk.END, "=" * 50 + "\n")
            self.log_output.insert(tk.END, f"[PASS] JIO Validation completed successfully.\n")
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
        
        full_error = "\n" + "=" * 50 + "\n"
        full_error += f"[FAIL] CRITICAL ERROR DURING VALIDATION:\n{error_msg}\n"
        full_error += "=" * 50 + "\n"
        
        self.log_output.insert(tk.END, full_error)
        messagebox.showerror("Validation Error", f"An error occurred during validation:\n\n{error_msg}")
        self.log_output.see(tk.END)
