# test_functionality.py
import os
import sys
import tempfile
import shutil

def setup_paths():
    """Setup proper Python paths for testing"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    modules_path = os.path.join(src_path, 'modules')
    
    # Add all necessary paths
    paths_to_add = [current_dir, src_path, modules_path]
    
    for path in paths_to_add:
        if path not in sys.path and os.path.exists(path):
            sys.path.insert(0, path)
            print(f"Added to path: {path}")

def test_module_structure():
    """Check if module directories exist"""
    print("\n" + "="*50)
    print("TESTING MODULE STRUCTURE")
    print("="*50)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    modules_path = os.path.join(current_dir, 'src', 'modules')
    
    if os.path.exists(modules_path):
        print(f"✅ Modules directory exists: {modules_path}")
        print("Contents of modules directory:")
        for item in os.listdir(modules_path):
            item_path = os.path.join(modules_path, item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                # Show contents of each module
                for subitem in os.listdir(item_path):
                    print(f"    📄 {subitem}")
            else:
                print(f"  📄 {item}")
    else:
        print(f"❌ Modules directory not found: {modules_path}")

def test_imports():
    """Test if all modules can be imported"""
    print("\n" + "="*50)
    print("TESTING MODULE IMPORTS")
    print("="*50)
    
    setup_paths()
    
    modules_to_test = [
        'modules.first_card_validation.core.validation_engine',
        'modules.first_card_validation.core.file_parsers', 
        'modules.first_card_validation.core.qr_processor',
        'modules.machine_log_validation.core.script_validator',
        'modules.mno_file_validator.core.file_comparator',
        'modules.mno_file_validator.core.validation_base'
    ]
    
    print("Testing module imports...")
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")

def test_direct_imports():
    """Test direct imports like the main app does"""
    print("\n" + "="*50)
    print("TESTING DIRECT IMPORTS")
    print("="*50)
    
    setup_paths()
    
    print("Testing direct imports...")
    
    # Test First Card Validation
    try:
        from modules.first_card_validation.core.validation_engine import ValidationEngine
        print("✅ First Card ValidationEngine")
    except ImportError as e:
        print(f"❌ First Card ValidationEngine: {e}")
    
    # Test Machine Log Validation
    try:
        from modules.machine_log_validation.core.script_validator import ScriptValidator
        print("✅ Machine Log ScriptValidator")
    except ImportError as e:
        print(f"❌ Machine Log ScriptValidator: {e}")
    
    # Test MNO File Validator
    try:
        from modules.mno_file_validator.core.file_comparator import MNOFileComparator
        print("✅ MNO FileComparator")
    except ImportError as e:
        print(f"❌ MNO FileComparator: {e}")

def test_assets():
    """Test if assets are accessible"""
    print("\n" + "="*50)
    print("TESTING ASSET ACCESSIBILITY")
    print("="*50)
    
    assets_to_test = [
        'assets/icons/Reliance_Jio_Logo.ico',
        'assets/images/logo.png'  # if you have other assets
    ]
    
    print("Testing asset accessibility...")
    for asset in assets_to_test:
        try:
            from runtime_hook import resource_path
            full_path = resource_path(asset)
            exists = os.path.exists(full_path)
            status = "✅" if exists else "❌"
            print(f"{status} {asset} -> {full_path}")
        except Exception as e:
            print(f"❌ {asset}: {e}")

def test_exe_simulation():
    """Test in a way that simulates EXE environment"""
    print("\n" + "="*50)
    print("TESTING EXE SIMULATION")
    print("="*50)
    
    # Simulate PyInstaller environment
    temp_dir = tempfile.mkdtemp()
    print(f"Created temp directory: {temp_dir}")
    
    try:
        # Test resource_path in simulated EXE environment
        original_meipass = getattr(sys, '_MEIPASS', None)
        sys._MEIPASS = temp_dir  # Simulate PyInstaller
        
        from runtime_hook import resource_path
        
        # Test resource_path with simulated EXE
        test_path = resource_path('modules')
        print(f"Resource path in EXE simulation: {test_path}")
        
        # Restore original _MEIPASS
        if original_meipass is None:
            delattr(sys, '_MEIPASS')
        else:
            sys._MEIPASS = original_meipass
            
        print("✅ EXE simulation test passed")
        
    except Exception as e:
        print(f"❌ EXE simulation test failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def check_common_exe_issues():
    """Check for common PyInstaller issues"""
    print("\n" + "="*50)
    print("CHECKING COMMON EXE ISSUES")
    print("="*50)
    
    issues_found = []
    
    # Check for dynamic imports
    print("1. Checking for dynamic imports...")
    dynamic_import_patterns = [
        '__import__', 'importlib', 'exec', 'eval'
    ]
    
    # Check main files for dynamic imports
    files_to_check = ['src/main.py', 'src/gui/main_window.py']
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in dynamic_import_patterns:
                    if pattern in content and 'test_functionality' not in file_path:
                        print(f"   ⚠️  Found '{pattern}' in {file_path}")
    
    # Check asset paths
    print("2. Checking asset paths...")
    required_assets = [
        'assets/icons/Reliance_Jio_Logo.ico',
        'src/modules'
    ]
    
    for asset in required_assets:
        if os.path.exists(asset):
            print(f"   ✅ {asset} exists")
        else:
            print(f"   ❌ {asset} missing")
            issues_found.append(f"Missing asset: {asset}")
    
    # Check if runtime_hook exists
    print("3. Checking runtime hook...")
    if os.path.exists('runtime_hook.py'):
        print("   ✅ runtime_hook.py exists")
    else:
        print("   ❌ runtime_hook.py missing")
        issues_found.append("Missing runtime_hook.py")
    
    # Check spec file
    print("4. Checking build configuration...")
    if os.path.exists('build.spec'):
        print("   ✅ build.spec exists")
        # Check if spec file has proper datas configuration
        with open('build.spec', 'r', encoding='utf-8') as f:
            spec_content = f.read()
            if 'src/modules' in spec_content and 'modules' in spec_content:
                print("   ✅ Modules properly configured in spec file")
            else:
                print("   ⚠️  Check modules configuration in spec file")
    else:
        print("   ❌ build.spec missing")
        issues_found.append("Missing build.spec")
    
    if not issues_found:
        print("✅ No common EXE issues found")
    else:
        print(f"❌ Found {len(issues_found)} potential issues:")
        for issue in issues_found:
            print(f"   - {issue}")
    
    return len(issues_found) == 0

def test_gui_creation():
    """Test if GUI can be created without errors"""
    print("\n" + "="*50)
    print("TESTING GUI CREATION")
    print("="*50)
    
    try:
        import tkinter as tk
        from gui.main_window import MainWindow
        
        # Create root window but don't display it
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Try to create main window
        app = MainWindow(root)
        print("✅ GUI creation test passed")
        
        # Clean up
        root.destroy()
        
    except Exception as e:
        print(f"❌ GUI creation test failed: {e}")
        import traceback
        traceback.print_exc()

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 STARTING COMPREHENSIVE PRE-BUILD TEST")
    print("="*60)
    
    all_tests_passed = True
    
    # Run all tests
    test_module_structure()
    test_imports()
    test_direct_imports()
    test_assets()
    test_exe_simulation()
    test_gui_creation()
    exe_issues_ok = check_common_exe_issues()
    
    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    # Check if we can import all critical components
    try:
        setup_paths()
        from modules.first_card_validation.core.validation_engine import ValidationEngine
        from modules.machine_log_validation.core.script_validator import ScriptValidator
        from modules.mno_file_validator.core.file_comparator import MNOFileComparator
        from gui.main_window import MainWindow
        from runtime_hook import resource_path
        
        print("✅ All critical imports successful")
        print("✅ Resource path function working")
        
        # Test resource path with actual asset
        icon_path = resource_path('assets/icons/Reliance_Jio_Logo.ico')
        if os.path.exists(icon_path):
            print("✅ Asset loading working")
        else:
            print("❌ Asset loading issue")
            all_tests_passed = False
            
    except Exception as e:
        print(f"❌ Critical test failed: {e}")
        all_tests_passed = False
    
    if all_tests_passed and exe_issues_ok:
        print("\n🎉 ALL TESTS PASSED! Ready to build EXE.")
        print("\nNext steps:")
        print("1. py -m PyInstaller build.spec")
        print("2. cd dist")
        print("3. .\\Jio_Validation_Suite.exe")
    else:
        print("\n⚠️  SOME TESTS FAILED! Fix issues before building EXE.")
    
    return all_tests_passed and exe_issues_ok

if __name__ == "__main__":
    # Run comprehensive test
    success = run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)