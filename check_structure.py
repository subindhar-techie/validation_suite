# check_structure.py
import os

def check_project_structure():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Project root: {current_dir}")
    print("\nProject structure:")
    
    for root, dirs, files in os.walk(current_dir):
        level = root.replace(current_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py') or file in ['__init__.py', 'Reliance_Jio_Logo.ico']:
                print(f"{subindent}{file}")

if __name__ == "__main__":
    check_project_structure()