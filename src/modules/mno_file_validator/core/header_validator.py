"""
MNO File Validator - Header validation logic
"""
import os
import sys
from typing import List, Tuple
from pathlib import Path

# Add the modules path to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
modules_path = os.path.join(project_root, 'modules')

if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from .validation_base import BaseValidator, ValidationResult


def _make_long_path(path) -> str:
    """Convert path to extended-length path on Windows for long paths (>240 chars)"""
    if sys.platform != 'win32':
        return str(path)
    
    path_str = str(path)
    if path_str.startswith('\\\\?\\'):
        return path_str
    
    abs_path = os.path.abspath(path_str)
    if len(abs_path) > 240:
        if len(abs_path) >= 2 and abs_path[1] == ':':
            return '\\\\?\\' + abs_path
        elif abs_path.startswith('\\\\'):
            return '\\\\?\\UNC\\' + abs_path[2:]
    return path_str


def _safe_open(path, mode='r', encoding='utf-8', errors='replace'):
    """Open file with long path support on Windows"""
    long_path = _make_long_path(path)
    return open(long_path, mode, encoding=encoding, errors=errors)


class HeaderValidator(BaseValidator):
    """Handles header validation between IN and CNUM files"""
    
    def validate_headers(self, in_file: Path, cnum_file: Path) -> ValidationResult:
        """Validate first 15 lines match exactly between IN and CNUM files"""
        try:
            with _safe_open(in_file, 'r', 'utf-8') as f_in:
                in_lines = [
                    line.rstrip('\n\r') 
                    for line in f_in.readlines()[:15]
                ]
            
            with _safe_open(cnum_file, 'r', 'utf-8') as f_cnum:
                cnum_lines = [
                    line.rstrip('\n\r') 
                    for line in f_cnum.readlines()[:15]
                ]
            
            mismatches = []
            for i in range(min(len(in_lines), len(cnum_lines))):
                if in_lines[i] != cnum_lines[i]:
                    mismatches.append(
                        f"ERR: Header Data Mismatch "
                        f"(Expected: '{in_lines[i]}') "
                        f"(Found: '{cnum_lines[i]}') "
                        f"[Line: {i+1}]"
                    )
            
            if mismatches:
                error_msg = f"Header validation failed - {len(mismatches)} mismatches found"
                return ValidationResult(False, error_msg, mismatches)
            
            return ValidationResult(True, "All header lines match exactly", [])
            
        except Exception as e:
            return ValidationResult(False, f"Error during header validation: {str(e)}", [])