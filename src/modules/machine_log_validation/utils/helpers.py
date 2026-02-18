import os
import sys

def normalize_imsi(imsi: str) -> str:
    """Normalize IMSI by removing spaces and non-digit characters"""
    if not imsi:
        return ""
    return ''.join(filter(str.isdigit, str(imsi)))

def normalize_iccid(iccid: str) -> str:
    """Normalize ICCID by removing spaces"""
    if not iccid:
        return ""
    return iccid.replace(' ', '')

def swap_pairs(data: str) -> str:
    """
    Swap pairs of digits in the data.
    Example: '123456' -> '214365'
    Odd-length strings keep the last character as-is: '12345' -> '21435'
    """
    if not data:
        return ""
    
    swapped = []
    length = len(data)
    for i in range(0, length - 1, 2):
        swapped.append(data[i + 1])
        swapped.append(data[i])
    if length % 2 != 0:
        swapped.append(data[-1])
    return ''.join(swapped)

def hex_to_ascii(hex_string: str) -> str:
    """Convert hex string to ASCII, ignore invalid bytes"""
    if not hex_string:
        return ""
    try:
        bytes_obj = bytes.fromhex(hex_string)
        return bytes_obj.decode('ascii', errors='ignore')
    except ValueError:
        # Raised if hex_string is invalid
        return hex_string

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and PyInstaller.
    relative_path: file relative to the project or executable.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Fallback to current file directory
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
