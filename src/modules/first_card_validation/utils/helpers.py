import os
import sys
import re

import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def normalize_field(field_name):
    return field_name.strip().upper().replace(" ", "").replace(".", "")

def hex_to_ascii(hex_str):
    """Convert hex string to ASCII."""
    try:
        return bytes.fromhex(hex_str).decode('ascii')
    except Exception:
        return ''

def swap_pairs(s):
    """Swap every two characters in the string (for ICCID/IMSI formatting)."""
    return ''.join(s[i+1] + s[i] for i in range(0, len(s)-1, 2)) if s else ''

def normalize_iccid(iccid):
    """Normalize ICCID by removing non-digits and swapping pairs."""
    if not iccid:
        return None
    iccid = re.sub(r'[^0-9A-F]', '', iccid.upper())
    return swap_pairs(iccid)# Return first 20 characters

def normalize_imsi(imsi):
    """Normalize IMSI by removing prefix and swapping pairs."""
    if not imsi:
        return None
    imsi = re.sub(r'[^0-9A-F]', '', imsi.upper())
    swapped = swap_pairs(imsi)
    return swapped[3:] if len(swapped) > 3 else swapped  # Remove first 3 chars (prefix)

def normalize_ascii_imsi(ascii_imsi):
    """Convert hex to ASCII and clean IMSI."""
    if not ascii_imsi:
        return None
    if all(c in '0123456789ABCDEFabcdef' for c in ascii_imsi):
        ascii_imsi = hex_to_ascii(ascii_imsi)
    return ascii_imsi[1:] if ascii_imsi.startswith('3') else ascii_imsi