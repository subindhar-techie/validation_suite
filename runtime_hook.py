# runtime_hook.py
import os
import sys

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Get project root for development
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = current_dir
    
    full_path = os.path.join(base_path, relative_path)
    
    # Normalize the path
    full_path = os.path.normpath(full_path)
    
    return full_path

def find_icon(icon_name="Reliance_Jio_Logo.ico"):
    """
    Find icon file in common locations
    """
    possible_paths = [
        f"assets/icons/{icon_name}",
        f"icons/{icon_name}",
        f"assets/{icon_name}",
        icon_name,
        f"../assets/icons/{icon_name}",
        f"../../assets/icons/{icon_name}"
    ]
    
    for path in possible_paths:
        try:
            full_path = resource_path(path)
            if os.path.exists(full_path):
                return full_path
        except:
            continue
    
    return None

# Make functions available globally
sys.modules[__name__].resource_path = resource_path
sys.modules[__name__].find_icon = find_icon