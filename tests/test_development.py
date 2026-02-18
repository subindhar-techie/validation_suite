# test_development.py
import os
import sys

def test_like_main_app():
    """Test imports exactly like main.py does"""
    
    # Simulate main.py path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    project_root = current_dir
    
    # Add paths like main.py does
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"sys.path: {sys.path}")
    
    # Test GUI import (like main.py)
    try:
        from gui.main_window import MainWindow
        print("✅ SUCCESS: Imported MainWindow (like main.py)")
        
        # Test creating the window (without showing it)
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        app = MainWindow(root)
        root.destroy()
        print("✅ SUCCESS: MainWindow created successfully")
        
    except ImportError as e:
        print(f"❌ FAILED: Import MainWindow: {e}")
        
        # Try alternative
        try:
            from src.gui.main_window import MainWindow
            print("✅ SUCCESS: Imported using src.gui path")
        except ImportError as e2:
            print(f"❌ FAILED: Alternative import: {e2}")

def test_runtime_hook():
    """Test runtime hook functionality"""
    print("\nTesting runtime hook...")
    try:
        from runtime_hook import resource_path, find_icon
        
        # Test resource_path
        test_path = resource_path('assets/icons/Reliance_Jio_Logo.ico')
        print(f"✅ resource_path working: {test_path}")
        
        # Test find_icon
        icon_path = find_icon()
        if icon_path:
            print(f"✅ find_icon working: {icon_path}")
        else:
            print("❌ find_icon could not locate icon")
            
    except ImportError as e:
        print(f"❌ Runtime hook import failed: {e}")

if __name__ == "__main__":
    print("🔧 DEVELOPMENT ENVIRONMENT TEST")
    print("="*50)
    test_like_main_app()
    test_runtime_hook()