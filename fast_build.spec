# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
import glob

# Add the current directory to Python path
sys.path.append('.')

# Get Python install path
python_path = os.path.dirname(os.path.dirname(sys.executable))

# Find Python DLL
python_dll = os.path.join(python_path, 'python312.dll')

# Collect all necessary DLLs from Python directory
dll_files = []
for dll in ['python312.dll', 'python3.dll']:
    dll_path = os.path.join(python_path, dll)
    if os.path.exists(dll_path):
        dll_files.append((dll_path, '.'))

# Add DLLs from libffi and other locations
libffi_path = os.path.join(python_path, 'Lib', 'site-packages', 'pyzmq', 'DLLs')
if os.path.exists(libffi_path):
    for dll in glob.glob(os.path.join(libffi_path, '*.dll')):
        dll_files.append((dll, '.'))

# Also check for libffi-7.dll or libffi-8.dll in Python directory
for dll in ['libffi-7.dll', 'libffi-8.dll']:
    dll_path = os.path.join(python_path, dll)
    if os.path.exists(dll_path):
        dll_files.append((dll_path, '.'))

# Check for pythonw (no console) DLL
for dll in ['pythonw312.dll']:                  
    dll_path = os.path.join(python_path, dll)
    if os.path.exists(dll_path):
        dll_files.append((dll_path, '.'))




a = Analysis(
    ['src/main.py'],
    pathex=['.', 'src'],
    binaries=dll_files +
    [
        ('C:/Users/m.subindar/AppData/Local/Programs/Python/Python312/Lib/site-packages/pyzbar/libiconv.dll', '.'),
        ('C:/Users/m.subindar/AppData/Local/Programs/Python/Python312/Lib/site-packages/pyzbar/libzbar-64.dll', '.'),
    ],
    datas=[
        ('src/modules', 'modules'),
        ('assets', 'assets'),
        ('src/gui', 'gui'),
        ('assets/icons', 'assets/icons'),
    ],
    hiddenimports=[
        'mno_file_validator.core.file_comparator',
        'mno_file_validator.core.validation_base',
        'mno_file_validator.core.header_validator',
        'mno_file_validator.core.data_field_validator',
        'mno_file_validator.core.scm_validator',
        'mno_file_validator.core.simoda_validator',
        'mno_file_validator',
        'mno_file_validator.utils.file_utils',
        'mno_file_validator.utils.excel_report_generator',
        'first_card_validation.core.validation_engine',
        'first_card_validation.core.file_parsers',
        'first_card_validation.core.qr_processor',
        'first_card_validation.core.excel_generator',
        'first_card_validation.core.jio_validator',
        'first_card_validation.core.airtel_validation',
        'first_card_validation',
        'machine_log_validation.core.script_validator',
        'machine_log_validation',
        'cv2', 'numpy', 'pandas', 'openpyxl', 'PIL', 'PIL.Image',
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        'pyzbar', 'pyzbar.pyzbar',
        'scipy', 'scipy.special', 'scipy.linalg',
        'sklearn', 'sklearn.utils', 'sklearn.preprocessing',
        'xml', 'xml.etree', 'xml.etree.ElementTree',
        'dateutil', 'dateutil.parser',
        'jinja2', 'jinja2.sandbox',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=True,
    name='Data Validation Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/RTL_logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Data Validation Tool',
)
