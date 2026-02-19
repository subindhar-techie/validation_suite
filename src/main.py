import tkinter as tk
from tkinter import messagebox
import sys
import os

# Store original messagebox functions
_original_showinfo = messagebox.showinfo
_original_showerror = messagebox.showerror
_original_showwarning = messagebox.showwarning

# Simple flag to prevent multiple popups
_popup_active = False

def safe_showinfo(title, message, **kwargs):
    """Prevent multiple popups from appearing"""
    global _popup_active
    
    if _popup_active:
        # If a popup is already showing, just return without doing anything
        return "ok"
    
    _popup_active = True
    try:
        result = _original_showinfo(title, message, **kwargs)
    finally:
        # Use after to reset the flag, ensuring it happens after popup closes
        if tk._default_root:
            tk._default_root.after(500, lambda: set_global_popup_false())
    
    return result

def safe_showerror(title, message, **kwargs):
    """Prevent multiple error popups from appearing"""
    global _popup_active
    
    if _popup_active:
        return "ok"
    
    _popup_active = True
    try:
        result = _original_showerror(title, message, **kwargs)
    finally:
        if tk._default_root:
            tk._default_root.after(500, lambda: set_global_popup_false())
    
    return result

def safe_showwarning(title, message, **kwargs):
    """Prevent multiple warning popups from appearing"""
    global _popup_active
    
    if _popup_active:
        return "ok"
    
    _popup_active = True
    try:
        result = _original_showwarning(title, message, **kwargs)
    finally:
        if tk._default_root:
            tk._default_root.after(500, lambda: set_global_popup_false())
    
    return result

def set_global_popup_false():
    """Helper function to reset the popup flag"""
    global _popup_active
    _popup_active = False

# Monkey patch the messagebox functions
messagebox.showinfo = safe_showinfo
messagebox.showerror = safe_showerror
messagebox.showwarning = safe_showwarning

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add both src and project root to sys.path
src_path = current_dir
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import resource_path function
try:
    from runtime_hook import resource_path, find_icon
except ImportError:
    # Fallback functions
    def resource_path(relative_path):
        base_path = getattr(sys, '_MEIPASS', project_root)
        return os.path.join(base_path, relative_path)
    
    def find_icon(icon_name=r"D:\Jio_Validation_Suite\assets\icons\RTL_logo.ico"):
        possible_paths = [
            f"assets/icons/{icon_name}",
            f"icons/{icon_name}",
            icon_name,
        ]
        for path in possible_paths:
            full_path = resource_path(path)
            if os.path.exists(full_path):
                return full_path
        return None

print(f"Looking for gui module in: {src_path}")

try:
    from gui.main_window import MainWindow
    print("SUCCESS: Imported MainWindow")
except ImportError as e:
    print(f"Import error: {e}")
    try:
        from src.gui.main_window import MainWindow
        print("SUCCESS: Imported using src.gui path")
    except ImportError:
        raise

def set_window_icon(root):
    """Set the application icon with proper path handling"""
    icon_path = find_icon()
    if icon_path and os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
            print(f"SUCCESS: Icon loaded from {icon_path}")
            return True
        except Exception as e:
            print(f"Error setting icon: {e}")
    
    print("WARNING: Using default system icon")
    return False

def main():
    root = tk.Tk()
    
    # Set application icon
    set_window_icon(root)
    
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()