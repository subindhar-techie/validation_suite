# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys

# Add the current directory to Python path
sys.path.append('.')

a = Analysis(
    ['src/main.py'],
    pathex=['.', 'src'],
    binaries=[
        ('C:/Users/m.subindar/AppData/Local/Programs/Python/Python312/Lib/site-packages/pyzbar/libiconv.dll', '.'),
        ('C:/Users/m.subindar/AppData/Local/Programs/Python/Python312/Lib/site-packages/pyzbar/libzbar-64.dll', '.'),
    ],
    datas=[
        ('src/modules', 'modules'),
        ('assets', 'assets'),
        ('src/gui', 'gui'),
        ('assets/icons', 'assets/icons'),
        ('runtime_hook.py', '.')
    ],
    hiddenimports=[
        'mno_file_validator.core.file_comparator',
        'mno_file_validator.core.validation_base',
        'mno_file_validator.core.header_validator',
        'mno_file_validator.core.data_field_validator',
        'mno_file_validator.core.scm_validator',
        'mno_file_validator.core.simoda_validator',
        'first_card_validation.core.validation_engine',
        'first_card_validation.core.file_parsers',
        'first_card_validation.core.qr_processor',
        'first_card_validation.core.excel_generator',
        'machine_log_validation.core.script_validator',
        'cv2', 'numpy', 'pandas', 'openpyxl', 'PIL', 'PIL.Image',
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'pyzbar', 'pyzbar.pyzbar'
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
    [], # binaries
    [], # zipfiles
    [], # datas
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
